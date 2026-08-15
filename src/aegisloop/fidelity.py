from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import ks_2samp

from aegisloop.attacks import AttackCard, CampaignAction


@dataclass(frozen=True, slots=True)
class FidelityReport:
    valid: bool
    score: float
    schema_score: float
    range_score: float
    temporal_score: float
    graph_score: float
    behavioural_score: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "score": self.score,
            "schema_score": self.schema_score,
            "range_score": self.range_score,
            "temporal_score": self.temporal_score,
            "graph_score": self.graph_score,
            "behavioural_score": self.behavioural_score,
            "reasons": list(self.reasons),
        }


class FidelityGate:
    """Reject simulator exploits before the red-team reward is calculated."""

    def __init__(self, reference_legitimate: pd.DataFrame):
        self.reference = reference_legitimate.copy()

    def evaluate(self, campaign: pd.DataFrame, action: CampaignAction, card: AttackCard) -> FidelityReport:
        reasons: list[str] = []
        required = {
            "timestamp",
            "amount",
            "customer_id",
            "device_id",
            "merchant_id",
            "velocity_1h",
            "graph_degree",
        }
        schema_score = len(required.intersection(campaign.columns)) / len(required)
        if campaign.empty or schema_score < 1:
            return FidelityReport(False, 0.0, schema_score, 0.0, 0.0, 0.0, 0.0, ("missing schema",))

        finite = np.isfinite(campaign.select_dtypes(include=[np.number]).to_numpy()).all()
        sane_amounts = bool((campaign["amount"] > 0).all() and (campaign["amount"] <= 25000).all())
        event_count_ok = card.event_range[0] <= len(campaign) <= card.event_range[1]
        range_score = np.mean([finite, sane_amounts, event_count_ok])
        if not finite:
            reasons.append("non-finite numeric value")
        if not sane_amounts:
            reasons.append("amount outside simulator boundary")
        if not event_count_ok:
            reasons.append("campaign length outside attack card")

        times = pd.to_datetime(campaign["timestamp"], utc=True).sort_values()
        deltas = times.diff().dropna().dt.total_seconds().to_numpy()
        chronological = len(deltas) == 0 or bool((deltas >= 0).all())
        nondegenerate = len(deltas) == 0 or bool(np.std(deltas) > 0.5)
        plausible_gap = len(deltas) == 0 or bool((deltas <= 72 * 3600).all())
        temporal_score = np.mean([chronological, nondegenerate, plausible_gap])
        if not chronological:
            reasons.append("non-chronological events")
        if not nondegenerate:
            reasons.append("degenerate timing pattern")

        unique_entities = np.mean(
            [
                campaign["device_id"].nunique() / len(campaign),
                campaign["merchant_id"].nunique() / len(campaign),
                campaign["beneficiary_id"].nunique() / len(campaign),
            ]
        )
        graph_score = float(np.clip(1 - abs(unique_entities - (0.72 - 0.34 * max(action.device_reuse, action.beneficiary_reuse))), 0, 1))

        amount_ratio = campaign["amount_to_customer_median"].to_numpy()
        tail_ok = np.mean((amount_ratio > 0.03) & (amount_ratio < 180))
        velocity_ok = np.mean((campaign["velocity_1h"] >= 0) & (campaign["velocity_1h"] <= 32))
        behavioural_score = float(np.mean([tail_ok, velocity_ok]))

        score = float(0.18 * schema_score + 0.24 * range_score + 0.22 * temporal_score + 0.18 * graph_score + 0.18 * behavioural_score)
        valid = bool(score >= 0.78 and schema_score == 1 and range_score >= 2 / 3 and temporal_score >= 2 / 3)
        if not valid and not reasons:
            reasons.append("composite fidelity below threshold")
        return FidelityReport(valid, score, schema_score, range_score, temporal_score, graph_score, behavioural_score, tuple(reasons))

    def distribution_report(self, synthetic: pd.DataFrame) -> dict[str, float]:
        """Distributional checks used for evidence, not as a permissive reward shortcut."""

        reference = self.reference
        numeric = ["amount", "velocity_1h", "device_trust", "merchant_risk", "graph_degree"]
        ks = {
            f"ks_{column}": float(ks_2samp(reference[column], synthetic[column]).statistic)
            for column in numeric
            if column in synthetic and not synthetic.empty
        }
        ref_hist, bins = np.histogram(np.log1p(reference["amount"]), bins=24, density=True)
        syn_hist, _ = np.histogram(np.log1p(synthetic["amount"]), bins=bins, density=True)
        ref_hist = np.clip(ref_hist, 1e-8, None)
        syn_hist = np.clip(syn_hist, 1e-8, None)
        js = float(jensenshannon(ref_hist / ref_hist.sum(), syn_hist / syn_hist.sum()) ** 2)
        return {**ks, "js_log_amount": js}

