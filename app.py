from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts" / "precomputed"
MULTISEED = ROOT / "artifacts" / "full_multiseed"

st.set_page_config(page_title="AegisLoop | Payment Threat Digital Twin", page_icon="🛡️", layout="wide")
st.markdown(
    """
<style>
:root { --ink:#0e223d; --orange:#e45a21; --blue:#236baa; --paper:#f5f7fa; }
.stApp { background: var(--paper); }
[data-testid="stSidebar"] { background: #0e223d; }
[data-testid="stSidebar"] * { color: #eef4fa; }
.hero { padding: 1.35rem 1.55rem; border-radius: 18px; color:white;
  background: linear-gradient(125deg,#0e223d 0%,#15395f 62%,#e45a21 160%); margin-bottom:1rem; }
.hero h1 { font-size:3rem; margin:0; letter-spacing:-.04em; }
.hero p { font-size:1.15rem; color:#dce8f5; margin:.45rem 0 0; max-width:900px; }
.pill { display:inline-block; padding:.3rem .65rem; border-radius:999px; background:#e45a21;
 color:white; font-weight:700; font-size:.78rem; letter-spacing:.04em; }
.metric-card { background:white; border:1px solid #dce3eb; border-radius:14px; padding:1rem 1.1rem; min-height:126px; }
.metric-card .value { color:#0e223d; font-size:2rem; font-weight:800; letter-spacing:-.04em; }
.metric-card .label { color:#52657a; font-size:.84rem; font-weight:700; text-transform:uppercase; }
.metric-card .detail { color:#60758a; font-size:.82rem; margin-top:.25rem; }
.stage { background:white; border:1px solid #dce3eb; border-radius:14px; padding:1rem 1.1rem; min-height:190px; }
.stage b { color:#e45a21; }
.proof { border-left:5px solid #e45a21; background:#fff; padding:.85rem 1rem; border-radius:8px; }
div[data-testid="stMetricValue"] { color:#0e223d; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_evidence():
    try:
        with (ARTIFACTS / "summary.json").open("r", encoding="utf-8") as handle:
            summary = json.load(handle)
        required = {"seed", "attack_atlas", "strategy_metrics", "defender", "evaluation_protocol"}
        missing = sorted(required.difference(summary))
        if missing:
            raise ValueError(f"summary.json is missing required keys: {', '.join(missing)}")
        attacks = pd.read_csv(ARTIFACTS / "attack_strategy_runs.csv")
        loop = pd.read_csv(ARTIFACTS / "defender_loop_metrics.csv")
        family = pd.read_csv(ARTIFACTS / "held_out_family_metrics.csv")
        with (ARTIFACTS / "attack_atlas.json").open("r", encoding="utf-8") as handle:
            atlas = json.load(handle)
        seeds = pd.read_csv(MULTISEED / "seed_results.csv") if (MULTISEED / "seed_results.csv").exists() else pd.DataFrame()
        aggregate = {}
        if (MULTISEED / "aggregate.json").exists():
            with (MULTISEED / "aggregate.json").open("r", encoding="utf-8") as handle:
                aggregate = json.load(handle)
        return summary, attacks, loop, family, atlas, seeds, aggregate
    except (OSError, ValueError, json.JSONDecodeError, pd.errors.ParserError) as exc:
        raise RuntimeError(
            "Evidence artifacts are missing or malformed. Run "
            "`python experiments/run_benchmark.py` to rebuild them. "
            f"Original error: {exc}"
        ) from exc


try:
    summary, attacks, loop, family, atlas, seeds, aggregate = load_evidence()
except RuntimeError as exc:
    st.error("AegisLoop evidence is unavailable, so the dashboard cannot render safely.")
    st.code(str(exc))
    st.stop()

with st.sidebar:
    st.markdown("## AegisLoop")
    page = st.radio(
        "Judge view",
        ["Mission control", "Attack atlas", "Red-team arena", "Defence hardening", "Evidence & governance"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Reproducible run")
    st.code(f"seed = {summary['seed']}\nbudget = {summary['evaluation_protocol']['equal_campaign_budget']} campaigns")
    st.caption("Synthetic-only • offline • no payment-network connectors")

st.markdown(
    """
<div class="hero">
  <span class="pill">NOVELTY = LEARNING ADVERSARY</span>
  <h1>AegisLoop</h1>
  <p>A self-evolving payment threat digital twin: ground emerging attacks, learn realistic evasions,
  and turn every valid blind spot into evidence for a stronger defence—before production.</p>
</div>
""",
    unsafe_allow_html=True,
)

strategy = summary["strategy_metrics"]
defence = summary["defender"]

if page == "Mission control":
    cols = st.columns(4)
    cards = [
        (f"{summary['attack_atlas']['vectors']}", "grounded attack vectors", f"{summary['attack_atlas']['executable_archetypes']} executable archetypes • {summary['attack_atlas']['channels']} channels"),
        (f"{strategy['contextual_bandit']['mean_reward']:.3f}", "bandit mean reward", f"random {strategy['random']['mean_reward']:.3f}"),
        (f"{defence['fresh_attacker_value_reduction']:.1%}", "fresh fraud value reduced", "V1 versus V0, fresh action space"),
        (f"{defence['v1_held_out']['roc_auc']:.3f}", "held-out-family ROC-AUC", f"legitimate FPR {defence['v1_held_out']['legitimate_fpr']:.2%}"),
    ]
    for col, (value, label, detail) in zip(cols, cards):
        col.markdown(f'<div class="metric-card"><div class="value">{value}</div><div class="label">{label}</div><div class="detail">{detail}</div></div>', unsafe_allow_html=True)

    st.markdown("### Closed-loop architecture")
    stages = st.columns([1, 1, 1, 1])
    copy = [
        ("01 · IDENTIFY", "Threat compiler", "Curated intelligence becomes a machine-readable scenario DSL across agentic intent abuse, APP scams, card testing, fake merchants and post-transaction fraud."),
        ("02 · GENERATE", "Payment digital twin", "A synthetic customer–device–merchant–beneficiary world rolls out 5–20 linked events. The fidelity firewall rejects impossible campaigns."),
        ("03 · ADAPT", "Contextual-bandit red team", "Shared LinUCB sees black-box outcomes and learns a complete campaign configuration under a fixed query and resource budget."),
        ("04 · DEFEND", "Decision and hardening", "Boosted risk + anomaly + relationship and intent signals choose approve, step-up, hold or decline; successful evasions train V1."),
    ]
    for column, (number, title, body) in zip(stages, copy):
        column.markdown(f'<div class="stage"><b>{number}</b><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="proof"><b>The falsifiable proof:</b> learned attacker beats equal-budget baselines; V1 then reduces approved fraud from a fresh attacker without increasing legitimate false positives.</div>', unsafe_allow_html=True)

elif page == "Attack atlas":
    st.markdown("### Emerging GenAI-powered payment attack atlas")
    st.caption("Safe, abstract hypotheses—grounded for simulation, not operational attack instructions.")
    selected = st.selectbox("Inspect a scenario", [item["family"] for item in atlas], format_func=lambda value: value.replace("_", " ").title())
    card = next(item for item in atlas if item["family"] == selected)
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader(card["title"])
        st.write(card["genai_enabler"])
        st.markdown(f"**Objective:** {card['objective']}")
        st.markdown(f"**Channel / rail:** {card['channel']} · {card['rail']}")
        st.markdown("**Executable variants:** " + " · ".join(card["variants"]))
        st.markdown("**Defensive controls:** " + " · ".join(card["mitigations"]))
    with right:
        sequence = pd.DataFrame({"step": range(1, len(card["event_sequence"]) + 1), "event": card["event_sequence"]})
        fig = px.line(sequence, x="step", y=[1] * len(sequence), text="event", markers=True, title="Stateful campaign sequence")
        fig.update_yaxes(visible=False)
        fig.update_traces(line_color="#e45a21", marker_size=14, textposition="top center")
        fig.update_layout(height=280, margin={"l": 15, "r": 15, "t": 50, "b": 25}, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    table = pd.DataFrame(atlas)[["family", "channel", "rail", "novelty", "base_risk"]]
    st.dataframe(table, use_container_width=True, hide_index=True)

elif page == "Red-team arena":
    st.markdown("### Equal-budget attacker benchmark")
    st.caption("Same frozen V0 defender, action space, campaign budget and hard fidelity gate.")
    aggregate_frame = (
        attacks.groupby("strategy", as_index=False)
        .agg(mean_reward=("reward", "mean"), approved_value=("approved_value", "sum"), detection_rate=("detection_rate", "mean"), valid_rate=("valid", "mean"))
    )
    left, right = st.columns(2)
    with left:
        fig = px.bar(aggregate_frame, x="strategy", y="mean_reward", color="strategy", title="Net campaign reward", color_discrete_map={"contextual_bandit":"#e45a21","random":"#7b8da1","rule_mutation":"#236baa"})
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        sorted_runs = attacks.sort_values(["strategy", "iteration"])
        sorted_runs["cumulative_reward"] = sorted_runs.groupby("strategy")["reward"].cumsum()
        fig = px.line(sorted_runs, x="iteration", y="cumulative_reward", color="strategy", title="Learning over the campaign budget", color_discrete_map={"contextual_bandit":"#e45a21","random":"#7b8da1","rule_mutation":"#236baa"})
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)
    if aggregate:
        st.info(f"Across {len(seeds)} seeds, the bandit beats random in {aggregate['bandit_win_rate_vs_random']:.0%} of runs; mean reward {aggregate['contextual_bandit_reward']['mean']:.3f} ± {aggregate['contextual_bandit_reward']['std']:.3f}.")
    st.dataframe(aggregate_frame.style.format({"mean_reward":"{:.3f}","approved_value":"{:,.0f}","detection_rate":"{:.1%}","valid_rate":"{:.1%}"}), use_container_width=True, hide_index=True)

elif page == "Defence hardening":
    st.markdown("### V0 → adversarial examples → V1")
    cols = st.columns(3)
    cols[0].metric("Held-out ROC-AUC", f"{defence['v1_held_out']['roc_auc']:.3f}", f"+{defence['v1_held_out']['roc_auc']-defence['v0_held_out']['roc_auc']:.3f}")
    cols[1].metric("Held-out recall", f"{defence['v1_held_out']['recall']:.1%}", f"+{defence['v1_held_out']['recall']-defence['v0_held_out']['recall']:.1%}")
    cols[2].metric("Fresh approved fraud", f"{defence['fresh_attacker_approved_value_v1']:,.0f}", f"-{defence['fresh_attacker_value_reduction']:.1%}")
    family_plot = family.copy()
    family_plot["attack_family"] = family_plot["attack_family"].str.replace("_", " ").str.title()
    fig = px.bar(family_plot, x="attack_family", y="recall", color="defender", barmode="group", title="Recall on attack families never shown to V0", color_discrete_map={"V0":"#7b8da1","V1":"#e45a21"})
    fig.update_yaxes(tickformat=".0%", range=[0, 1.05])
    fig.update_layout(height=420, xaxis_title="", yaxis_title="Recall")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("V1 is challenged with a fresh attacker and a newly sampled action space; results are not replayed training campaigns.")

else:
    st.markdown("### Evidence, fidelity and governance")
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### What is measured")
        st.write("• Campaign-disjoint and temporal train/validation/test splits")
        st.write("• Four attack families held out entirely from V0 training")
        st.write("• Equal-budget random and rule-mutation red-team baselines")
        st.write("• Five deterministic seeds with mean, spread and win rate")
        st.write("• Marginal, temporal, velocity, relationship and downstream-utility evidence")
        st.write("• Approve / step-up / hold / decline operational decisions")
    with right:
        fidelity = summary["fidelity"]
        display = pd.DataFrame({"check": list(fidelity), "distance": list(fidelity.values())})
        fig = px.bar(display, x="distance", y="check", orientation="h", title="Distribution distance diagnostics (lower is closer)", color_discrete_sequence=["#236baa"])
        fig.update_layout(height=330, yaxis_title="", xaxis_title="Distance")
        st.plotly_chart(fig, use_container_width=True)
    st.warning("These distances compare attack traffic with legitimate traffic and are diagnostics—not a claim that fraud should be statistically identical to genuine payments. The hard gate separately enforces schema, range, sequence and relationship validity.")
    st.markdown("#### Published protocol anchors")
    st.markdown("[FRAUD-RLA](https://arxiv.org/abs/2502.02290) · [Adyen contextual bandits](https://arxiv.org/abs/2412.00569) · [Behavioural fidelity benchmark](https://arxiv.org/abs/2604.13125) · [Mastercard Decision Intelligence Pro](https://www.mastercard.com/news/press/2024/february/mastercard-supercharges-consumer-protection-with-gen-ai)")
    st.markdown("#### Live reproducibility")
    if st.button("Run a fresh quick benchmark", type="primary"):
        with st.status("Running simulator, red team, hardening and held-out evaluation…", expanded=True) as status:
            command = [sys.executable, str(ROOT / "experiments" / "run_benchmark.py"), "--quick", "--output", str(ROOT / "artifacts" / "runs" / "ui-latest")]
            try:
                completed = subprocess.run(
                    command,
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=240,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                status.update(label="Benchmark timed out safely", state="error")
                st.error("The quick benchmark exceeded 240 seconds. The dashboard is still usable; run it from the command line on a faster machine if needed.")
            except OSError as exc:
                status.update(label="Benchmark could not start", state="error")
                st.error(f"The benchmark process could not be started: {exc}")
            else:
                if completed.returncode == 0:
                    status.update(label="Fresh benchmark complete", state="complete")
                    st.code(completed.stdout)
                else:
                    status.update(label="Benchmark failed", state="error")
                    st.code(completed.stderr or completed.stdout)
