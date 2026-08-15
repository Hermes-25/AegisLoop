from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegisloop.config import load_config
from aegisloop.experiment import run_benchmark


def _bootstrap_mean_ci(values: np.ndarray, seed: int, draws: int = 20_000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    bootstrap = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))


def _describe(values: np.ndarray, seed: int) -> dict:
    low, high = _bootstrap_mean_ci(values, seed)
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "ci95_low": low,
        "ci95_high": high,
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "n": len(values),
    }


def _paired_test(results: pd.DataFrame, treatment: str, baseline: str, seed: int) -> dict:
    treatment_values = results[treatment].to_numpy(dtype=float)
    baseline_values = results[baseline].to_numpy(dtype=float)
    differences = treatment_values - baseline_values
    ci_low, ci_high = _bootstrap_mean_ci(differences, seed)
    test = (
        wilcoxon(treatment_values, baseline_values, alternative="greater", method="auto")
        if len(differences) >= 2 and np.any(differences != 0)
        else None
    )
    return {
        "test": "paired Wilcoxon signed-rank",
        "alternative": f"{treatment} > {baseline}",
        "statistic": float(test.statistic) if test else float("nan"),
        "p_value_one_sided": float(test.pvalue) if test else float("nan"),
        "mean_paired_difference": float(np.mean(differences)),
        "mean_difference_ci95_low": ci_low,
        "mean_difference_ci95_high": ci_high,
        "wins": int(np.sum(differences > 0)),
        "ties": int(np.sum(differences == 0)),
        "n_pairs": len(differences),
    }


def _paired_two_sided(results: pd.DataFrame, treatment: str, baseline: str, seed: int) -> dict:
    treatment_values = results[treatment].to_numpy(dtype=float)
    baseline_values = results[baseline].to_numpy(dtype=float)
    differences = treatment_values - baseline_values
    ci_low, ci_high = _bootstrap_mean_ci(differences, seed)
    test = (
        wilcoxon(treatment_values, baseline_values, alternative="two-sided", method="auto")
        if len(differences) >= 2 and np.any(differences != 0)
        else None
    )
    return {
        "test": "paired Wilcoxon signed-rank",
        "alternative": "two-sided",
        "statistic": float(test.statistic) if test else float("nan"),
        "p_value_two_sided": float(test.pvalue) if test else float("nan"),
        "mean_paired_difference": float(np.mean(differences)),
        "mean_difference_ci95_low": ci_low,
        "mean_difference_ci95_high": ci_high,
        "positive_differences": int(np.sum(differences > 0)),
        "negative_differences": int(np.sum(differences < 0)),
        "n_pairs": len(differences),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AegisLoop over multiple deterministic seeds.")
    parser.add_argument("--config", default=str(ROOT / "config" / "default.yaml"))
    parser.add_argument("--output", default=None)
    parser.add_argument("--seeds", default="20260812,20260813,20260814,20260815,20260816")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    protocol = "quick" if args.quick else "full"
    output = Path(args.output) if args.output else ROOT / "artifacts" / f"{protocol}_multiseed"
    output.mkdir(parents=True, exist_ok=True)
    base = load_config(args.config)
    seed_values = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    rows = []
    fresh_diagnostic_frames = []
    for seed in seed_values:
        artifacts = run_benchmark(replace(base, seed=seed), quick=args.quick)
        summary = artifacts.summary
        fresh_diagnostic_frames.append(artifacts.fresh_diagnostics)
        row = {"seed": seed, "protocol": protocol}
        for strategy, metrics in summary["strategy_metrics"].items():
            row[f"{strategy}_reward"] = metrics["mean_reward"]
            row[f"{strategy}_approved_value"] = metrics["total_approved_value"]
            row[f"{strategy}_detection_rate"] = metrics["mean_detection_rate"]
        generations = summary["defender"]["generations"]
        for generation in ("V0", "V1", "V2"):
            metrics = generations[generation]["held_out"]
            row[f"{generation.lower()}_held_out_auc"] = metrics["roc_auc"]
            row[f"{generation.lower()}_held_out_precision"] = metrics["precision"]
            row[f"{generation.lower()}_held_out_recall"] = metrics["recall"]
            row[f"{generation.lower()}_held_out_fpr"] = metrics["legitimate_fpr"]
            row[f"{generation.lower()}_fresh_reward"] = generations[generation]["fresh_attacker_mean_reward"]
            row[f"{generation.lower()}_fresh_approved_value"] = generations[generation]["fresh_attacker_approved_value"]
        row.update(
            {
                "fresh_value_reduction_v0_to_v1": summary["defender"]["fresh_attacker_value_reduction"],
                "fresh_value_reduction_v1_to_v2": summary["defender"]["fresh_attacker_value_reduction_v1_to_v2"],
                "fresh_value_reduction_v0_to_v2": summary["defender"]["fresh_attacker_value_reduction_v0_to_v2"],
                "novelty_ablation_reward_delta": summary["reward_ablation"]["absolute_difference"],
            }
        )
        rows.append(row)
        print(
            f"protocol={protocol} seed={seed} "
            f"bandit={row['contextual_bandit_reward']:.3f} random={row['random_reward']:.3f} "
            f"V0/V1/V2 AUC={row['v0_held_out_auc']:.3f}/{row['v1_held_out_auc']:.3f}/{row['v2_held_out_auc']:.3f}",
            flush=True,
        )
    results = pd.DataFrame(rows)
    results.to_csv(output / "seed_results.csv", index=False)
    fresh_diagnostics = pd.concat(fresh_diagnostic_frames, ignore_index=True)
    fresh_diagnostics.to_csv(output / "fresh_campaign_diagnostics.csv", index=False)
    if not args.quick:
        v2 = fresh_diagnostics[fresh_diagnostics["generation"] == "V2"].copy()
        rollup = v2.groupby("seed", sort=True).agg(
            seed_campaigns=("iteration", "size"),
            seed_valid_campaigns=("valid", "sum"),
            seed_invalid_campaigns=("valid", lambda values: int((~values.astype(bool)).sum())),
            seed_fully_detected_campaigns=("detection_rate", lambda values: int((values == 1.0).sum())),
            seed_total_events=("event_count", "sum"),
            seed_approved_value=("approved_value", "sum"),
            seed_mean_detection_rate=("detection_rate", "mean"),
            seed_mean_fidelity=("fidelity", "mean"),
            seed_min_fidelity=("fidelity", "min"),
            seed_median_fidelity=("fidelity", "median"),
            seed_max_fidelity=("fidelity", "max"),
            seed_unique_actions=("action_id", "nunique"),
            seed_families_selected=("family", "nunique"),
            seed_mean_reward=("reward", "mean"),
        ).reset_index()
        v2 = v2.merge(rollup, on="seed", how="left")
        v2.insert(0, "artifact_version", "1.0")
        v2_output = ROOT / "artifacts" / "precomputed" / "v2_campaign_diagnostics.csv"
        v2_output.parent.mkdir(parents=True, exist_ok=True)
        v2.to_csv(v2_output, index=False)
    aggregate: dict[str, object] = {
        "protocol": protocol,
        "seeds": seed_values,
        "n_seeds": len(seed_values),
        "bootstrap_draws": 20_000,
        "confidence_interval": "nonparametric bootstrap 95% CI for the seed-level mean",
    }
    for index, column in enumerate(results.columns):
        if column in {"seed", "protocol"}:
            continue
        aggregate[column] = _describe(results[column].to_numpy(dtype=float), seed_values[0] + index)
    aggregate["bandit_win_rate_vs_random"] = float(
        np.mean(results["contextual_bandit_reward"] > results["random_reward"])
    )
    aggregate["bandit_win_rate_vs_rule"] = float(
        np.mean(results["contextual_bandit_reward"] > results["rule_mutation_reward"])
    )
    aggregate["significance_tests"] = {
        "bandit_vs_random": _paired_test(
            results,
            "contextual_bandit_reward",
            "random_reward",
            seed_values[0] + 91,
        ),
        "bandit_vs_rule": _paired_test(
            results,
            "contextual_bandit_reward",
            "rule_mutation_reward",
            seed_values[0] + 92,
        ),
        "novelty_on_vs_off": _paired_two_sided(
            results,
            "contextual_bandit_reward",
            "contextual_bandit_no_novelty_reward",
            seed_values[0] + 95,
        ),
        "v1_vs_v0_fresh_reward": _paired_test(
            results,
            "v0_fresh_reward",
            "v1_fresh_reward",
            seed_values[0] + 93,
        ),
        "v2_vs_v1_fresh_reward": _paired_test(
            results,
            "v1_fresh_reward",
            "v2_fresh_reward",
            seed_values[0] + 94,
        ),
    }
    with (output / "aggregate.json").open("w", encoding="utf-8") as handle:
        json.dump(aggregate, handle, indent=2)


if __name__ == "__main__":
    main()
