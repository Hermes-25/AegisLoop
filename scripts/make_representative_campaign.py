from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegisloop.attacks import atlas_by_family, sample_action
from aegisloop.config import load_config
from aegisloop.fidelity import FidelityGate
from aegisloop.simulator import PaymentDigitalTwin


ARTIFACT_VERSION = "1.0.0"
FAMILY = "agentic_intent_hijack"
WORLD_SEED = 20260812
ACTION_SEED = 20260820
CAMPAIGN_SEED = 20260821


def _json_value(value: object) -> object:
    if isinstance(value, pd.Timestamp):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, np.datetime64):
        return pd.Timestamp(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if pd.isna(value):
        return None
    return value


def build_artifact() -> dict:
    config = load_config(ROOT / "config" / "default.yaml")
    twin = PaymentDigitalTwin(config.simulation, seed=WORLD_SEED)
    legitimate_reference = twin.generate_legitimate(config.simulation.legitimate_events)

    card = atlas_by_family()[FAMILY]
    action = sample_action(card, np.random.default_rng(ACTION_SEED))
    campaign = twin.generate_campaign(
        action,
        n_events=card.event_range[1],
        seed=CAMPAIGN_SEED,
    ).sort_values("timestamp").reset_index(drop=True)
    fidelity = FidelityGate(legitimate_reference).evaluate(campaign, action, card)
    if not fidelity.valid:
        raise RuntimeError(
            "The fixed representative rollout failed the fidelity firewall: "
            + "; ".join(fidelity.reasons)
        )

    sequence = list(card.event_sequence)
    events: list[dict] = []
    for index, row in campaign.iterrows():
        sequence_index = min(int(index * len(sequence) / len(campaign)), len(sequence) - 1)
        event = {key: _json_value(value) for key, value in row.to_dict().items()}
        event["sequence_stage"] = sequence[sequence_index]
        event["rollout_index"] = index + 1
        events.append(event)

    timestamps = pd.to_datetime(campaign["timestamp"], utc=True)
    return {
        "artifact_version": ARTIFACT_VERSION,
        "artifact_type": "representative_campaign_rollout",
        "evidence_boundary": (
            "A deterministic synthetic rollout from the hand-coded, stateful, entity-linked "
            "AegisLoop simulator; it is not real cardholder data or production performance evidence."
        ),
        "selection_note": (
            "One illustrative case study selected to demonstrate simulator state; it does not rank "
            "this attack family above the other atlas archetypes."
        ),
        "generator": {
            "implementation": "aegisloop.simulator.PaymentDigitalTwin",
            "simulator_design": "hand-coded_stateful_entity_linked",
            "config_path": "config/default.yaml",
            "world_seed": WORLD_SEED,
            "action_seed": ACTION_SEED,
            "campaign_seed": CAMPAIGN_SEED,
        },
        "attack_card": card.to_dict(),
        "action": asdict(action),
        "fidelity": asdict(fidelity),
        "summary": {
            "campaign_id": str(campaign["campaign_id"].iloc[0]),
            "event_count": int(len(campaign)),
            "start_timestamp": timestamps.min().isoformat().replace("+00:00", "Z"),
            "end_timestamp": timestamps.max().isoformat().replace("+00:00", "Z"),
            "duration_minutes": float((timestamps.max() - timestamps.min()).total_seconds() / 60),
            "unique_customers": int(campaign["customer_id"].nunique()),
            "unique_devices": int(campaign["device_id"].nunique()),
            "unique_merchants": int(campaign["merchant_id"].nunique()),
            "unique_beneficiaries": int(campaign["beneficiary_id"].nunique()),
            "maximum_velocity_10m": int(campaign["velocity_10m"].max()),
            "maximum_velocity_1h": int(campaign["velocity_1h"].max()),
            "maximum_graph_shared_entities": int(campaign["graph_shared_entities"].max()),
        },
        "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the versioned representative campaign artifact.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "precomputed" / "representative_campaign.json",
    )
    args = parser.parse_args()
    artifact = build_artifact()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.output} with {artifact['summary']['event_count']} events; "
        f"fidelity={artifact['fidelity']['score']:.6f}"
    )


if __name__ == "__main__":
    main()
