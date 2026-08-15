from aegisloop.attacks import atlas_by_family, sample_action
from aegisloop.config import SimulationConfig
from aegisloop.fidelity import FidelityGate
from aegisloop.simulator import EVENT_COLUMNS, PaymentDigitalTwin


def test_digital_twin_is_deterministic_for_fixed_seed():
    config = SimulationConfig(customers=100, merchants=40, devices=120, beneficiaries=60, legitimate_events=300)
    first = PaymentDigitalTwin(config, seed=13).generate_legitimate(100)
    second = PaymentDigitalTwin(config, seed=13).generate_legitimate(100)
    assert first.drop(columns=["timestamp"]).equals(second.drop(columns=["timestamp"]))
    assert list(first.columns) == EVENT_COLUMNS


def test_valid_campaign_passes_hard_gate():
    config = SimulationConfig(customers=100, merchants=40, devices=120, beneficiaries=60, legitimate_events=300)
    twin = PaymentDigitalTwin(config, seed=13)
    legitimate = twin.generate_legitimate(200)
    card = atlas_by_family()["ai_app_scam_mule"]
    action = sample_action(card, twin.rng)
    campaign = twin.generate_campaign(action, n_events=8, seed=21)
    report = FidelityGate(legitimate).evaluate(campaign, action, card)
    assert report.valid
    assert report.score >= 0.78
    assert campaign["campaign_id"].nunique() == 1

