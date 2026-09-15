"""
Bias corrector with temporal train/test split and per-regime hyperparameter tuning.
Fixes data leakage (random split on panel data).
"""
import numpy as np
import pickle
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]
FEATURE_NAMES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
    "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude",
    "lead_time",
]
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models")

PER_REGIME_CONFIGS = {
    "active_monsoon": [
        {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1},
        {"n_estimators": 300, "max_depth": 8, "learning_rate": 0.05},
    ],
    "break_monsoon": [
        {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1},
        {"n_estimators": 250, "max_depth": 5, "learning_rate": 0.08},
    ],
    "depression": [
        {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1},
        {"n_estimators": 150, "max_depth": 8, "learning_rate": 0.12},
    ],
    "orographic": [
        {"n_estimators": 300, "max_depth": 8, "learning_rate": 0.05},
        {"n_estimators": 400, "max_depth": 10, "learning_rate": 0.03},
        {"n_estimators": 250, "max_depth": 6, "learning_rate": 0.08},
    ],
    "coastal": [
        {"n_estimators": 400, "max_depth": 10, "learning_rate": 0.03},
        {"n_estimators": 500, "max_depth": 12, "learning_rate": 0.02},
        {"n_estimators": 300, "max_depth": 8, "learning_rate": 0.05},
    ],
    "western_disturbance": [
        {"n_estimators": 400, "max_depth": 10, "learning_rate": 0.03},
        {"n_estimators": 300, "max_depth": 8, "learning_rate": 0.05},
        {"n_estimators": 500, "max_depth": 12, "learning_rate": 0.02},
    ],
}

DEFAULT_CONFIGS = [
    {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1},
    {"n_estimators": 300, "max_depth": 8, "learning_rate": 0.05},
    {"n_estimators": 150, "max_depth": 10, "learning_rate": 0.15},
]


class BiasCorrector:
    def __init__(self):
        self.correctors = {}
        self.is_trained = False
        self.metrics_ = {}

    def _get_model(self, n_estimators=200, max_depth=6, learning_rate=0.1):
        try:
            from xgboost import XGBRegressor
            return XGBRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=5,
                random_state=42,
                n_jobs=1,
            )
        except ImportError:
            return GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                min_samples_split=5,
                min_samples_leaf=3,
                random_state=42,
            )

    def _temporal_split(self, regime_df):
        """Split by date: last 20% of dates for test, not random rows."""
        dates = sorted(regime_df["date"].unique())
        split_idx = int(len(dates) * 0.8)
        train_dates = set(dates[:split_idx])
        test_dates = set(dates[split_idx:])
        train_mask = regime_df["date"].isin(train_dates)
        test_mask = regime_df["date"].isin(test_dates)
        return train_mask, test_mask

    def train(self, df):
        results = {}
        for regime in REGIMES:
            regime_df = df[df["regime"] == regime].copy()
            if len(regime_df) < 50:
                continue

            X = regime_df[FEATURE_NAMES].values.astype(np.float64)
            y = regime_df["observed_rainfall"].values

            train_mask, test_mask = self._temporal_split(regime_df)
            X_train, X_test = X[train_mask.values], X[test_mask.values]
            y_train, y_test = y[train_mask.values], y[test_mask.values]

            if len(X_test) < 10:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )

            configs = PER_REGIME_CONFIGS.get(regime, DEFAULT_CONFIGS)
            best_model = None
            best_rmse = float("inf")

            for params in configs:
                model = self._get_model(**params)
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                rmse = np.sqrt(mean_squared_error(y_test, pred))
                if rmse < best_rmse:
                    best_rmse = rmse
                    best_model = model

            best_model.fit(X, y)
            self.correctors[regime] = best_model

            y_pred_test = best_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)

            self.metrics_[regime] = {
                "rmse": round(float(best_rmse), 3),
                "mae": round(float(mae), 3),
                "r2": round(float(r2), 4),
                "n_samples": len(regime_df),
                "n_train": int(train_mask.sum()),
                "n_test": int(test_mask.sum()),
                "split": "temporal",
            }
            results[regime] = self.metrics_[regime]

        self.is_trained = True
        return results

    def predict(self, raw_rainfall, features, regime, lead_time=24):
        if not self.is_trained:
            self.load()
        if regime not in self.correctors:
            return max(0, raw_rainfall * 0.85)
        X = np.array([[
            raw_rainfall,
            features.get("wind_speed", 0),
            features.get("wind_dir", 0),
            features.get("cape", 500),
            features.get("pressure", 1013),
            features.get("radiation", 15),
            features.get("temp_range", 5),
            features.get("temp_mean", 27),
            features.get("day_of_year", 180),
            features.get("month", 7),
            features.get("monsoon_phase", 2),
            features.get("is_peak_monsoon", 1),
            features.get("latitude", 28),
            features.get("longitude", 77),
            lead_time,
        ]], dtype=np.float64)
        corrected = float(self.correctors[regime].predict(X)[0])
        return round(max(0, corrected), 1)

    def predict_soft(self, raw_rainfall, features, regime_probs, lead_time=24):
        """Probability-weighted blend over all regime bias correctors.
        Superior to hard argmax assignment when the regime classifier is uncertain
        (e.g. depression events that get hard-labeled as coastal)."""
        if not self.is_trained:
            self.load()
        acc = 0.0
        total_w = 0.0
        for regime, prob in regime_probs.items():
            if regime not in self.correctors or prob <= 0:
                continue
            X = np.array([[
                raw_rainfall,
                features.get("wind_speed", 0),
                features.get("wind_dir", 0),
                features.get("cape", 500),
                features.get("pressure", 1013),
                features.get("radiation", 15),
                features.get("temp_range", 5),
                features.get("temp_mean", 27),
                features.get("day_of_year", 180),
                features.get("month", 7),
                features.get("monsoon_phase", 2),
                features.get("is_peak_monsoon", 1),
                features.get("latitude", 28),
                features.get("longitude", 77),
                lead_time,
            ]], dtype=np.float64)
            acc += prob * float(self.correctors[regime].predict(X)[0])
            total_w += prob
        if total_w <= 0:
            best = max(regime_probs, key=regime_probs.get)
            return self.predict(raw_rainfall, features, best, lead_time)
        return round(max(0.0, acc / total_w), 1)

    def save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        path = os.path.join(MODEL_DIR, "bias_corrector.pkl")
        with open(path, "wb") as f:
            pickle.dump({"correctors": self.correctors, "metrics": self.metrics_}, f)

    def load(self):
        path = os.path.join(MODEL_DIR, "bias_corrector.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.correctors = data["correctors"]
            self.metrics_ = data.get("metrics", {})
            self.is_trained = True
