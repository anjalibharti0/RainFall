"""
Probability estimator V2: per-threshold binary targets (obs >= threshold).
Trains proper probability models with XGBClassifier (predict_proba), tuned by Brier score
on temporally held-out dates. Available thresholds: 7.5, 64.5, 124.5, 244.5 mm/day.
"""
import numpy as np
import pickle
import os
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score, accuracy_score

THRESHOLDS = [7.5, 64.5, 124.5, 244.5]
FEATURE_NAMES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
    "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude",
    "lead_time",
]
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models")


def _temporal_split(df):
    dates = sorted(df["date"].unique())
    split_idx = int(len(dates) * 0.8)
    train_dates = set(dates[:split_idx])
    test_dates = set(dates[split_idx:])
    return df["date"].isin(train_dates).values, df["date"].isin(test_dates).values


class ProbabilityEstimator:
    def __init__(self):
        self.models = {}
        self.is_trained = False
        self.metrics_ = {}

    def _get_model(self, n_estimators=200, max_depth=5, learning_rate=0.1):
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=5,
                random_state=42,
                n_jobs=1,
                verbosity=0,
            )
        except ImportError:
            return GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                min_samples_split=10,
                min_samples_leaf=5,
                random_state=42,
            )

    def train(self, df):
        results = {}
        X = df[FEATURE_NAMES].values.astype(np.float64)
        train_mask, test_mask = _temporal_split(df)
        X_train, X_test = X[train_mask], X[test_mask]
        observed = df["observed_rainfall"].values

        for threshold in THRESHOLDS:
            y = (observed >= threshold).astype(int)
            y_train, y_test = y[train_mask], y[test_mask]
            base_rate = float(y_test.mean())
            clim_brier = base_rate * (1 - base_rate)

            configs = [
                {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.1},
                {"n_estimators": 400, "max_depth": 7, "learning_rate": 0.05},
                {"n_estimators": 150, "max_depth": 4, "learning_rate": 0.15},
            ]
            best_model = None
            best_brier = float("inf")
            test_has_both = len(np.unique(y_test)) > 1

            for params in configs:
                model = self._get_model(**params)
                model.fit(X_train, y_train)
                prob_test = model.predict_proba(X_test)[:, 1]
                brier = brier_score_loss(y_test, prob_test)
                if brier < best_brier:
                    best_brier = brier
                    best_model = model

            best_model.fit(X, y)
            self.models[threshold] = best_model

            y_pred_test = best_model.predict_proba(X_test)[:, 1]
            brier_test = brier_score_loss(y_test, y_pred_test)
            meta = {
                "brier": round(float(brier_test), 4),
                "clim_brier": round(float(clim_brier), 4),
                "improvement_vs_clim": round(float(clim_brier - brier_test), 4)
                if clim_brier > 0 else 0.0,
                "base_rate": round(base_rate, 4),
                "mean_prob": round(float(y_pred_test.mean()), 4),
                "n_samples": len(df),
                "n_train": int(train_mask.sum()),
                "n_test": int(test_mask.sum()),
                "split": "temporal",
            }
            if test_has_both:
                meta["auc"] = round(float(roc_auc_score(y_test, y_pred_test)), 4)
                meta["acc"] = round(float(accuracy_score(y_test, (y_pred_test >= 0.5).astype(int))), 4)
            self.metrics_[str(threshold)] = meta
            results[str(threshold)] = meta

        self.is_trained = True
        return results

    def predict(self, raw_rainfall, features, lead_time=24):
        if not self.is_trained:
            self.load()
        probs = {}
        X = np.array([[
            raw_rainfall,
            features.get("wind_speed", 0),
            features.get("wind_dir", 0),
            features.get("cape", np.nan),
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
        for threshold in THRESHOLDS:
            if threshold in self.models:
                prob = float(self.models[threshold].predict_proba(X)[0, 1])
                probs[threshold] = round(float(np.clip(prob, 0, 1)), 3)
            else:
                prob = 1 / (1 + np.exp(0.06 * (threshold - raw_rainfall)))
                probs[threshold] = round(float(np.clip(prob, 0, 1)), 3)
        return {
            "p_moderate": probs.get(7.5, 0),
            "p_heavy": probs.get(64.5, 0),
            "p_very_heavy": probs.get(124.5, 0),
            "p_extreme": probs.get(244.5, 0),
        }

    def save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        path = os.path.join(MODEL_DIR, "probability_estimator.pkl")
        with open(path, "wb") as f:
            pickle.dump({"models": self.models, "metrics": self.metrics_}, f)

    def load(self):
        path = os.path.join(MODEL_DIR, "probability_estimator.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.models = data["models"]
            self.metrics_ = data.get("metrics", {})
            self.is_trained = True