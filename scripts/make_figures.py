"""Build every figure in the AegisLoop solution paper from versioned evidence.

Usage:
    python scripts/make_figures.py

Outputs PNG and SVG copies under artifacts/paper/figures. The analytical
figures read only approved evidence artifacts; the two system diagrams read
the approved architecture document and attack-atlas artifact respectively.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

NAVY = "#10233F"
BLUE = "#2457C5"
CYAN = "#11A7A0"
ORANGE = "#EF7B28"
RED = "#C23B36"
SLATE = "#566477"
LIGHT = "#EEF3F8"
MID = "#C8D2DE"
WHITE = "#FFFFFF"


def configure_style() -> None:
    plt.switch_backend("Agg")
    mpl.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 9.5,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.5,
            "axes.edgecolor": MID,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "grid.color": "#E5EAF0",
            "grid.linewidth": 0.7,
            "grid.alpha": 0.85,
            "xtick.color": SLATE,
            "ytick.color": SLATE,
            "text.color": NAVY,
            "figure.facecolor": WHITE,
            "axes.facecolor": WHITE,
            "legend.frameon": False,
            "savefig.facecolor": WHITE,
            "savefig.bbox": "tight",
            "svg.fonttype": "none",
        }
    )


def save(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)


def box(ax, xy, width, height, title, body, color, *, fontsize=8.4):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=WHITE, edgecolor=color, linewidth=1.6,
    )
    ax.add_patch(patch)
    ax.add_patch(
        FancyBboxPatch(
            (x, y + height - 0.18 * height), width, 0.18 * height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor=color, edgecolor=color, linewidth=0,
        )
    )
    ax.text(x + 0.018, y + height - 0.09 * height, title, color=WHITE, weight="bold", va="center")
    ax.text(
        x + 0.024, y + height - 0.23 * height, body,
        color=NAVY, va="top", ha="left", fontsize=fontsize, linespacing=1.25,
    )
    return patch


def arrow(ax, start, end, color=SLATE, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            start, end, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
            mutation_scale=12, linewidth=1.4, color=color,
        )
    )


def architecture_figure(output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.75))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.96, "AegisLoop closes the attack-to-defense learning loop", fontsize=15, weight="bold")
    ax.text(0.02, 0.91, "Offline synthetic threat laboratory; no connection to live payment rails", color=SLATE, fontsize=9.5)

    box(ax, (0.02, 0.56), 0.21, 0.26, "1  IDENTIFY", "8 equal archetypes\n32 research variants\nScenario DSL", BLUE)
    box(ax, (0.27, 0.56), 0.21, 0.26, "2  GENERATE", "Stateful entity-linked\npayment digital twin\nFidelity firewall", CYAN)
    box(ax, (0.52, 0.56), 0.21, 0.26, "3  ADAPT", "LinUCB chooses full\ncampaign parameters\nImmediate feedback", ORANGE)
    box(ax, (0.77, 0.56), 0.21, 0.26, "4  DEFEND", "GBDT + anomaly +\nrelationship / intent\nrisk ensemble", RED)
    for x1, x2 in [(0.23, 0.27), (0.48, 0.52), (0.73, 0.77)]:
        arrow(ax, (x1 + 0.003, 0.69), (x2 - 0.003, 0.69))

    arrow(ax, (0.88, 0.55), (0.88, 0.35), RED)
    box(
        ax, (0.57, 0.14), 0.39, 0.19, "GOVERNED HARDENING BOUNDARY",
        "Valid, positive-value evasions only\nRetrain -> recalibrate -> freeze",
        NAVY, fontsize=7.7,
    )
    arrow(ax, (0.57, 0.235), (0.53, 0.235), NAVY)
    box(
        ax, (0.02, 0.14), 0.51, 0.19, "EVIDENCE CONTRACT",
        "Temporal train / validation / test\nHeld-out families stay outside hardening\nFive seeds; paired baselines",
        SLATE, fontsize=7.7,
    )
    arrow(ax, (0.125, 0.33), (0.125, 0.55), BLUE)
    ax.text(0.5, 0.035, "Evidence source: docs/ARCHITECTURE.md and docs/BENCHMARKS.md", ha="center", color=SLATE, fontsize=7.5)
    save(fig, output_dir, "fig01_closed_loop_architecture")


def taxonomy_figure(atlas_path: Path, output_dir: Path) -> None:
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(8.0, 7.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.965, "Attack atlas: equal coverage across the payment lifecycle", fontsize=15, weight="bold")
    ax.text(0.02, 0.925, "Eight archetypes x four variants; three are illustrative case studies, not a selection hierarchy", color=SLATE)
    colors = [BLUE, CYAN, ORANGE, RED, "#6C56B3", "#297A66", "#B65B8F", "#8A6A2F"]
    case_studies = {"ai_app_scam_mule", "agentic_intent_hijack", "synthetic_evidence_refund"}
    positions = [(0.02, 0.70), (0.51, 0.70), (0.02, 0.48), (0.51, 0.48), (0.02, 0.26), (0.51, 0.26), (0.02, 0.04), (0.51, 0.04)]
    for item, color, pos in zip(atlas, colors, positions, strict=True):
        title = item["title"]
        variants = " | ".join(item["variants"])
        case_label = "Illustrative case study\n" if item["family"] in case_studies else ""
        body = case_label + f"{item['channel']} / {item['rail']}\n" + textwrap.fill(variants, width=54)
        box(ax, pos, 0.47, 0.18, title, body, color, fontsize=7.2)
    save(fig, output_dir, "fig02_attack_atlas")


def reward_figure(seed_path: Path, aggregate_path: Path, output_dir: Path) -> None:
    seed = pd.read_csv(seed_path)
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    series = [
        ("Contextual\nbandit", "contextual_bandit_reward", BLUE),
        ("Rule\nmutation", "rule_mutation_reward", ORANGE),
        ("Random\nsearch", "random_reward", SLATE),
    ]
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    rng = np.random.default_rng(20260812)
    for i, (_, column, color) in enumerate(series):
        values = seed[column].to_numpy()
        metric = aggregate[column]
        jitter = rng.normal(0, 0.025, size=len(values))
        ax.scatter(np.full(len(values), i) + jitter, values, s=38, color=color, alpha=0.82, edgecolor=WHITE, linewidth=0.8, zorder=3)
        ax.errorbar(
            i, metric["mean"],
            yerr=[[metric["mean"] - metric["ci95_low"]], [metric["ci95_high"] - metric["mean"]]],
            fmt="D", ms=7, color=NAVY, capsize=6, linewidth=2, zorder=4,
        )
        ax.text(i, metric["ci95_high"] + 0.09, f"{metric['mean']:.3f}", ha="center", weight="bold")
    ax.axhline(0, color=MID, linewidth=1)
    ax.set_xticks(range(3), [s[0] for s in series])
    ax.set_ylabel("Mean campaign reward")
    fig.suptitle("The contextual bandit wins every paired seed against both baselines", x=0.08, ha="left", fontsize=14, weight="bold")
    fig.text(0.08, 0.92, "Diamonds: mean; bars: bootstrap 95% CI; circles: all five fixed seeds", color=SLATE)
    ax.text(0.99, 0.02, "Paired one-sided Wilcoxon p=0.03125 vs each baseline", transform=ax.transAxes, ha="right", color=SLATE, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(top=0.82)
    save(fig, output_dir, "fig03_reward_comparison")


def defender_progression_figure(aggregate_path: Path, output_dir: Path) -> None:
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    generations = ["V0", "V1", "V2"]
    metrics = [("held_out_auc", "ROC-AUC", BLUE), ("held_out_recall", "Recall", RED)]
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.4), sharex=True)
    for ax, (suffix, title, color) in zip(axes, metrics, strict=True):
        means = np.array([aggregate[f"{g.lower()}_{suffix}"]["mean"] for g in generations])
        lows = np.array([aggregate[f"{g.lower()}_{suffix}"]["ci95_low"] for g in generations])
        highs = np.array([aggregate[f"{g.lower()}_{suffix}"]["ci95_high"] for g in generations])
        x = np.arange(3)
        ax.fill_between(x, lows, highs, color=color, alpha=0.13)
        ax.plot(x, means, marker="o", ms=7, lw=2.2, color=color)
        for xi, value in zip(x, means, strict=True):
            ax.text(xi, value + 0.0025, f"{value:.4f}", ha="center", weight="bold", fontsize=8.5)
        ax.set_xticks(x, generations)
        ax.set_title(title, loc="left")
        ax.set_ylim(0.82 if suffix.endswith("recall") else 0.965, 1.008)
        ax.set_ylabel(title)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Held-out-family performance improves through two hardening cycles", x=0.055, ha="left", fontsize=14, weight="bold")
    fig.text(0.055, 0.92, "Lines: five-seed mean; bands: bootstrap 95% CI", color=SLATE)
    fig.subplots_adjust(top=0.80, wspace=0.26)
    save(fig, output_dir, "fig04_defender_progression")


def approved_value_figure(seed_path: Path, diagnostic_path: Path, output_dir: Path) -> None:
    seed = pd.read_csv(seed_path)
    diagnostic = pd.read_csv(diagnostic_path)
    generations = ["V0", "V1", "V2"]
    columns = ["v0_fresh_approved_value", "v1_fresh_approved_value", "v2_fresh_approved_value"]
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    x = np.arange(3)
    for _, row in seed.iterrows():
        values = [row[column] for column in columns]
        ax.plot(x, values, color=MID, lw=1.25, alpha=0.95, marker="o", ms=4)
    means = [seed[column].mean() for column in columns]
    ax.plot(x, means, color=RED, lw=2.6, marker="D", ms=7, label="Five-seed mean", zorder=4)
    for xi, value in zip(x, means, strict=True):
        ax.text(xi, value + 2300, f"{value:,.0f}", ha="center", weight="bold", color=RED)
    valid = int(diagnostic.groupby("seed")["seed_valid_campaigns"].first().min())
    detected = int(diagnostic.groupby("seed")["seed_fully_detected_campaigns"].first().min())
    actions = diagnostic.groupby("seed")["seed_unique_actions"].first()
    caveat = (
        "Matched fixed action pool held constant across generations; fresh policies reset.\n"
        f"V2 diagnostic: {valid}/72 valid and {detected}/72 detected per seed; "
        f"{actions.min()}-{actions.max()} unique actions."
    )
    ax.text(
        0.985, 0.96, caveat, transform=ax.transAxes, ha="right", va="top", fontsize=8.3, color=NAVY,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": LIGHT, "edgecolor": MID},
    )
    ax.set_xticks(x, generations)
    ax.set_ylabel("Approved synthetic value per 72-campaign run")
    ax.set_title("Approved value falls across matched attacker-defender generations", loc="left")
    ax.set_ylim(bottom=-1500)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="center right")
    save(fig, output_dir, "fig05_fresh_approved_value")


def prevalence_figure(prevalence_path: Path, output_dir: Path) -> None:
    data = pd.read_csv(prevalence_path)
    selected = data[data["scenario"].isin(["experiment_prevalence", "deployment_exact_prevalence_reweighted_0.015pct"])].copy()
    colors = {"V0": BLUE, "V1": ORANGE, "V2": RED}
    low_offsets = {"V0": (7, 20), "V1": (7, 8), "V2": (7, -7)}
    high_offsets = {"V0": (7, 12), "V1": (7, -1), "V2": (7, -14)}
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    for defender in ["V0", "V1", "V2"]:
        rows = selected[selected["defender"] == defender].sort_values("prevalence")
        ax.plot(rows["prevalence"] * 100, rows["precision_mean"] * 100, marker="o", ms=7, lw=2.2, color=colors[defender], label=defender)
        for _, row in rows.iterrows():
            offset = low_offsets[defender] if row["prevalence"] < 0.001 else high_offsets[defender]
            ax.annotate(
                f"{row['precision_mean'] * 100:.2f}%",
                (row["prevalence"] * 100, row["precision_mean"] * 100),
                xytext=offset, textcoords="offset points", color=colors[defender], fontsize=8, weight="bold",
            )
    ax.set_xscale("log")
    ax.set_xlim(0.008, 18)
    ax.set_ylim(-3, 100)
    ax.set_xlabel("Attack prevalence (%) - logarithmic scale")
    ax.set_ylabel("Precision at fixed score and threshold (%)")
    fig.suptitle("High lab precision does not survive realistic prevalence", x=0.08, ha="left", fontsize=14, weight="bold")
    fig.text(0.08, 0.92, "Seed 20260812; exact importance reweighting to 0.015%", color=SLATE)
    ax.text(
        0.48, 0.06,
        "Only the two evaluated endpoints are shown.\nConnecting segments are visual guides, not intermediate estimates.",
        transform=ax.transAxes, fontsize=8.2, color=NAVY, ha="center",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": LIGHT, "edgecolor": MID},
    )
    ax.legend(loc="center right", title="Defender")
    ax.spines[["top", "right"]].set_visible(False)
    fig.subplots_adjust(top=0.82)
    save(fig, output_dir, "fig06_precision_prevalence")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output_dir = (args.output or repo / "artifacts" / "paper" / "figures").resolve()
    configure_style()
    architecture_figure(output_dir)
    taxonomy_figure(repo / "artifacts" / "precomputed" / "attack_atlas.json", output_dir)
    reward_figure(repo / "artifacts" / "full_multiseed" / "seed_results.csv", repo / "artifacts" / "full_multiseed" / "aggregate.json", output_dir)
    defender_progression_figure(repo / "artifacts" / "full_multiseed" / "aggregate.json", output_dir)
    approved_value_figure(repo / "artifacts" / "full_multiseed" / "seed_results.csv", repo / "artifacts" / "precomputed" / "v2_campaign_diagnostics.csv", output_dir)
    prevalence_figure(repo / "artifacts" / "precomputed" / "prevalence_metrics.csv", output_dir)
    print(f"Wrote six figures (PNG + SVG) to {output_dir}")


if __name__ == "__main__":
    main()
