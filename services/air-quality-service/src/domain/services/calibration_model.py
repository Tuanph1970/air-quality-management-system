"""Calibration model domain service.

ML-based sensor calibration using satellite reference data.  Uses
gradient boosting to learn the mapping from raw sensor readings
(with environmental covariates) to satellite-validated values.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor


@dataclass
class TrainingResult:
    """Result of training a calibration model."""

    model_version: str
    r_squared: float
    rmse: float
    mae: float
    training_samples: int
    feature_importance: Dict[str, float]


@dataclass
class EvaluationMetrics:
    """Model evaluation metrics on test data."""

    r_squared: float
    rmse: float
    mae: float
    bias: float


class CalibrationModel:
    """ML model for sensor calibration using satellite reference.

    Features used:
        - raw_pm25: Raw PM2.5 from sensor
        - temperature: Ambient temperature
        - humidity: Relative humidity
        - satellite_aod: Satellite AOD value
        - hour: Hour of day (0-23)
        - day_of_week: Day of week (0-6)
    """

    FEATURE_NAMES = [
        "raw_pm25",
        "temperature",
        "humidity",
        "satellite_aod",
        "hour",
        "day_of_week",
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/models/calibration_model.joblib"
        self.model = self._load_or_create_model()
        self.is_trained = os.path.exists(self.model_path)

    def _load_or_create_model(self):
        """Load existing model or create a new untrained one."""
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)
        return GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def calibrate(self, features: Dict) -> Dict:
        """Apply calibration to a raw sensor reading.

        Parameters
        ----------
        features:
            Dict with keys matching ``FEATURE_NAMES``.

        Returns
        -------
        dict
            ``{'pm25': calibrated_value, 'pm10': calibrated_value | None}``
        """
        if not self.is_trained:
            return {
                "pm25": features.get("raw_pm25"),
                "pm10": features.get("raw_pm10"),
            }

        X = np.array(
            [
                [
                    features.get("raw_pm25", 0),
                    features.get("temperature", 25),
                    features.get("humidity", 50),
                    features.get("satellite_aod", 0.5),
                    features.get("hour", 12),
                    features.get("day_of_week", 0),
                ]
            ]
        )

        calibrated_pm25 = float(self.model.predict(X)[0])

        # Apply same calibration ratio to PM10 if available.
        calibrated_pm10 = None
        raw_pm25 = features.get("raw_pm25")
        raw_pm10 = features.get("raw_pm10")
        if raw_pm10 and raw_pm25 and raw_pm25 != 0:
            ratio = calibrated_pm25 / raw_pm25
            calibrated_pm10 = float(raw_pm10 * ratio)

        return {
            "pm25": calibrated_pm25,
            "pm10": calibrated_pm10,
        }

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(
        self,
        training_data: List[Tuple[Dict, float]],
    ) -> TrainingResult:
        """Train calibration model with matched sensor-satellite pairs.

        Parameters
        ----------
        training_data:
            List of ``(feature_dict, satellite_reference_value)`` pairs.

        Returns
        -------
        TrainingResult
            Model performance metrics and feature importance.

        Raises
        ------
        ValueError
            If fewer than 50 training samples are provided.
        """
        if len(training_data) < 50:
            raise ValueError("Need at least 50 samples for training")

        X: List[List[float]] = []
        y: List[float] = []

        for features, reference in training_data:
            X.append(
                [
                    features.get("raw_pm25", 0),
                    features.get("temperature", 25),
                    features.get("humidity", 50),
                    features.get("satellite_aod", 0.5),
                    features.get("hour", 12),
                    features.get("day_of_week", 0),
                ]
            )
            y.append(reference)

        X_arr = np.array(X)
        y_arr = np.array(y)

        # Fit model.
        self.model.fit(X_arr, y_arr)

        # Evaluate on training set.
        y_pred = self.model.predict(X_arr)
        ss_res = float(np.sum((y_arr - y_pred) ** 2))
        ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse = float(np.sqrt(np.mean((y_arr - y_pred) ** 2)))
        mae = float(np.mean(np.abs(y_arr - y_pred)))

        # Persist model.
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        self.is_trained = True

        importance = dict(
            zip(self.FEATURE_NAMES, self.model.feature_importances_)
        )

        return TrainingResult(
            model_version=f"v{len(training_data)}_{int(r_squared * 100)}",
            r_squared=r_squared,
            rmse=rmse,
            mae=mae,
            training_samples=len(training_data),
            feature_importance=importance,
        )

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def evaluate(
        self, test_data: List[Tuple[Dict, float]]
    ) -> EvaluationMetrics:
        """Evaluate model on held-out test data.

        Parameters
        ----------
        test_data:
            List of ``(feature_dict, satellite_reference_value)`` pairs.

        Returns
        -------
        EvaluationMetrics
            R², RMSE, MAE, and bias on the test set.
        """
        X: List[List[float]] = []
        y_true: List[float] = []

        for features, reference in test_data:
            X.append(
                [
                    features.get("raw_pm25", 0),
                    features.get("temperature", 25),
                    features.get("humidity", 50),
                    features.get("satellite_aod", 0.5),
                    features.get("hour", 12),
                    features.get("day_of_week", 0),
                ]
            )
            y_true.append(reference)

        X_arr = np.array(X)
        y_true_arr = np.array(y_true)
        y_pred = self.model.predict(X_arr)

        ss_res = float(np.sum((y_true_arr - y_pred) ** 2))
        ss_tot = float(np.sum((y_true_arr - np.mean(y_true_arr)) ** 2))
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        rmse = float(np.sqrt(np.mean((y_true_arr - y_pred) ** 2)))
        mae = float(np.mean(np.abs(y_true_arr - y_pred)))
        bias = float(np.mean(y_pred - y_true_arr))

        return EvaluationMetrics(
            r_squared=r_squared,
            rmse=rmse,
            mae=mae,
            bias=bias,
        )
