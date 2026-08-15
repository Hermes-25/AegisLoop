from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

import numpy as np
import pandas as pd

from aegisloop.attacks import (
    CampaignAction,
    atlas_by_family,
    attack_families,
    mutate_action,
    sample_action,
)
from aegisloop.config import RedTeamConfig
from aegisloop.defender import AegisDefender
from aegisloop.fidelity import FidelityGate
from aegisloop.simulator import PaymentDigitalTwin


@dataclass(frozen=True, slots=True)
class CampaignResult:
    iteration: int
    strategy: str
    action_id: str
    family: str
    reward: float
    fidelity: float
    valid: bool
    approved_value: float
    detection_rate: float
    mean_risk_score: float
    event_count: int
    novel_evasion: bool
    value_term: float
    evasion_term: float
    detection_cost_term: float
    resource_cost_term: float
    novelty_term: float
    validity_term: float
    pre_fidelity_reward: float

    def to_dict(self) -> dict:
        return asdict(self)


class Strategy(Protocol):
    name: str

    def select(self, context: np.ndarray, rng: np.random.Generator) -> CampaignAction: ...

    def update(self, context: np.ndarray, action: CampaignAction, reward: float) -> None: ...


def build_action_space(
    seed: int,
    variants_per_family: int = 14,
    families: list[str] | None = None,
) -> list[CampaignAction]:
    rng = np.random.default_rng(seed)
    atlas = atlas_by_family()
    actions = []
    selected_families = families or attack_families()
    for family in selected_families:
        for _ in range(variants_per_family):
            actions.append(sample_action(atlas[family], rng))
    return actions


class RandomStrategy:
    name = "random"

    def __init__(self, actions: list[CampaignAction]):
        self.actions = actions

    def select(self, context: np.ndarray, rng: np.random.Generator) -> CampaignAction:
        return self.actions[int(rng.integers(0, len(self.actions)))]

    def update(self, context: np.ndarray, action: CampaignAction, reward: float) -> None:
        return None


class RuleMutationStrategy:
    name = "rule_mutation"

    def __init__(self, actions: list[CampaignAction]):
        self.actions = actions
        self.best = actions[0]
        self.best_reward = -np.inf

    def select(self, context: np.ndarray, rng: np.random.Generator) -> CampaignAction:
        if self.best_reward == -np.inf or rng.random() < 0.28:
            return self.actions[int(rng.integers(0, len(self.actions)))]
        return mutate_action(self.best, rng, scale=0.10)

    def update(self, context: np.ndarray, action: CampaignAction, reward: float) -> None:
        if reward > self.best_reward:
            self.best, self.best_reward = action, reward


class LinUCBStrategy:
    """Shared LinUCB that generalises across related campaign configurations."""

    def __init__(
        self,
        actions: list[CampaignAction],
        context_dim: int,
        alpha: float = 1.15,
        name: str = "contextual_bandit",
    ):
        self.actions = actions
        self.name = name
        self.alpha = float(alpha)
        self.context_dim = int(context_dim)
        self.families = attack_families()
        self.feature_dim = context_dim + len(self.families) + 7 + 7
        self.A = np.eye(self.feature_dim)
        self.b = np.zeros(self.feature_dim)

    def _features(self, context: np.ndarray, action: CampaignAction) -> np.ndarray:
        family = np.zeros(len(self.families), dtype=float)
        family[self.families.index(action.family)] = 1.0
        parameters = np.array(
            [
                np.log(max(action.amount_scale, 1e-6)),
                np.log(max(action.timing_scale, 1e-6)),
                action.device_reuse,
                action.beneficiary_reuse,
                action.merchant_risk,
                action.auth_friction,
                action.evidence_quality,
            ],
            dtype=float,
        )
        interactions = parameters * float(context[1])
        return np.concatenate([context, family, parameters, interactions])

    def select(self, context: np.ndarray, rng: np.random.Generator) -> CampaignAction:
        inverse = np.linalg.inv(self.A)
        theta = inverse @ self.b
        scores = np.empty(len(self.actions))
        for idx, action in enumerate(self.actions):
            features = self._features(context, action)
            exploitation = theta @ features
            uncertainty = self.alpha * np.sqrt(features @ inverse @ features)
            scores[idx] = exploitation + uncertainty + rng.normal(0, 1e-9)
        return self.actions[int(np.argmax(scores))]

    def update(self, context: np.ndarray, action: CampaignAction, reward: float) -> None:
        features = self._features(context, action)
        self.A += np.outer(features, features)
        self.b += reward * features


class RedTeamArena:
    """Frozen-defender, black-box campaign evaluation arena."""

    def __init__(
        self,
        twin: PaymentDigitalTwin,
        defender: AegisDefender,
        gate: FidelityGate,
        config: RedTeamConfig,
        seed: int,
    ):
        self.twin = twin
        self.defender = defender
        self.gate = gate
        self.config = config
        self.seed = int(seed)

    @staticmethod
    def context(history: list[CampaignResult], family: str) -> np.ndarray:
        recent = history[-8:]
        family_recent = [item for item in recent if item.family == family]
        return np.array(
            [
                1.0,
                np.mean([item.detection_rate for item in recent]) if recent else 0.5,
                np.mean([item.fidelity for item in recent]) if recent else 0.8,
                np.mean([item.reward for item in recent]) / 5000 if recent else 0.0,
                np.mean([item.detection_rate for item in family_recent]) if family_recent else 0.5,
                len({item.family for item in recent}) / max(len(attack_families()), 1),
            ],
            dtype=float,
        )

    def run(self, strategy: Strategy, budget: int | None = None) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
        budget = int(budget or self.config.campaign_budget)
        rng = np.random.default_rng(self.seed)
        history: list[CampaignResult] = []
        campaigns: list[pd.DataFrame] = []
        seen_successes: set[str] = set()
        for iteration in range(budget):
            base_context = self.context(history, "unknown")
            action = strategy.select(base_context, rng)
            context = self.context(history, action.family)
            campaign = self.twin.generate_campaign(
                action,
                n_events=self.config.events_per_evaluation,
                seed=int(rng.integers(0, 2**31 - 1)),
            )
            card = self.twin.cards[action.family]
            fidelity = self.gate.evaluate(campaign, action, card)
            if not fidelity.valid:
                reward = self.config.validity_penalty
                approved_value = 0.0
                detection_rate = 1.0
                mean_score = 1.0
                novel_evasion = False
                value_term = 0.0
                evasion_term = 0.0
                detection_cost_term = 0.0
                resource_cost_term = 0.0
                novelty_term = 0.0
                validity_term = float(self.config.validity_penalty)
                pre_fidelity_reward = float(self.config.validity_penalty)
            else:
                scores = self.defender.score(campaign)
                detected = self.defender.detected_mask(campaign)
                approved_value = float(campaign.loc[~detected, "amount"].sum())
                detection_rate = float(detected.mean())
                mean_score = float(scores.mean())
                success_key = f"{action.family}:{round(action.amount_scale, 1)}:{round(action.timing_scale, 1)}:{round(action.device_reuse, 1)}"
                novel_evasion = approved_value > 0 and success_key not in seen_successes
                if novel_evasion:
                    seen_successes.add(success_key)
                evasion_rate = 1 - detection_rate
                value_term = approved_value / self.config.approved_value_scale
                evasion_term = self.config.evasion_reward_weight * evasion_rate
                detection_cost_term = -self.config.detection_cost_rate * detection_rate
                resource_cost_term = -self.config.resource_cost_per_event * len(campaign) / 1000
                novelty_term = self.config.novelty_bonus if novel_evasion else 0.0
                validity_term = 0.0
                pre_fidelity_reward = (
                    value_term
                    + evasion_term
                    + detection_cost_term
                    + resource_cost_term
                    + novelty_term
                )
                reward = pre_fidelity_reward * fidelity.score
                campaigns.append(
                    campaign.assign(
                        red_team_reward=reward,
                        red_team_strategy=strategy.name,
                        red_team_approved_value=approved_value,
                    )
                )
            result = CampaignResult(
                iteration=iteration,
                strategy=strategy.name,
                action_id=action.action_id,
                family=action.family,
                reward=float(reward),
                fidelity=float(fidelity.score),
                valid=bool(fidelity.valid),
                approved_value=float(approved_value),
                detection_rate=float(detection_rate),
                mean_risk_score=float(mean_score),
                event_count=len(campaign),
                novel_evasion=bool(novel_evasion),
                value_term=float(value_term),
                evasion_term=float(evasion_term),
                detection_cost_term=float(detection_cost_term),
                resource_cost_term=float(resource_cost_term),
                novelty_term=float(novelty_term),
                validity_term=float(validity_term),
                pre_fidelity_reward=float(pre_fidelity_reward),
            )
            history.append(result)
            strategy.update(context, action, float(reward))
        return pd.DataFrame([item.to_dict() for item in history]), campaigns
