from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from aegisloop.attacks import CampaignAction, atlas_by_family
from aegisloop.config import SimulationConfig

EVENT_COLUMNS = [
    "event_id",
    "campaign_id",
    "timestamp",
    "customer_id",
    "device_id",
    "merchant_id",
    "beneficiary_id",
    "channel",
    "rail",
    "amount",
    "customer_age_days",
    "account_tenure_days",
    "hour_sin",
    "hour_cos",
    "is_cross_border",
    "device_age_days",
    "device_trust",
    "device_reuse_24h",
    "beneficiary_age_days",
    "beneficiary_reuse_24h",
    "merchant_risk",
    "merchant_age_days",
    "velocity_10m",
    "velocity_1h",
    "amount_to_customer_median",
    "auth_strength",
    "auth_changed_recently",
    "intent_match",
    "evidence_provenance",
    "graph_degree",
    "graph_shared_entities",
    "is_fraud",
    "attack_family",
    "campaign_step",
]


@dataclass(slots=True)
class SyntheticWorld:
    customers: pd.DataFrame
    merchants: pd.DataFrame
    devices: pd.DataFrame
    beneficiaries: pd.DataFrame


class PaymentDigitalTwin:
    """A deterministic, synthetic-only, multi-entity payment environment."""

    def __init__(self, config: SimulationConfig, seed: int = 20260812):
        self.config = config
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.world = self._make_world()
        self.cards = atlas_by_family()
        self._event_counter = 0
        self._campaign_counter = 0
        self.start_time = datetime(2026, 1, 1, tzinfo=UTC)

    def _make_world(self) -> SyntheticWorld:
        rng = self.rng
        customers = pd.DataFrame(
            {
                "customer_id": [f"C{i:06d}" for i in range(self.config.customers)],
                "account_tenure_days": rng.integers(20, 4200, self.config.customers),
                "customer_age_days": rng.integers(18 * 365, 83 * 365, self.config.customers),
                "median_amount": np.clip(rng.lognormal(3.45, 0.85, self.config.customers), 4, 850),
                "cross_border_rate": rng.beta(1.2, 13.0, self.config.customers),
                "digital_confidence": rng.beta(6.2, 2.0, self.config.customers),
                "preferred_hour": rng.normal(15, 4.5, self.config.customers) % 24,
            }
        )
        merchants = pd.DataFrame(
            {
                "merchant_id": [f"M{i:05d}" for i in range(self.config.merchants)],
                "merchant_risk": rng.beta(1.4, 8.5, self.config.merchants),
                "merchant_age_days": rng.integers(7, 5200, self.config.merchants),
                "cross_border": rng.binomial(1, 0.16, self.config.merchants),
                "base_ticket": np.clip(rng.lognormal(3.7, 1.0, self.config.merchants), 3, 1600),
            }
        )
        devices = pd.DataFrame(
            {
                "device_id": [f"D{i:06d}" for i in range(self.config.devices)],
                "device_age_days": rng.integers(0, 2100, self.config.devices),
                "device_trust": rng.beta(7.0, 1.8, self.config.devices),
            }
        )
        beneficiaries = pd.DataFrame(
            {
                "beneficiary_id": [f"B{i:06d}" for i in range(self.config.beneficiaries)],
                "beneficiary_age_days": rng.integers(1, 3300, self.config.beneficiaries),
                "beneficiary_risk": rng.beta(1.3, 10.0, self.config.beneficiaries),
            }
        )
        return SyntheticWorld(customers, merchants, devices, beneficiaries)

    def _new_event_id(self) -> str:
        self._event_counter += 1
        return f"E{self._event_counter:09d}"

    def _new_campaign_id(self, family: str) -> str:
        self._campaign_counter += 1
        return f"{family[:4].upper()}-{self._campaign_counter:06d}"

    def generate_legitimate(self, n_events: int | None = None) -> pd.DataFrame:
        n = int(n_events or self.config.legitimate_events)
        rng, world = self.rng, self.world
        customer_idx = rng.integers(0, len(world.customers), n)
        merchant_idx = rng.integers(0, len(world.merchants), n)
        device_idx = np.mod(customer_idx + rng.integers(-2, 3, n), len(world.devices))
        beneficiary_idx = rng.integers(0, len(world.beneficiaries), n)
        customers = world.customers.iloc[customer_idx].reset_index(drop=True)
        merchants = world.merchants.iloc[merchant_idx].reset_index(drop=True)
        devices = world.devices.iloc[device_idx].reset_index(drop=True)
        beneficiaries = world.beneficiaries.iloc[beneficiary_idx].reset_index(drop=True)
        hours = (customers["preferred_hour"].to_numpy() + rng.normal(0, 3.4, n)) % 24
        gaps = rng.exponential(26, n)
        timestamps = [self.start_time + timedelta(minutes=float(value)) for value in np.cumsum(gaps)]
        expected = 0.62 * customers["median_amount"].to_numpy() + 0.38 * merchants["base_ticket"].to_numpy()
        amounts = np.clip(expected * rng.lognormal(0, 0.52, n), 0.5, 8000)
        channel = rng.choice(["ecommerce", "pos", "wallet", "a2a"], n, p=[0.37, 0.36, 0.12, 0.15])
        rail = np.where(channel == "a2a", "account-to-account", "card")
        cross = np.maximum(merchants["cross_border"].to_numpy(), rng.binomial(1, customers["cross_border_rate"].to_numpy()))
        amount_ratio = amounts / np.maximum(customers["median_amount"].to_numpy(), 1)
        data = pd.DataFrame(
            {
                "event_id": [self._new_event_id() for _ in range(n)],
                "campaign_id": "legitimate",
                "timestamp": timestamps,
                "customer_id": customers["customer_id"].to_numpy(),
                "device_id": devices["device_id"].to_numpy(),
                "merchant_id": merchants["merchant_id"].to_numpy(),
                "beneficiary_id": beneficiaries["beneficiary_id"].to_numpy(),
                "channel": channel,
                "rail": rail,
                "amount": amounts,
                "customer_age_days": customers["customer_age_days"].to_numpy(),
                "account_tenure_days": customers["account_tenure_days"].to_numpy(),
                "hour_sin": np.sin(2 * np.pi * hours / 24),
                "hour_cos": np.cos(2 * np.pi * hours / 24),
                "is_cross_border": cross,
                "device_age_days": devices["device_age_days"].to_numpy(),
                "device_trust": devices["device_trust"].to_numpy(),
                "device_reuse_24h": np.clip(rng.poisson(1.2, n), 0, 12),
                "beneficiary_age_days": beneficiaries["beneficiary_age_days"].to_numpy(),
                "beneficiary_reuse_24h": np.clip(rng.poisson(0.7, n), 0, 10),
                "merchant_risk": merchants["merchant_risk"].to_numpy(),
                "merchant_age_days": merchants["merchant_age_days"].to_numpy(),
                "velocity_10m": np.clip(rng.poisson(0.35, n), 0, 8),
                "velocity_1h": np.clip(rng.poisson(1.3, n), 0, 16),
                "amount_to_customer_median": amount_ratio,
                "auth_strength": np.clip(customers["digital_confidence"].to_numpy() + rng.normal(0, 0.1, n), 0, 1),
                "auth_changed_recently": rng.binomial(1, 0.013, n),
                "intent_match": np.clip(rng.beta(15, 1.3, n), 0, 1),
                "evidence_provenance": np.clip(rng.beta(13, 1.6, n), 0, 1),
                "graph_degree": np.clip(rng.poisson(2.0, n), 0, 18),
                "graph_shared_entities": np.clip(rng.poisson(0.22, n), 0, 8),
                "is_fraud": 0,
                "attack_family": "legitimate",
                "campaign_step": 0,
            }
        )
        return data[EVENT_COLUMNS]

    def generate_campaign(
        self,
        action: CampaignAction,
        n_events: int | None = None,
        seed: int | None = None,
    ) -> pd.DataFrame:
        card = self.cards[action.family]
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        lower, upper = card.event_range
        n = int(n_events or rng.integers(lower, upper + 1))
        n = int(np.clip(n, self.config.campaign_min_events, self.config.campaign_max_events))
        campaign_id = self._new_campaign_id(card.family)
        world = self.world
        customer = world.customers.iloc[int(rng.integers(0, len(world.customers)))]
        base_device = int(rng.integers(0, len(world.devices)))
        base_beneficiary = int(rng.integers(0, len(world.beneficiaries)))
        base_merchant = int(rng.integers(0, len(world.merchants)))
        median_amount = float(customer["median_amount"])
        low, high = card.amount_range
        campaign_start = self.start_time + timedelta(days=float(rng.uniform(120, 250)))
        rows = []

        for step in range(n):
            progress = step / max(n - 1, 1)
            repeated_device = rng.random() < action.device_reuse
            repeated_beneficiary = rng.random() < action.beneficiary_reuse
            device_idx = base_device if repeated_device else int(rng.integers(0, len(world.devices)))
            beneficiary_idx = base_beneficiary if repeated_beneficiary else int(rng.integers(0, len(world.beneficiaries)))
            merchant_idx = base_merchant if rng.random() < action.merchant_risk else int(rng.integers(0, len(world.merchants)))
            device = world.devices.iloc[device_idx]
            beneficiary = world.beneficiaries.iloc[beneficiary_idx]
            merchant = world.merchants.iloc[merchant_idx]
            base_amount = np.exp(np.log(low + 1) + progress * (np.log(high + 1) - np.log(low + 1))) - 1
            amount = float(np.clip(base_amount * action.amount_scale * rng.lognormal(0, 0.32), 0.5, 25000))
            minutes = float((step + 1) * 18 * action.timing_scale + rng.uniform(0, 10))
            timestamp = campaign_start + timedelta(minutes=minutes)
            hour = timestamp.hour + timestamp.minute / 60
            velocity = card.velocity / max(action.timing_scale, 0.25)
            intent_match = 1 - 0.72 * (card.family == "agentic_intent_hijack") * progress
            intent_match -= 0.18 * (card.family in {"ai_app_scam_mule", "qr_invoice_redirection"})
            provenance = action.evidence_quality
            if card.family != "synthetic_evidence_refund":
                provenance = 0.75 + 0.2 * action.evidence_quality
            merchant_risk = float(np.clip(0.72 * merchant["merchant_risk"] + 0.28 * action.merchant_risk, 0, 1))
            auth_strength = float(np.clip(0.68 + 0.25 * (1 - action.auth_friction) + rng.normal(0, 0.09), 0, 1))
            graph_degree = int(np.clip(1 + 6 * max(action.beneficiary_reuse, action.merchant_risk) + rng.normal(0, 1.7), 0, 18))
            shared = int(np.clip((step + 1) * max(action.device_reuse, action.beneficiary_reuse) * 0.42 + rng.normal(0, 0.7), 0, 12))
            rows.append(
                {
                    "event_id": self._new_event_id(),
                    "campaign_id": campaign_id,
                    "timestamp": timestamp,
                    "customer_id": customer["customer_id"],
                    "device_id": device["device_id"],
                    "merchant_id": merchant["merchant_id"],
                    "beneficiary_id": beneficiary["beneficiary_id"],
                    "channel": card.channel,
                    "rail": card.rail,
                    "amount": amount,
                    "customer_age_days": customer["customer_age_days"],
                    "account_tenure_days": customer["account_tenure_days"],
                    "hour_sin": np.sin(2 * np.pi * hour / 24),
                    "hour_cos": np.cos(2 * np.pi * hour / 24),
                    "is_cross_border": int(rng.random() < 0.28 + 0.36 * card.base_risk),
                    "device_age_days": max(0, int(device["device_age_days"] * (1 - 0.18 * action.device_reuse))),
                    "device_trust": float(np.clip(device["device_trust"] * (1 - 0.10 * card.base_risk) + rng.normal(0, 0.09), 0, 1)),
                    "device_reuse_24h": int(np.clip((step + 1) * action.device_reuse * 0.48 + rng.poisson(1), 0, 16)),
                    "beneficiary_age_days": max(0, int(beneficiary["beneficiary_age_days"] * (1 - 0.22 * action.beneficiary_reuse))),
                    "beneficiary_reuse_24h": int(np.clip((step + 1) * action.beneficiary_reuse * 0.52 + rng.poisson(1), 0, 16)),
                    "merchant_risk": merchant_risk,
                    "merchant_age_days": max(1, int(merchant["merchant_age_days"] * (1 - 0.24 * action.merchant_risk))),
                    "velocity_10m": int(np.clip(velocity * 1.4 + step * 0.08 + rng.poisson(0.5), 0, 12)),
                    "velocity_1h": int(np.clip(velocity * 3.1 + step * 0.18 + rng.poisson(1.3), 0, 20)),
                    "amount_to_customer_median": amount / max(median_amount, 1),
                    "auth_strength": auth_strength,
                    "auth_changed_recently": int(card.family == "deepfake_account_takeover" and progress < 0.55),
                    "intent_match": float(np.clip(intent_match + rng.normal(0, 0.05), 0, 1)),
                    "evidence_provenance": float(np.clip(provenance + rng.normal(0, 0.05), 0, 1)),
                    "graph_degree": graph_degree,
                    "graph_shared_entities": shared,
                    "is_fraud": 1,
                    "attack_family": card.family,
                    "campaign_step": 0,
                }
            )
        return pd.DataFrame(rows, columns=EVENT_COLUMNS)

    def generate_attack_set(
        self,
        families: list[str],
        campaigns_per_family: int = 35,
        seed: int | None = None,
    ) -> pd.DataFrame:
        from aegisloop.attacks import sample_action

        rng = np.random.default_rng(seed if seed is not None else self.seed + 13)
        frames = []
        for family in families:
            card = self.cards[family]
            for _ in range(campaigns_per_family):
                frames.append(self.generate_campaign(sample_action(card, rng), seed=int(rng.integers(0, 2**31 - 1))))
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=EVENT_COLUMNS)
