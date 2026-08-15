import pandas as pd

from aegisloop.config import SimulationConfig
from aegisloop.defender import AegisDefender
from aegisloop.simulator import PaymentDigitalTwin


def test_defender_scores_and_actions_are_operational():
    config = SimulationConfig(customers=180, merchants=60, devices=220, beneficiaries=80, legitimate_events=1200)
    twin = PaymentDigitalTwin(config, seed=17)
    legitimate = twin.generate_legitimate(900)
    attacks = twin.generate_attack_set(["adaptive_card_testing", "ai_app_scam_mule"], 8, seed=19)
    train = pd.concat([legitimate.iloc[:550], attacks.iloc[: int(len(attacks) * 0.65)]], ignore_index=True)
    valid = pd.concat([legitimate.iloc[550:725], attacks.iloc[int(len(attacks) * 0.65) : int(len(attacks) * 0.82)]], ignore_index=True)
    test = pd.concat([legitimate.iloc[725:], attacks.iloc[int(len(attacks) * 0.82) :]], ignore_index=True)
    defender = AegisDefender(target_fpr=0.03, random_state=17).fit(train, valid)
    scores = defender.score(test)
    assert len(scores) == len(test)
    assert ((scores >= 0) & (scores <= 1)).all()
    assert set(defender.decide(test)["decision"]).issubset({"approve", "step_up", "hold", "decline"})


def test_threshold_metadata_names_validation_calibration_only():
    config = SimulationConfig(customers=180, merchants=60, devices=220, beneficiaries=80, legitimate_events=1200)
    twin = PaymentDigitalTwin(config, seed=47)
    legitimate = twin.generate_legitimate(900)
    attacks = twin.generate_attack_set(["adaptive_card_testing", "ai_app_scam_mule"], 8, seed=49)
    train = pd.concat([legitimate.iloc[:550], attacks.iloc[: int(len(attacks) * 0.65)]], ignore_index=True)
    valid = pd.concat([legitimate.iloc[550:725], attacks.iloc[int(len(attacks) * 0.65) : int(len(attacks) * 0.82)]], ignore_index=True)
    defender = AegisDefender(target_fpr=0.03, random_state=47).fit(
        train,
        valid,
        calibration_label="unit_test_validation",
    )
    assert defender.calibration_metadata["source"] == "unit_test_validation"
    assert defender.calibration_metadata["legitimate_rows"] == 175
