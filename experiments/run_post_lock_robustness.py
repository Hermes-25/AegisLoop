from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from aegisloop.config import AegisConfig, load_config
from aegisloop.defender import AegisDefender
from aegisloop.experiment import (
    _balanced_mix,
    _campaign_split,
    _extract_hard_examples,
    _split_legitimate,
)
from aegisloop.fidelity import FidelityGate
from aegisloop.redteam import LinUCBStrategy, RedTeamArena, build_action_space
from aegisloop.simulator import PaymentDigitalTwin

SEEDS = (20260812, 20260813, 20260814, 20260815, 20260816)


def build_v2(config: AegisConfig) -> tuple[AegisDefender, FidelityGate]:
    """Reproduce the submitted V0->V1->V2 training path without writing artifacts."""

    seed = config.seed
    rng = np.random.default_rng(seed)
    twin = PaymentDigitalTwin(config.simulation, seed=seed)
    legitimate = twin.generate_legitimate(config.simulation.legitimate_events)
    legit_train, legit_valid, _ = _split_legitimate(
        legitimate,
        config.training.validation_fraction,
        config.training.test_fraction,
    )
    known = twin.generate_attack_set(config.training.known_attack_families, 42, seed + 1)
    known_train, known_valid, _ = _campaign_split(known, rng)
    train = _balanced_mix(legit_train, known_train, seed)
    valid = _balanced_mix(legit_valid, known_valid, seed + 1)
    defender = AegisDefender(config.training.target_legitimate_fpr, seed).fit(
        train,
        valid,
        calibration_label="legitimate_validation_temporal_60_80pct",
    )
    gate = FidelityGate(legit_train)
    search_families = config.training.known_attack_families + config.training.adaptive_attack_families

    initial_space = build_action_space(
        seed + 11,
        variants_per_family=16,
        families=search_families,
    )
    initial_strategy = LinUCBStrategy(
        initial_space,
        context_dim=6,
        alpha=config.red_team.linucb_alpha,
    )
    _, initial_campaigns = RedTeamArena(
        PaymentDigitalTwin(config.simulation, seed=seed),
        defender,
        gate,
        config.red_team,
        seed + 102,
    ).run(initial_strategy, budget=config.red_team.campaign_budget)
    hard_examples = _extract_hard_examples(
        initial_campaigns,
        config.loop.top_evasions_per_round,
        known_valid,
        "ADV-V0",
    )
    cumulative_attack_train = known_train.copy()

    for transition in range(config.loop.adversarial_rounds):
        cumulative_attack_train = pd.concat(
            [cumulative_attack_train, hard_examples],
            ignore_index=True,
        )
        hardened_train = _balanced_mix(
            legit_train,
            cumulative_attack_train,
            seed + 70 + transition,
        )
        defender = AegisDefender(
            config.training.target_legitimate_fpr,
            seed + transition + 1,
        ).fit(
            hardened_train,
            valid,
            calibration_label="legitimate_validation_temporal_60_80pct",
        )
        if transition + 1 < config.loop.adversarial_rounds:
            search_space = build_action_space(
                seed + 1200 + transition,
                variants_per_family=16,
                families=search_families,
            )
            search_strategy = LinUCBStrategy(
                search_space,
                context_dim=6,
                alpha=config.red_team.linucb_alpha,
                name=f"hardening_search_v{transition + 1}",
            )
            _, search_campaigns = RedTeamArena(
                PaymentDigitalTwin(config.simulation, seed=seed),
                defender,
                gate,
                config.red_team,
                seed + 1300 + transition,
            ).run(search_strategy, budget=config.red_team.campaign_budget)
            hard_examples = _extract_hard_examples(
                search_campaigns,
                config.loop.top_evasions_per_round,
                known_valid,
                f"ADV-V{transition + 1}",
            )

    return defender, gate


def evaluate_pool(
    config: AegisConfig,
    defender: AegisDefender,
    gate: FidelityGate,
    *,
    condition: str,
    replicate: int,
    pool_seed: int,
    arena_seed: int,
    variants_per_family: int,
    budget: int,
) -> pd.DataFrame:
    search_families = config.training.known_attack_families + config.training.adaptive_attack_families
    action_space = build_action_space(
        pool_seed,
        variants_per_family=variants_per_family,
        families=search_families,
    )
    strategy = LinUCBStrategy(
        action_space,
        context_dim=6,
        alpha=config.red_team.linucb_alpha,
        name=f"v2_{condition}_r{replicate}",
    )
    run, _ = RedTeamArena(
        PaymentDigitalTwin(config.simulation, seed=config.seed),
        defender,
        gate,
        config.red_team,
        arena_seed,
    ).run(strategy, budget=budget)
    return run.assign(
        defender_seed=config.seed,
        condition=condition,
        replicate=replicate,
        pool_seed=pool_seed,
        arena_seed=arena_seed,
        variants_per_family=variants_per_family,
        candidate_actions=len(action_space),
        campaign_budget=budget,
    )


def summarise(campaigns: pd.DataFrame) -> pd.DataFrame:
    return (
        campaigns.groupby(["defender_seed", "condition", "replicate"], sort=True)
        .agg(
            campaigns=("iteration", "size"),
            valid_campaigns=("valid", "sum"),
            fully_detected_campaigns=("detection_rate", lambda values: int((values == 1.0).sum())),
            mean_detection_rate=("detection_rate", "mean"),
            total_approved_value=("approved_value", "sum"),
            mean_reward=("reward", "mean"),
            mean_fidelity=("fidelity", "mean"),
            min_fidelity=("fidelity", "min"),
            unique_selected_actions=("action_id", "nunique"),
            selected_families=("family", "nunique"),
            candidate_actions=("candidate_actions", "first"),
            campaign_budget=("campaign_budget", "first"),
            pool_seed=("pool_seed", "first"),
            arena_seed=("arena_seed", "first"),
        )
        .reset_index()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "post_lock_robustness",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    base = load_config(PROJECT_ROOT / "config" / "default.yaml")
    all_frames: list[pd.DataFrame] = []

    for seed in SEEDS:
        config = replace(base, seed=seed)
        print(f"training submitted-path V2 for seed={seed}", flush=True)
        defender, gate = build_v2(config)

        # Three genuinely independent action pools and arena RNG streams per defender seed.
        for replicate in range(3):
            all_frames.append(
                evaluate_pool(
                    config,
                    defender,
                    gate,
                    condition="independent_pool",
                    replicate=replicate,
                    pool_seed=seed + 50_000 + replicate * 1009,
                    arena_seed=seed + 60_000 + replicate * 1013,
                    variants_per_family=20,
                    budget=72,
                )
            )

        # Additional search-pressure stress: 2x candidate density and 2x budget.
        all_frames.append(
            evaluate_pool(
                config,
                defender,
                gate,
                condition="double_search_pressure",
                replicate=0,
                pool_seed=seed + 90_000,
                arena_seed=seed + 100_000,
                variants_per_family=40,
                budget=144,
            )
        )

    campaigns = pd.concat(all_frames, ignore_index=True)
    summary = summarise(campaigns)
    campaigns.to_csv(args.output / "campaign_results.csv", index=False)
    summary.to_csv(args.output / "run_summary.csv", index=False)

    conditions = {}
    for condition, group in summary.groupby("condition", sort=True):
        conditions[condition] = {
            "runs": len(group),
            "defender_seeds": int(group["defender_seed"].nunique()),
            "campaigns": int(group["campaigns"].sum()),
            "valid_campaigns": int(group["valid_campaigns"].sum()),
            "fully_detected_campaigns": int(group["fully_detected_campaigns"].sum()),
            "approved_value": float(group["total_approved_value"].sum()),
            "mean_detection_rate": float(
                np.average(group["mean_detection_rate"], weights=group["campaigns"])
            ),
            "mean_reward": float(np.average(group["mean_reward"], weights=group["campaigns"])),
            "mean_fidelity": float(np.average(group["mean_fidelity"], weights=group["campaigns"])),
            "min_fidelity": float(group["min_fidelity"].min()),
            "runs_with_nonzero_approved_value": int((group["total_approved_value"] > 0).sum()),
            "seeds_with_nonzero_approved_value": int(
                group.loc[group["total_approved_value"] > 0, "defender_seed"].nunique()
            ),
        }
    aggregate = {
        "artifact_version": "1.0",
        "source_revision": "c37586b15d2205c9495881778827d39c3444e7bd",
        "defender_seeds": list(SEEDS),
        "search_families": list(
            base.training.known_attack_families + base.training.adaptive_attack_families
        ),
        "conditions": conditions,
        "interpretation_boundary": (
            "Offline synthetic robustness tests within the configured bounded action "
            "distribution; not evidence of universal protection against open-ended future attackers."
        ),
    }
    with (args.output / "aggregate.json").open("w", encoding="utf-8") as handle:
        json.dump(aggregate, handle, indent=2)
    print(json.dumps(aggregate, indent=2), flush=True)


if __name__ == "__main__":
    main()
