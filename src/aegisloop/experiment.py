from __future__ import annotations

import json
from dataclasses import dataclass, replace
from itertools import pairwise
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_score, roc_auc_score

from aegisloop.attacks import ATTACK_ATLAS, scenario_dsl
from aegisloop.config import AegisConfig
from aegisloop.defender import AegisDefender
from aegisloop.fidelity import FidelityGate
from aegisloop.redteam import (
    LinUCBStrategy,
    RandomStrategy,
    RedTeamArena,
    RuleMutationStrategy,
    build_action_space,
)
from aegisloop.simulator import PaymentDigitalTwin


@dataclass(frozen=True, slots=True)
class BenchmarkArtifacts:
    summary: dict
    attack_runs: pd.DataFrame
    loop_metrics: pd.DataFrame
    family_metrics: pd.DataFrame
    fidelity_metrics: dict
    prevalence_metrics: pd.DataFrame
    hardening_runs: pd.DataFrame
    calibration_audit: dict
    fresh_diagnostics: pd.DataFrame


def _split_legitimate(frame: pd.DataFrame, validation_fraction: float, test_fraction: float):
    ordered = frame.sort_values("timestamp").reset_index(drop=True)
    train_end = int(len(ordered) * (1 - validation_fraction - test_fraction))
    valid_end = int(len(ordered) * (1 - test_fraction))
    return ordered.iloc[:train_end], ordered.iloc[train_end:valid_end], ordered.iloc[valid_end:]


def _campaign_split(frame: pd.DataFrame, rng: np.random.Generator):
    ids = frame["campaign_id"].unique().copy()
    rng.shuffle(ids)
    train_end = int(len(ids) * 0.60)
    valid_end = int(len(ids) * 0.80)
    train_ids, valid_ids, test_ids = ids[:train_end], ids[train_end:valid_end], ids[valid_end:]
    return (
        frame[frame["campaign_id"].isin(train_ids)],
        frame[frame["campaign_id"].isin(valid_ids)],
        frame[frame["campaign_id"].isin(test_ids)],
    )


def _balanced_mix(legitimate: pd.DataFrame, fraud: pd.DataFrame, seed: int) -> pd.DataFrame:
    return pd.concat([legitimate, fraud], ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


def _assert_disjoint(left: pd.DataFrame, right: pd.DataFrame, key: str, label: str) -> None:
    overlap = set(left[key]).intersection(right[key])
    if overlap:
        raise AssertionError(f"Data leakage in {label}: {len(overlap)} overlapping {key} values")


def _strategy_summary(frame: pd.DataFrame) -> dict:
    valid = frame[frame["valid"]]
    reward_terms = [
        "value_term",
        "evasion_term",
        "detection_cost_term",
        "resource_cost_term",
        "novelty_term",
        "validity_term",
        "pre_fidelity_reward",
    ]
    return {
        "mean_reward": float(frame["reward"].mean()),
        "total_approved_value": float(valid["approved_value"].sum()),
        "mean_detection_rate": float(valid["detection_rate"].mean()) if len(valid) else 1.0,
        "validity_rate": float(frame["valid"].mean()),
        "novel_evasions": int(frame["novel_evasion"].sum()),
        "families_explored": int(frame["family"].nunique()),
        "top_quartile_reward": float(frame["reward"].quantile(0.75)),
        "mean_reward_decomposition": {column: float(frame[column].mean()) for column in reward_terms},
        "mean_fidelity_multiplier": float(frame["fidelity"].mean()),
    }


def _family_evaluation(defender: AegisDefender, legitimate: pd.DataFrame, attacks: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for family, fraud in attacks.groupby("attack_family"):
        evaluation = _balanced_mix(legitimate, fraud, 31)
        metrics = defender.evaluate(evaluation).to_dict()
        rows.append({"defender": label, "attack_family": family, **metrics})
    return pd.DataFrame(rows)


def _extract_hard_examples(
    campaigns: list[pd.DataFrame],
    top_k: int,
    empty_like: pd.DataFrame,
    id_prefix: str,
) -> pd.DataFrame:
    if not campaigns:
        return empty_like.iloc[:0].copy()
    bank = pd.concat(campaigns, ignore_index=True)
    bank = bank[bank["red_team_approved_value"] > 0].copy()
    if bank.empty:
        return empty_like.iloc[:0].copy()
    campaign_rewards = bank.groupby("campaign_id")["red_team_reward"].first().nlargest(top_k)
    selected = bank[bank["campaign_id"].isin(campaign_rewards.index)].copy()
    selected["campaign_id"] = id_prefix + "-" + selected["campaign_id"].astype(str)
    selected["event_id"] = id_prefix + "-" + selected["event_id"].astype(str)
    return selected.drop(columns=["red_team_reward", "red_team_strategy", "red_team_approved_value"])


def _prevalence_evaluation(
    defender: AegisDefender,
    legitimate: pd.DataFrame,
    fraud: pd.DataFrame,
    label: str,
    seed: int,
    target_prevalence: float = 0.00015,
    repetitions: int = 400,
) -> list[dict]:
    current = _balanced_mix(legitimate, fraud, seed)
    current_metrics = defender.evaluate(current).to_dict()
    current_prevalence = float(current["is_fraud"].mean())
    rows = [
        {
            "defender": label,
            "scenario": "experiment_prevalence",
            "prevalence": current_prevalence,
            "fraud_rows": len(fraud),
            "legitimate_rows": len(legitimate),
            "repetitions": 1,
            "roc_auc_mean": current_metrics["roc_auc"],
            "roc_auc_ci_low": current_metrics["roc_auc"],
            "roc_auc_ci_high": current_metrics["roc_auc"],
            "pr_auc_mean": current_metrics["pr_auc"],
            "precision_mean": current_metrics["precision"],
            "precision_ci_low": current_metrics["precision"],
            "precision_ci_high": current_metrics["precision"],
            "recall_mean": current_metrics["recall"],
            "fpr_mean": current_metrics["legitimate_fpr"],
        }
    ]

    n_fraud = max(1, round(len(legitimate) * target_prevalence / (1 - target_prevalence)))
    rng = np.random.default_rng(seed + 7000)
    legitimate_scores = defender.score(legitimate)
    legitimate_pred = defender.detected_mask(legitimate).astype(int)
    fraud_scores = defender.score(fraud)
    fraud_pred = defender.detected_mask(fraud).astype(int)
    samples: list[dict[str, float]] = []
    for _ in range(repetitions):
        indices = rng.choice(len(fraud), size=n_fraud, replace=False)
        y_true = np.concatenate([np.zeros(len(legitimate), dtype=int), np.ones(n_fraud, dtype=int)])
        scores = np.concatenate([legitimate_scores, fraud_scores[indices]])
        pred = np.concatenate([legitimate_pred, fraud_pred[indices]])
        samples.append(
            {
                "roc_auc": float(roc_auc_score(y_true, scores)),
                "pr_auc": float(average_precision_score(y_true, scores)),
                "precision": float(precision_score(y_true, pred, zero_division=0)),
                "recall": float(np.mean(fraud_pred[indices])),
                "fpr": float(np.mean(legitimate_pred)),
            }
        )
    sample_frame = pd.DataFrame(samples)
    actual_prevalence = n_fraud / (len(legitimate) + n_fraud)
    rows.append(
        {
            "defender": label,
            "scenario": "deployment_stress_downsampled_0.015pct",
            "prevalence": float(actual_prevalence),
            "fraud_rows": n_fraud,
            "legitimate_rows": len(legitimate),
            "repetitions": repetitions,
            "roc_auc_mean": float(sample_frame["roc_auc"].mean()),
            "roc_auc_ci_low": float(sample_frame["roc_auc"].quantile(0.025)),
            "roc_auc_ci_high": float(sample_frame["roc_auc"].quantile(0.975)),
            "pr_auc_mean": float(sample_frame["pr_auc"].mean()),
            "precision_mean": float(sample_frame["precision"].mean()),
            "precision_ci_low": float(sample_frame["precision"].quantile(0.025)),
            "precision_ci_high": float(sample_frame["precision"].quantile(0.975)),
            "recall_mean": float(sample_frame["recall"].mean()),
            "fpr_mean": float(sample_frame["fpr"].mean()),
        }
    )
    full_y = np.concatenate([np.zeros(len(legitimate), dtype=int), np.ones(len(fraud), dtype=int)])
    full_scores = np.concatenate([legitimate_scores, fraud_scores])
    full_pred = np.concatenate([legitimate_pred, fraud_pred])
    negative_weight = (1 - target_prevalence) / max(len(legitimate), 1)
    positive_weight = target_prevalence / max(len(fraud), 1)
    weights = np.concatenate(
        [np.full(len(legitimate), negative_weight), np.full(len(fraud), positive_weight)]
    )
    weighted_precision = float(precision_score(full_y, full_pred, sample_weight=weights, zero_division=0))
    weighted_pr_auc = float(average_precision_score(full_y, full_scores, sample_weight=weights))
    rows.append(
        {
            "defender": label,
            "scenario": "deployment_exact_prevalence_reweighted_0.015pct",
            "prevalence": target_prevalence,
            "fraud_rows": len(fraud),
            "legitimate_rows": len(legitimate),
            "repetitions": 1,
            "roc_auc_mean": float(roc_auc_score(full_y, full_scores, sample_weight=weights)),
            "roc_auc_ci_low": float("nan"),
            "roc_auc_ci_high": float("nan"),
            "pr_auc_mean": weighted_pr_auc,
            "precision_mean": weighted_precision,
            "precision_ci_low": float("nan"),
            "precision_ci_high": float("nan"),
            "recall_mean": float(np.mean(fraud_pred)),
            "fpr_mean": float(np.mean(legitimate_pred)),
        }
    )
    return rows


def run_benchmark(config: AegisConfig, quick: bool = False) -> BenchmarkArtifacts:
    seed = config.seed
    rng = np.random.default_rng(seed)
    legitimate_events = min(config.simulation.legitimate_events, 9000) if quick else config.simulation.legitimate_events
    campaigns_per_family = 14 if quick else 42
    campaign_budget = min(config.red_team.campaign_budget, 36) if quick else config.red_team.campaign_budget
    variants_per_family = 10 if quick else 16
    fresh_variants_per_family = 14 if quick else 20

    twin = PaymentDigitalTwin(config.simulation, seed=seed)
    legitimate = twin.generate_legitimate(legitimate_events)
    legit_train, legit_valid, legit_test = _split_legitimate(
        legitimate,
        config.training.validation_fraction,
        config.training.test_fraction,
    )
    known = twin.generate_attack_set(config.training.known_attack_families, campaigns_per_family, seed + 1)
    known_train, known_valid, known_test = _campaign_split(known, rng)
    adaptive_reference = twin.generate_attack_set(
        config.training.adaptive_attack_families,
        campaigns_per_family,
        seed + 2,
    )
    held_out = twin.generate_attack_set(config.training.held_out_attack_families, campaigns_per_family, seed + 3)

    _assert_disjoint(legit_train, legit_valid, "event_id", "legitimate train/validation")
    _assert_disjoint(legit_valid, legit_test, "event_id", "legitimate validation/test")
    _assert_disjoint(known_train, known_valid, "campaign_id", "known attack train/validation")
    _assert_disjoint(known_valid, known_test, "campaign_id", "known attack validation/test")

    train = _balanced_mix(legit_train, known_train, seed)
    valid = _balanced_mix(legit_valid, known_valid, seed + 1)
    defender_v0 = AegisDefender(config.training.target_legitimate_fpr, seed).fit(
        train,
        valid,
        calibration_label="legitimate_validation_temporal_60_80pct",
    )
    gate = FidelityGate(legit_train)

    search_families = config.training.known_attack_families + config.training.adaptive_attack_families
    # The final held-out families remain untouched until evaluation for every
    # defender generation. Adaptive families are exposed only through red-team search.
    action_space = build_action_space(
        seed + 11,
        variants_per_family=variants_per_family,
        families=search_families,
    )
    strategies = [
        RandomStrategy(action_space),
        RuleMutationStrategy(action_space),
        LinUCBStrategy(action_space, context_dim=6, alpha=config.red_team.linucb_alpha),
    ]
    run_frames: list[pd.DataFrame] = []
    campaign_banks: dict[str, list[pd.DataFrame]] = {}
    for index, strategy in enumerate(strategies):
        strategy_twin = PaymentDigitalTwin(config.simulation, seed=seed)
        arena = RedTeamArena(strategy_twin, defender_v0, gate, config.red_team, seed + 100 + index)
        run, campaigns = arena.run(strategy, budget=campaign_budget)
        run_frames.append(run)
        campaign_banks[strategy.name] = campaigns

    no_novelty_config = replace(config.red_team, novelty_bonus=0.0)
    no_novelty = LinUCBStrategy(
        action_space,
        context_dim=6,
        alpha=config.red_team.linucb_alpha,
        name="contextual_bandit_no_novelty",
    )
    no_novelty_run, _ = RedTeamArena(
        PaymentDigitalTwin(config.simulation, seed=seed),
        defender_v0,
        gate,
        no_novelty_config,
        seed + 102,
    ).run(no_novelty, budget=campaign_budget)
    run_frames.append(no_novelty_run)
    attack_runs = pd.concat(run_frames, ignore_index=True)

    defenders: list[AegisDefender] = [defender_v0]
    defender_labels = ["V0"]
    cumulative_attack_train = known_train.copy()
    hardening_frames: list[pd.DataFrame] = []
    initial_hard = _extract_hard_examples(
        campaign_banks["contextual_bandit"],
        config.loop.top_evasions_per_round,
        known_valid,
        "ADV-V0",
    )
    hardening_sources = [(attack_runs[attack_runs["strategy"] == "contextual_bandit"].copy(), initial_hard)]

    for transition in range(config.loop.adversarial_rounds):
        source_run, hard_examples = hardening_sources[transition]
        source_run = source_run.assign(source_defender=f"V{transition}", target_defender=f"V{transition + 1}")
        hardening_frames.append(source_run)
        cumulative_attack_train = pd.concat([cumulative_attack_train, hard_examples], ignore_index=True)
        hardened_train = _balanced_mix(legit_train, cumulative_attack_train, seed + 70 + transition)
        next_defender = AegisDefender(config.training.target_legitimate_fpr, seed + transition + 1).fit(
            hardened_train,
            valid,
            calibration_label="legitimate_validation_temporal_60_80pct",
        )
        defenders.append(next_defender)
        defender_labels.append(f"V{transition + 1}")
        if transition + 1 < config.loop.adversarial_rounds:
            search_space = build_action_space(
                seed + 1200 + transition,
                variants_per_family=variants_per_family,
                families=search_families,
            )
            search_strategy = LinUCBStrategy(
                search_space,
                context_dim=6,
                alpha=config.red_team.linucb_alpha,
                name=f"hardening_search_v{transition + 1}",
            )
            search_run, search_campaigns = RedTeamArena(
                PaymentDigitalTwin(config.simulation, seed=seed),
                next_defender,
                gate,
                config.red_team,
                seed + 1300 + transition,
            ).run(search_strategy, budget=campaign_budget)
            next_hard = _extract_hard_examples(
                search_campaigns,
                config.loop.top_evasions_per_round,
                known_valid,
                f"ADV-V{transition + 1}",
            )
            hardening_sources.append((search_run, next_hard))

    hardening_runs = pd.concat(hardening_frames, ignore_index=True)
    known_eval = _balanced_mix(legit_test, known_test, seed + 3)
    held_eval = _balanced_mix(legit_test, held_out, seed + 4)
    _assert_disjoint(valid, held_eval, "event_id", "calibration validation/held-out evaluation")

    fresh_space = build_action_space(
        seed + 909,
        variants_per_family=fresh_variants_per_family,
        families=search_families,
    )
    fresh_results: dict[str, tuple[pd.DataFrame, list[pd.DataFrame]]] = {}
    evaluations: dict[str, dict[str, dict]] = {}
    loop_rows: list[dict] = []
    family_frames: list[pd.DataFrame] = []
    prevalence_rows: list[dict] = []
    fresh_diagnostic_frames: list[pd.DataFrame] = []
    for index, (label, defender) in enumerate(zip(defender_labels, defenders)):
        known_metrics = defender.evaluate(known_eval).to_dict()
        held_metrics = defender.evaluate(held_eval).to_dict()
        evaluations[label] = {"known": known_metrics, "held_out": held_metrics}
        loop_rows.extend(
            [
                {"defender": label, "test_slice": "known_families", **known_metrics},
                {"defender": label, "test_slice": "held_out_families", **held_metrics},
            ]
        )
        family_frames.append(_family_evaluation(defender, legit_test, held_out, label))
        prevalence_rows.extend(
            _prevalence_evaluation(defender, legit_test, held_out, label, seed + index)
        )
        fresh_strategy = LinUCBStrategy(
            fresh_space,
            6,
            config.red_team.linucb_alpha,
            name=f"fresh_bandit_{label.lower()}",
        )
        fresh_run, fresh_campaigns = RedTeamArena(
            PaymentDigitalTwin(config.simulation, seed=seed),
            defender,
            gate,
            config.red_team,
            seed + 777,
        ).run(fresh_strategy, budget=campaign_budget)
        fresh_results[label] = (fresh_run, fresh_campaigns)
        fresh_diagnostic_frames.append(
            fresh_run.assign(
                seed=seed,
                generation=label,
                protocol="quick" if quick else "full",
                fresh_pool_seed=seed + 909,
                fresh_arena_seed=seed + 777,
                campaign_budget=campaign_budget,
                action_variants_per_family=fresh_variants_per_family,
                search_family_count=len(search_families),
            )
        )
        total_value = max(sum(frame["amount"].sum() for frame in fresh_campaigns), 1e-8)
        loop_rows.append(
            {
                "defender": label,
                "test_slice": "fresh_bandit",
                "roc_auc": np.nan,
                "pr_auc": np.nan,
                "precision": np.nan,
                "recall": float(fresh_run["detection_rate"].mean()),
                "f1": np.nan,
                "legitimate_fpr": held_metrics["legitimate_fpr"],
                "fraud_value_detection_rate": float(1 - fresh_run["approved_value"].sum() / total_value),
                "threshold": held_metrics["threshold"],
                "n_events": int(fresh_run["event_count"].sum()),
            }
        )

    loop_metrics = pd.DataFrame(loop_rows)
    family_metrics = pd.concat(family_frames, ignore_index=True)
    prevalence_metrics = pd.DataFrame(prevalence_rows)
    fresh_diagnostics = pd.concat(fresh_diagnostic_frames, ignore_index=True)
    synthetic_for_fidelity = pd.concat([known, adaptive_reference, held_out], ignore_index=True)
    fidelity_metrics = gate.distribution_report(synthetic_for_fidelity)
    strategy_metrics = {name: _strategy_summary(group) for name, group in attack_runs.groupby("strategy")}

    approved_by_generation = {
        label: float(fresh_results[label][0]["approved_value"].sum()) for label in defender_labels
    }
    generation_results = {}
    for label in defender_labels:
        fresh_run = fresh_results[label][0]
        generation_results[label] = {
            "known": evaluations[label]["known"],
            "held_out": evaluations[label]["held_out"],
            "fresh_attacker_approved_value": approved_by_generation[label],
            "fresh_attacker_mean_reward": float(fresh_run["reward"].mean()),
            "fresh_attacker_mean_detection_rate": float(fresh_run["detection_rate"].mean()),
            "calibration": next(defender.calibration_metadata for name, defender in zip(defender_labels, defenders) if name == label),
        }
    for prior, current in pairwise(defender_labels):
        generation_results[current]["fresh_value_reduction_vs_prior"] = float(
            1 - approved_by_generation[current] / max(approved_by_generation[prior], 1e-8)
        )
    final_label = defender_labels[-1]
    generation_results[final_label]["fresh_value_reduction_vs_v0"] = float(
        1 - approved_by_generation[final_label] / max(approved_by_generation["V0"], 1e-8)
    )

    latency_samples = []
    latency_frame = held_eval.reset_index(drop=True)
    final_defender = defenders[-1]
    for index in range(min(80, len(latency_frame))):
        one_event = latency_frame.iloc[[index]]
        start = perf_counter()
        final_defender.score(one_event)
        latency_samples.append((perf_counter() - start) * 1000)

    calibration_audit = {
        "calibration_split": "legitimate validation rows from temporal 60%-80% window",
        "evaluation_split": "legitimate test rows from temporal 80%-100% window plus separately generated attack campaigns",
        "legitimate_split_rows": {
            "train": len(legit_train),
            "validation": len(legit_valid),
            "test": len(legit_test),
        },
        "event_id_overlap_validation_test": 0,
        "known_campaign_overlap_train_validation": 0,
        "known_campaign_overlap_validation_test": 0,
        "held_out_campaigns_generated_separately": True,
        "thresholds": {label: defender.calibration_metadata for label, defender in zip(defender_labels, defenders)},
        "test_rows_used_for_threshold_selection": False,
    }

    bandit_reward = strategy_metrics["contextual_bandit"]["mean_reward"]
    random_reward = strategy_metrics["random"]["mean_reward"]
    rule_reward = strategy_metrics["rule_mutation"]["mean_reward"]
    novelty_off_reward = strategy_metrics["contextual_bandit_no_novelty"]["mean_reward"]
    corpus_attack_events = len(known) + len(adaptive_reference) + len(held_out)
    summary = {
        "seed": seed,
        "quick": quick,
        "protocol": "quick" if quick else "full",
        "events": {
            "legitimate": len(legitimate),
            "known_attack": len(known),
            "adaptive_reference_attack": len(adaptive_reference),
            "held_out_attack": len(held_out),
            "corpus_attack_prevalence": float(corpus_attack_events / (len(legitimate) + corpus_attack_events)),
        },
        "attack_atlas": {
            "vectors": sum(len(card.variants) for card in ATTACK_ATLAS),
            "executable_archetypes": len(ATTACK_ATLAS),
            "families": len(ATTACK_ATLAS),
            "channels": len({card.channel for card in ATTACK_ATLAS}),
            "rails": len({card.rail for card in ATTACK_ATLAS}),
        },
        "strategy_metrics": strategy_metrics,
        "reward_ablation": {
            "novelty_on_mean_reward": bandit_reward,
            "novelty_off_mean_reward": novelty_off_reward,
            "absolute_difference": float(bandit_reward - novelty_off_reward),
            "relative_difference": float((bandit_reward - novelty_off_reward) / max(abs(novelty_off_reward), 1e-8)),
        },
        "defender": {
            "v0_known": evaluations["V0"]["known"],
            "v0_held_out": evaluations["V0"]["held_out"],
            "v1_known": evaluations["V1"]["known"],
            "v1_held_out": evaluations["V1"]["held_out"],
            "v2_known": evaluations.get("V2", evaluations[final_label])["known"],
            "v2_held_out": evaluations.get("V2", evaluations[final_label])["held_out"],
            "fresh_attacker_approved_value_v0": approved_by_generation["V0"],
            "fresh_attacker_approved_value_v1": approved_by_generation["V1"],
            "fresh_attacker_approved_value_v2": approved_by_generation.get("V2", approved_by_generation[final_label]),
            "fresh_attacker_value_reduction": float(
                1 - approved_by_generation["V1"] / max(approved_by_generation["V0"], 1e-8)
            ),
            "fresh_attacker_value_reduction_v1_to_v2": float(
                1 - approved_by_generation.get("V2", approved_by_generation[final_label])
                / max(approved_by_generation["V1"], 1e-8)
            ),
            "fresh_attacker_value_reduction_v0_to_v2": float(
                1 - approved_by_generation.get("V2", approved_by_generation[final_label])
                / max(approved_by_generation["V0"], 1e-8)
            ),
            "generations": generation_results,
        },
        "claims": {
            "learned_attacker_beats_random": bool(bandit_reward > random_reward),
            "learned_attacker_beats_rule_mutation": bool(bandit_reward > rule_reward),
            "v1_reduces_fresh_attacker_value": bool(approved_by_generation["V1"] < approved_by_generation["V0"]),
            "v2_reduces_fresh_attacker_value": bool(approved_by_generation.get("V2", np.inf) < approved_by_generation["V1"]),
        },
        "fidelity": fidelity_metrics,
        "serving": {
            "single_event_latency_ms_p50": float(np.percentile(latency_samples, 50)),
            "single_event_latency_ms_p95": float(np.percentile(latency_samples, 95)),
            "measurement": "local commodity CPU, in-process single-event scoring",
        },
        "evaluation_protocol": {
            "held_out_families": config.training.held_out_attack_families,
            "initial_supervised_attack_families": config.training.known_attack_families,
            "adaptive_red_team_only_families": config.training.adaptive_attack_families,
            "hardening_search_families": search_families,
            "held_out_families_excluded_from_all_hardening": True,
            "target_legitimate_fpr": config.training.target_legitimate_fpr,
            "equal_campaign_budget": campaign_budget,
            "campaigns_per_family": campaigns_per_family,
            "action_variants_per_family": variants_per_family,
            "fresh_action_variants_per_family": fresh_variants_per_family,
            "defender_frozen_during_attack_search": True,
            "fresh_action_space_for_generation_tests": True,
            "adversarial_hardening_transitions": config.loop.adversarial_rounds,
            "threshold_calibration": calibration_audit,
        },
    }
    return BenchmarkArtifacts(
        summary,
        attack_runs,
        loop_metrics,
        family_metrics,
        fidelity_metrics,
        prevalence_metrics,
        hardening_runs,
        calibration_audit,
        fresh_diagnostics,
    )


def save_artifacts(artifacts: BenchmarkArtifacts, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(artifacts.summary, handle, indent=2, allow_nan=True)
    artifacts.attack_runs.to_csv(output / "attack_strategy_runs.csv", index=False)
    artifacts.loop_metrics.to_csv(output / "defender_loop_metrics.csv", index=False)
    artifacts.family_metrics.to_csv(output / "held_out_family_metrics.csv", index=False)
    artifacts.prevalence_metrics.to_csv(output / "prevalence_metrics.csv", index=False)
    artifacts.hardening_runs.to_csv(output / "hardening_generation_runs.csv", index=False)
    artifacts.fresh_diagnostics.to_csv(output / "fresh_campaign_diagnostics.csv", index=False)
    with (output / "calibration_audit.json").open("w", encoding="utf-8") as handle:
        json.dump(artifacts.calibration_audit, handle, indent=2)
    with (output / "attack_atlas.json").open("w", encoding="utf-8") as handle:
        json.dump(scenario_dsl(), handle, indent=2)
