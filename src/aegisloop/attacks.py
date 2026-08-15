from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace

import numpy as np


@dataclass(frozen=True, slots=True)
class AttackCard:
    """A safe, abstract fraud hypothesis used by the synthetic simulator."""

    family: str
    title: str
    variants: tuple[str, ...]
    channel: str
    rail: str
    genai_enabler: str
    objective: str
    event_sequence: tuple[str, ...]
    amount_range: tuple[float, float]
    event_range: tuple[int, int]
    base_risk: float
    device_reuse: float
    beneficiary_reuse: float
    merchant_risk: float
    velocity: float
    novelty: float
    mitigations: tuple[str, ...]

    def to_dict(self) -> dict:
        result = asdict(self)
        result["event_sequence"] = list(self.event_sequence)
        result["mitigations"] = list(self.mitigations)
        return result


@dataclass(frozen=True, slots=True)
class CampaignAction:
    family: str
    amount_scale: float = 1.0
    timing_scale: float = 1.0
    device_reuse: float = 0.5
    beneficiary_reuse: float = 0.5
    merchant_risk: float = 0.5
    auth_friction: float = 0.5
    evidence_quality: float = 0.5

    @property
    def action_id(self) -> str:
        values = (
            self.family,
            round(self.amount_scale, 2),
            round(self.timing_scale, 2),
            round(self.device_reuse, 2),
            round(self.beneficiary_reuse, 2),
            round(self.merchant_risk, 2),
            round(self.auth_friction, 2),
            round(self.evidence_quality, 2),
        )
        return "|".join(map(str, values))


ATTACK_ATLAS: tuple[AttackCard, ...] = (
    AttackCard(
        "adaptive_card_testing",
        "Adaptive card-testing swarm",
        ("micro-authorisation probes", "merchant-hop testing", "low-and-slow retries", "wallet-token validation"),
        "card-not-present",
        "card",
        "Generative agents vary low-value purchase semantics and timing at scale.",
        "Validate credentials before monetisation.",
        ("probe", "cooldown", "retry", "monetise"),
        (1.0, 85.0),
        (6, 18),
        0.67,
        0.28,
        0.08,
        0.47,
        0.88,
        0.48,
        ("velocity controls", "merchant-card graph risk", "step-up authentication"),
    ),
    AttackCard(
        "ai_app_scam_mule",
        "AI-personalised APP scam into mule network",
        ("investment grooming", "romance-to-payment", "impersonation urgency", "multilingual supplier scam"),
        "social engineering",
        "account-to-account",
        "LLMs personalise pretexts and sustain multilingual conversations.",
        "Induce an authorised transfer into a mule network.",
        ("trust_build", "new_payee", "small_test", "escalated_transfer"),
        (80.0, 4200.0),
        (5, 10),
        0.74,
        0.22,
        0.76,
        0.36,
        0.52,
        0.66,
        ("confirmation of payee", "beneficiary graph risk", "behavioural step-up"),
    ),
    AttackCard(
        "deepfake_account_takeover",
        "Deepfake-assisted account takeover",
        ("voice recovery", "video liveness challenge", "synthetic document recovery", "call-centre social engineering"),
        "remote authentication",
        "card and account",
        "Synthetic voice/video and generated documents challenge remote identity checks.",
        "Take control, add a payee, then move value.",
        ("recovery", "device_bind", "credential_change", "transfer"),
        (120.0, 6200.0),
        (5, 9),
        0.82,
        0.68,
        0.48,
        0.45,
        0.63,
        0.72,
        ("liveness", "device binding", "post-recovery cooling period"),
    ),
    AttackCard(
        "synthetic_identity_bustout",
        "Synthetic-identity credit bust-out",
        ("thin-file persona", "credit-line cultivation", "coordinated family identities", "AI-generated business identity"),
        "credit lifecycle",
        "card",
        "GenAI produces coherent identity artefacts and longitudinal personas.",
        "Build credibility, expand exposure, then exhaust credit.",
        ("onboard", "normal_spend", "limit_growth", "bustout"),
        (20.0, 8500.0),
        (10, 20),
        0.79,
        0.18,
        0.12,
        0.51,
        0.44,
        0.83,
        ("identity-link analysis", "credit trajectory monitoring", "exposure throttling"),
    ),
    AttackCard(
        "agentic_intent_hijack",
        "Agentic-commerce intent hijack",
        ("catalogue prompt injection", "delegation-scope confusion", "merchant substitution", "checkout intent drift"),
        "AI agent checkout",
        "card and token",
        "Prompt injection or delegated-authority confusion alters an agent's payment intent.",
        "Redirect an otherwise legitimate autonomous purchase.",
        ("delegation", "catalogue_poison", "intent_drift", "agent_checkout"),
        (25.0, 2400.0),
        (5, 9),
        0.76,
        0.31,
        0.10,
        0.70,
        0.49,
        0.94,
        ("verifiable intent", "merchant allow-list", "agent action trace"),
    ),
    AttackCard(
        "fake_merchant_collusion",
        "GenAI fake-merchant collusion ring",
        ("generated storefront ring", "transaction laundering", "subscription trap", "collusive refund cycling"),
        "merchant ecosystem",
        "card",
        "Generated storefronts, product content and support histories create plausible merchants.",
        "Launder fraudulent payments through related merchants.",
        ("merchant_onboard", "organic_cover", "collusive_sales", "cashout"),
        (15.0, 3100.0),
        (8, 18),
        0.73,
        0.24,
        0.18,
        0.91,
        0.39,
        0.87,
        ("merchant graph intelligence", "portfolio monitoring", "settlement holds"),
    ),
    AttackCard(
        "qr_invoice_redirection",
        "AI-crafted invoice and QR redirection",
        ("supplier bank-change", "dynamic QR replacement", "payment-link impersonation", "cross-border invoice diversion"),
        "business email compromise",
        "account-to-account",
        "GenAI mimics supplier language and generates credible invoices and QR artefacts.",
        "Redirect a business payment to a new beneficiary.",
        ("supplier_mimic", "invoice_issue", "beneficiary_change", "payment"),
        (240.0, 9800.0),
        (5, 8),
        0.78,
        0.16,
        0.61,
        0.32,
        0.41,
        0.80,
        ("beneficiary-change verification", "invoice consistency", "payee reputation"),
    ),
    AttackCard(
        "synthetic_evidence_refund",
        "Synthetic-evidence refund abuse",
        ("generated damage evidence", "fake non-delivery narrative", "synthetic merchant correspondence", "coordinated friendly fraud"),
        "post-transaction",
        "card dispute",
        "Image and text generators create coherent but false fulfilment or damage evidence.",
        "Obtain a refund or chargeback after legitimate fulfilment.",
        ("purchase", "fulfilment", "evidence_forge", "refund_claim"),
        (20.0, 1800.0),
        (5, 9),
        0.64,
        0.12,
        0.08,
        0.43,
        0.28,
        0.77,
        ("evidence provenance", "claim-behaviour graph", "merchant fulfilment signals"),
    ),
)


def atlas_by_family() -> dict[str, AttackCard]:
    return {card.family: card for card in ATTACK_ATLAS}


def attack_families() -> list[str]:
    return [card.family for card in ATTACK_ATLAS]


def sample_action(card: AttackCard, rng: np.random.Generator) -> CampaignAction:
    """Sample safe simulator parameters around a grounded attack hypothesis."""

    def clipped(center: float, spread: float = 0.18) -> float:
        return float(np.clip(rng.normal(center, spread), 0.05, 0.98))

    return CampaignAction(
        family=card.family,
        amount_scale=float(np.clip(rng.lognormal(0.0, 0.34), 0.45, 2.2)),
        timing_scale=float(np.clip(rng.lognormal(0.0, 0.30), 0.45, 2.1)),
        device_reuse=clipped(card.device_reuse),
        beneficiary_reuse=clipped(card.beneficiary_reuse),
        merchant_risk=clipped(card.merchant_risk),
        auth_friction=clipped(card.base_risk, 0.16),
        evidence_quality=clipped(0.45 + card.novelty * 0.35, 0.12),
    )


def mutate_action(action: CampaignAction, rng: np.random.Generator, scale: float = 0.12) -> CampaignAction:
    fields = {}
    for name in (
        "device_reuse",
        "beneficiary_reuse",
        "merchant_risk",
        "auth_friction",
        "evidence_quality",
    ):
        fields[name] = float(np.clip(getattr(action, name) + rng.normal(0, scale), 0.03, 0.99))
    fields["amount_scale"] = float(np.clip(action.amount_scale * rng.lognormal(0, scale), 0.4, 2.3))
    fields["timing_scale"] = float(np.clip(action.timing_scale * rng.lognormal(0, scale), 0.4, 2.3))
    return replace(action, **fields)


def scenario_dsl(cards: Iterable[AttackCard] = ATTACK_ATLAS) -> list[dict]:
    """Export the attack atlas as machine-readable scenario descriptions."""

    return [card.to_dict() for card in cards]
