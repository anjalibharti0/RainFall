import numpy as np
import pickle
import os
from sklearn.ensemble import GradientBoostingRegressor

THRESHOLDS = [7.5, 64.5, 124.5, 244.5]
FEATURE_NAMES = ["corrected_rainfall", "wind_shear", "olr", "cape", "vorticity", "moisture_flux", "humidity_700", "lead_time", "pressure", "sst"]
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models")


class ProbabilityEstimator:
    def __init__(self):
        self.models = {}
        self.is_trained = False

    def train(self, df):
        results = {}
        for threshold in THRESHOLDS:
            target_col = f"p_exceed_{threshold}"
            if target_col not in df.columns:
                continue
            X = df[FEATURE_NAMES].values
            y = df[target_col].values
            model = GradientBoostingRegressor(
                n_estimators=120,
                max_depth=5,
                learning_rate=0.1,
                min_samples_split=5,
                random_state=42,
            )
            model.fit(X, y)
            self.models[threshold] = model
            pred = model.predict(X)
            mse = float(np.mean((pred - y) ** 2))
            results[str(threshold)] = {"mse": round(mse, 5), "n_samples": len(df)}
        self.is_trained = True
        return results

    def predict(self, corrected_rainfall, features, lead_time=24):
        if not self.is_trained:
            self.load()
        probs = {}
        X = np.array([[
            corrected_rainfall,
            features.get("wind_shear", 0),
            features.get("olr", 0),
            features.get("cape", 0),
            features.get("vorticity", 0),
            features.get("moisture_flux", 0),
            features.get("humidity_700", 0),
            lead_time,
            features.get("pressure", 1005),
            features.get("sst", 28),
        ]])
        for threshold in THRESHOLDS:
            if threshold in self.models:
                prob = float(self.models[threshold].predict(X)[0])
                probs[threshold] = round(float(np.clip(prob, 0, 1)), 3)
            else:
                prob = 1 / (1 + np.exp(0.06 * (threshold - corrected_rainfall)))
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
            pickle.dump({"models": self.models}, f)

    def load(self):
        path = os.path.join(MODEL_DIR, "probability_estimator.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.models = data["models"]
            self.is_trained = True
