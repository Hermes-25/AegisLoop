from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from run_post_lock_robustness import PROJECT_ROOT, build_v2

from aegisloop.config import load_config
from aegisloop.redteam import LinUCBStrategy, RedTeamArena, build_action_space
from aegisloop.simulator import PaymentDigitalTwin


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "post_lock_robustness",
    )
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    seed = 20260813
    base = load_config(PROJECT_ROOT / "config" / "default.yaml")
    config = replace(base, seed=seed)
    defender, gate = build_v2(config)
    families = config.training.known_attack_families + config.training.adaptive_attack_families
    actions = build_action_space(seed + 90_000, variants_per_family=40, families=families)
    strategy = LinUCBStrategy(
        actions,
        context_dim=6,
        alpha=config.red_team.linucb_alpha,
        name="v2_double_search_pressure_diagnostic",
    )
    run, campaigns = RedTeamArena(
        PaymentDigitalTwin(config.simulation, seed=seed),
        defender,
        gate,
        config.red_team,
        seed + 100_000,
    ).run(strategy, budget=144)
    positive = run[run["approved_value"] > 0].copy()
    if len(positive) != 1:
        raise AssertionError(f"Expected one positive-value campaign, found {len(positive)}")
    iteration = int(positive.iloc[0]["iteration"])
    campaign = campaigns[iteration].copy()
    campaign["risk_score"] = defender.score(campaign)
    buckets = defender._event_buckets(campaign)
    campaign["operational_threshold"] = defender.event_thresholds()[buckets]
    campaign["score_margin"] = campaign["risk_score"] - campaign["operational_threshold"]
    campaign["detected"] = defender.detected_mask(campaign).astype(bool)
    campaign.to_csv(output / "stress_escape_events.csv", index=False)
    positive.to_csv(output / "stress_escape_summary.csv", index=False)
    missed = campaign[~campaign["detected"]].copy()
    diagnostic = {
        "defender_seed": seed,
        "iteration": iteration,
        "action_id": str(positive.iloc[0]["action_id"]),
        "family": str(positive.iloc[0]["family"]),
        "campaign_events": len(campaign),
        "detected_events": int(campaign["detected"].sum()),
        "missed_events": int((~campaign["detected"]).sum()),
        "approved_value": float(positive.iloc[0]["approved_value"]),
        "base_calibrated_threshold": float(defender.threshold),
        "missed_event_amounts": [float(value) for value in missed["amount"]],
        "missed_event_scores": [float(value) for value in missed["risk_score"]],
        "missed_event_operational_thresholds": [
            float(value) for value in missed["operational_threshold"]
        ],
        "missed_event_score_margins": [float(value) for value in missed["score_margin"]],
        "missed_event_steps": [int(value) for value in missed["campaign_step"]],
    }
    with (output / "stress_escape_diagnostic.json").open("w", encoding="utf-8") as handle:
        json.dump(diagnostic, handle, indent=2)
    print(json.dumps(diagnostic, indent=2))


if __name__ == "__main__":
    main()
