import numpy as np

from aegisloop.attacks import ATTACK_ATLAS, atlas_by_family, sample_action, scenario_dsl


def test_attack_atlas_is_diverse_and_serializable():
    assert len(ATTACK_ATLAS) >= 8
    assert len({card.channel for card in ATTACK_ATLAS}) >= 6
    assert len({card.rail for card in ATTACK_ATLAS}) >= 3
    assert len(scenario_dsl()) == len(ATTACK_ATLAS)


def test_sampled_action_stays_inside_safe_parameter_bounds():
    rng = np.random.default_rng(7)
    card = atlas_by_family()["agentic_intent_hijack"]
    action = sample_action(card, rng)
    assert 0.4 <= action.amount_scale <= 2.3
    assert 0.03 <= action.device_reuse <= 0.99

