from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class SimulationConfig:
    customers: int = 2400
    merchants: int = 620
    devices: int = 2900
    beneficiaries: int = 1300
    legitimate_events: int = 28000
    campaign_min_events: int = 5
    campaign_max_events: int = 20


@dataclass(slots=True)
class TrainingConfig:
    validation_fraction: float = 0.20
    test_fraction: float = 0.20
    target_legitimate_fpr: float = 0.01
    known_attack_families: list[str] = field(default_factory=list)
    adaptive_attack_families: list[str] = field(default_factory=list)
    held_out_attack_families: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RedTeamConfig:
    campaign_budget: int = 72
    events_per_evaluation: int = 12
    linucb_alpha: float = 1.15
    rolling_context_window: int = 8
    validity_penalty: float = -1.0
    approved_value_scale: float = 500.0
    evasion_reward_weight: float = 2.5
    detection_cost_rate: float = 0.16
    resource_cost_per_event: float = 2.5
    novelty_bonus: float = 0.20


@dataclass(slots=True)
class LoopConfig:
    adversarial_rounds: int = 2
    top_evasions_per_round: int = 12


@dataclass(slots=True)
class AegisConfig:
    seed: int = 20260812
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    red_team: RedTeamConfig = field(default_factory=RedTeamConfig)
    loop: LoopConfig = field(default_factory=LoopConfig)


def _construct(cls: type, values: dict[str, Any] | None):
    return cls(**(values or {}))


def load_config(path: str | Path | None = None) -> AegisConfig:
    """Load a YAML config, falling back to safe deterministic defaults."""

    if path is None:
        return AegisConfig()
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return AegisConfig(
        seed=int(raw.get("seed", 20260812)),
        simulation=_construct(SimulationConfig, raw.get("simulation")),
        training=_construct(TrainingConfig, raw.get("training")),
        red_team=_construct(RedTeamConfig, raw.get("red_team")),
        loop=_construct(LoopConfig, raw.get("loop")),
    )
