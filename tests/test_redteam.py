import pandas as pd

from aegisloop.config import RedTeamConfig, SimulationConfig
from aegisloop.defender import AegisDefender
from aegisloop.fidelity import FidelityGate
from aegisloop.redteam import LinUCBStrategy, RedTeamArena, build_action_space
from aegisloop.simulator import PaymentDigitalTwin


def test_bandit_arena_runs_with_frozen_black_box_defender():
    simulation = SimulationConfig(customers=180, merchants=60, devices=220, beneficiaries=80, legitimate_events=1200)
    twin = PaymentDigitalTwin(simulation, seed=27)
    legitimate = twin.generate_legitimate(900)
    attacks = twin.generate_attack_set(["adaptive_card_testing", "ai_app_scam_mule"], 8, seed=29)
    train = pd.concat([legitimate.iloc[:550], attacks.iloc[: int(len(attacks) * 0.65)]], ignore_index=True)
    valid = pd.concat([legitimate.iloc[550:725], attacks.iloc[int(len(attacks) * 0.65) :]], ignore_index=True)
    defender = AegisDefender(target_fpr=0.03, random_state=27).fit(train, valid)
    actions = build_action_space(31, variants_per_family=2)
    bandit = LinUCBStrategy(actions, context_dim=6, alpha=1.0)
    arena = RedTeamArena(twin, defender, FidelityGate(legitimate), RedTeamConfig(campaign_budget=5, events_per_evaluation=6), seed=33)
    results, campaigns = arena.run(bandit, budget=5)
    assert len(results) == 5
    assert set(results["strategy"]) == {"contextual_bandit"}
    assert results["valid"].mean() > 0.5
    assert len(campaigns) > 0


def test_reward_decomposition_reconciles_exactly():
    simulation = SimulationConfig(customers=180, merchants=60, devices=220, beneficiaries=80, legitimate_events=1200)
    twin = PaymentDigitalTwin(simulation, seed=37)
    legitimate = twin.generate_legitimate(900)
    attacks = twin.generate_attack_set(["adaptive_card_testing", "ai_app_scam_mule"], 8, seed=39)
    train = pd.concat([legitimate.iloc[:550], attacks.iloc[: int(len(attacks) * 0.65)]], ignore_index=True)
    valid = pd.concat([legitimate.iloc[550:725], attacks.iloc[int(len(attacks) * 0.65) :]], ignore_index=True)
    defender = AegisDefender(target_fpr=0.03, random_state=37).fit(train, valid)
    actions = build_action_space(41, variants_per_family=2)
    results, _ = RedTeamArena(
        twin,
        defender,
        FidelityGate(legitimate),
        RedTeamConfig(campaign_budget=5, events_per_evaluation=6),
        seed=43,
    ).run(LinUCBStrategy(actions, context_dim=6, alpha=1.0), budget=5)
    valid_results = results[results["valid"]]
    reconstructed = valid_results[
        ["value_term", "evasion_term", "detection_cost_term", "resource_cost_term", "novelty_term"]
    ].sum(axis=1) * valid_results["fidelity"]
    assert ((reconstructed - valid_results["reward"]).abs() < 1e-10).all()
