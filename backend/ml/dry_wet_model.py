"""
Dry/Wet hurdle model: predicts P(observed_rainfall >= 1.0mm) from forecast features.
Used to zero out corrected rainfall on districts likely to stay dry (hurdle model).
"""
import numpy as np
import os
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss

FEATURE_NAMES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
    "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude",
    "lead_time",
]
WET_MM = 1.0
ZERO_THRESHOLD = 0.5


def _temporal_split(df):
    dates = sorted(df["date"].unique())
    split_idx = int(len(dates) * 0.8)
    train_dates = set(dates[:split_idx])
    test_dates = set(dates[split_idx:])
    return df["date"].isin(train_dates).values, df["date"].isin(test_dates).values


class DryWetModel:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.wet_rate = 0.0
        self.zero_threshold = ZERO_THRESHOLD
        self.metrics_ = {}
        self._feature_names = FEATURE_NAMES

    def _get_model(self, n_estimators=250, max_depth=7, learning_rate=0.05):
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
        X = df[FEATURE_NAMES].values.astype(np.float64)
        y = (df["observed_rainfall"].values >= WET_MM).astype(int)
        self.wet_rate = float(y.mean())

        train_mask, test_mask = _temporal_split(df)
        X_train, X_test = X[train_mask], X[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]

        configs = [
            {"n_estimators": 250, "max_depth": 7, "learning_rate": 0.05},
            {"n_estimators": 400, "max_depth": 9, "learning_rate": 0.03},
            {"n_estimators": 150, "max_depth": 5, "learning_rate": 0.1},
        ]
        best_model = None
        best_score = -float("inf")
        test_has_both = len(np.unique(y_test)) > 1

        for params in configs:
            model = self._get_model(**params)
            model.fit(X_train, y_train)
            if test_has_both:
                score = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
            else:
                score = accuracy_score(y_test, model.predict(X_test))
            if score > best_score:
                best_score = score
                best_model = model

        best_model.fit(X, y)
        self.model = best_model
        self.is_trained = True

        prob_wet = best_model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, (prob_wet >= 0.5).astype(int))
        brier = brier_score_loss(y_test, prob_wet)
        self.metrics_ = {
            "auc": round(float(best_score), 4),
            "accuracy": round(float(acc), 4),
            "brier": round(float(brier), 4),
            "wet_rate": round(self.wet_rate, 4),
            "zero_threshold": self.zero_threshold,
            "n_samples": len(df),
            "n_train": int(train_mask.sum()),
            "n_test": int(test_mask.sum()),
            "split": "temporal",
        }
        return self.metrics_

    def predict_wet_prob(self, raw_rainfall, features, lead_time=24):
        if not self.is_trained or self.model is None:
            return 0.5
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
        return float(self.model.predict_proba(X)[0, 1])

    def should_zero(self, raw_rainfall, features, lead_time=24):
        return self.predict_wet_prob(raw_rainfall, features, lead_time) < self.zero_threshold