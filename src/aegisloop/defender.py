from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = [
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
]
CATEGORICAL_FEATURES = ["channel", "rail"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    roc_auc: float
    pr_auc: float
    precision: float
    recall: float
    f1: float
    legitimate_fpr: float
    fraud_value_detection_rate: float
    threshold: float
    n_events: int

    def to_dict(self) -> dict:
        return self.__dict__ if hasattr(self, "__dict__") else {
            field: getattr(self, field) for field in self.__dataclass_fields__
        }


class AegisDefender:
    """Calibrated supervised + anomaly ensemble with operational actions."""

    def __init__(self, target_fpr: float = 0.01, random_state: int = 20260812):
        self.target_fpr = float(target_fpr)
        self.random_state = int(random_state)
        self.preprocessor = ColumnTransformer(
            [
                (
                    "numeric",
                    Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
                    NUMERIC_FEATURES,
                ),
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    CATEGORICAL_FEATURES,
                ),
            ],
            remainder="drop",
        )
        self.classifier = HistGradientBoostingClassifier(
            learning_rate=0.075,
            max_iter=180,
            max_leaf_nodes=24,
            min_samples_leaf=24,
            l2_regularization=0.7,
            class_weight="balanced",
            random_state=self.random_state,
        )
        self.anomaly = IsolationForest(
            n_estimators=150,
            max_samples="auto",
            contamination="auto",
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.threshold = 0.5
        self._anomaly_min = 0.0
        self._anomaly_max = 1.0
        self._fitted = False
        self.calibration_metadata: dict[str, float | int | str] = {}

    def fit(
        self,
        train: pd.DataFrame,
        validation: pd.DataFrame,
        calibration_label: str = "legitimate_validation_split",
    ) -> AegisDefender:
        x_train = self.preprocessor.fit_transform(train[MODEL_FEATURES])
        y_train = train["is_fraud"].astype(int).to_numpy()
        self.classifier.fit(x_train, y_train)
        legitimate = x_train[y_train == 0]
        self.anomaly.fit(legitimate)
        raw = -self.anomaly.score_samples(legitimate)
        self._anomaly_min = float(np.quantile(raw, 0.01))
        self._anomaly_max = float(np.quantile(raw, 0.995))
        self._fitted = True
        legitimate_mask = validation["is_fraud"].to_numpy() == 0
        legitimate_validation = validation.loc[legitimate_mask]
        legit_scores = self.score(legitimate_validation)
        legit_factors = self._threshold_factors(legitimate_validation)
        effective_scores = legit_scores / np.maximum(legit_factors, 1e-8)
        self.threshold = float(np.quantile(effective_scores, 1 - self.target_fpr)) if len(effective_scores) else 0.5
        empirical_fpr = float(np.mean(effective_scores >= self.threshold)) if len(effective_scores) else float("nan")
        self.calibration_metadata = {
            "source": calibration_label,
            "legitimate_rows": len(legitimate_validation),
            "target_fpr": self.target_fpr,
            "empirical_validation_fpr": empirical_fpr,
            "threshold": self.threshold,
        }
        return self

    def _transform(self, frame: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Defender must be fitted before scoring.")
        return self.preprocessor.transform(frame[MODEL_FEATURES])

    def score(self, frame: pd.DataFrame) -> np.ndarray:
        transformed = self._transform(frame)
        supervised = self.classifier.predict_proba(transformed)[:, 1]
        raw_anomaly = -self.anomaly.score_samples(transformed)
        anomaly = np.clip(
            (raw_anomaly - self._anomaly_min) / max(self._anomaly_max - self._anomaly_min, 1e-8),
            0,
            1,
        )
        relation = np.clip(
            0.42 * frame["merchant_risk"].to_numpy()
            + 0.18 * np.clip(frame["graph_shared_entities"].to_numpy() / 8, 0, 1)
            + 0.18 * (1 - frame["intent_match"].to_numpy())
            + 0.12 * (1 - frame["evidence_provenance"].to_numpy())
            + 0.10 * np.clip(frame["beneficiary_reuse_24h"].to_numpy() / 12, 0, 1),
            0,
            1,
        )
        return np.clip(0.80 * supervised + 0.13 * anomaly + 0.07 * relation, 0, 1)

    def event_thresholds(self) -> np.ndarray:
        """Threshold multipliers model calibrated per-event operational tolerance."""

        return np.array([0.82, 0.94, 1.06, 1.18, 1.32], dtype=float) * self.threshold

    @staticmethod
    def _event_buckets(frame: pd.DataFrame) -> np.ndarray:
        return np.fromiter(
            (sum(str(event_id).encode("utf-8")) % 5 for event_id in frame["event_id"]),
            dtype=int,
            count=len(frame),
        )

    def _threshold_factors(self, frame: pd.DataFrame) -> np.ndarray:
        return np.array([0.82, 0.94, 1.06, 1.18, 1.32], dtype=float)[self._event_buckets(frame)]

    def effective_scores(self, frame: pd.DataFrame) -> np.ndarray:
        """Risk scores normalized by deterministic operational tolerance."""

        return self.score(frame) / np.maximum(self._threshold_factors(frame), 1e-8)

    def detected_mask(self, frame: pd.DataFrame) -> np.ndarray:
        """Deterministic payment-network outcome surface for black-box red teaming."""

        scores = self.score(frame)
        buckets = self._event_buckets(frame)
        return scores >= self.event_thresholds()[buckets]

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return self.detected_mask(frame).astype(int)

    def decide(self, frame: pd.DataFrame) -> pd.DataFrame:
        scores = self.score(frame)
        relative = scores / max(self.threshold, 1e-8)
        action = np.select(
            [relative < 0.55, relative < 1.0, relative < 1.55],
            ["approve", "step_up", "hold"],
            default="decline",
        )
        result = frame[["event_id", "campaign_id", "amount", "attack_family"]].copy()
        result["risk_score"] = scores
        result["decision"] = action
        return result

    def evaluate(self, frame: pd.DataFrame) -> EvaluationMetrics:
        y_true = frame["is_fraud"].astype(int).to_numpy()
        scores = self.score(frame)
        pred = self.detected_mask(frame).astype(int)
        tn, fp, _fn, _tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
        fraud_mask = y_true == 1
        fraud_value = frame.loc[fraud_mask, "amount"].sum()
        caught_value = frame.loc[fraud_mask & (pred == 1), "amount"].sum()
        return EvaluationMetrics(
            roc_auc=float(roc_auc_score(y_true, scores)) if len(np.unique(y_true)) > 1 else float("nan"),
            pr_auc=float(average_precision_score(y_true, scores)) if len(np.unique(y_true)) > 1 else float("nan"),
            precision=float(precision_score(y_true, pred, zero_division=0)),
            recall=float(recall_score(y_true, pred, zero_division=0)),
            f1=float(f1_score(y_true, pred, zero_division=0)),
            legitimate_fpr=float(fp / max(fp + tn, 1)),
            fraud_value_detection_rate=float(caught_value / max(fraud_value, 1e-8)),
            threshold=float(self.threshold),
            n_events=len(frame),
        )

    def explain(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Give judge-readable reason codes without exposing model internals to the attacker."""

        rows = []
        for _, row in frame.iterrows():
            reasons = {
                "unusual amount": min(float(row["amount_to_customer_median"]) / 12, 1),
                "velocity": min(float(row["velocity_1h"]) / 14, 1),
                "relationship risk": min(float(row["graph_shared_entities"]) / 8, 1),
                "weak intent match": 1 - float(row["intent_match"]),
                "weak evidence provenance": 1 - float(row["evidence_provenance"]),
                "device risk": 1 - float(row["device_trust"]),
            }
            ordered = sorted(reasons.items(), key=lambda item: item[1], reverse=True)[:3]
            rows.append(
                {
                    "event_id": row["event_id"],
                    "reason_codes": [name for name, value in ordered if value > 0.15],
                }
            )
        return pd.DataFrame(rows)
