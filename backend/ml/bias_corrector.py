import numpy as np
import pickle
import os
from sklearn.ensemble import GradientBoostingRegressor

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]
FEATURE_NAMES = ["raw_rainfall", "wind_shear", "olr", "cape", "vorticity", "moisture_flux", "humidity_700", "lead_time"]
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models")


class BiasCorrector:
    def __init__(self):
        self.correctors = {}
        self.is_trained = False

    def train(self, df):
        results = {}
        for regime in REGIMES:
            regime_df = df[df["regime"] == regime]
            if len(regime_df) < 50:
                continue
            X = regime_df[FEATURE_NAMES].values
            y = regime_df["corrected_rainfall"].values
            model = GradientBoostingRegressor(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                min_samples_split=5,
                min_samples_leaf=3,
                random_state=42,
            )
            model.fit(X, y)
            self.correctors[regime] = model
            train_pred = model.predict(X)
            rmse = float(np.sqrt(np.mean((train_pred - y) ** 2)))
            results[regime] = {"rmse": round(rmse, 3), "n_samples": len(regime_df)}
        self.is_trained = True
        return results

    def predict(self, raw_rainfall, features, regime, lead_time=24):
        if not self.is_trained:
            self.load()
        if regime not in self.correctors:
            return max(0, raw_rainfall / 1.2)
        X = np.array([[
            raw_rainfall,
            features.get("wind_shear", 0),
            features.get("olr", 0),
            features.get("cape", 0),
            features.get("vorticity", 0),
            features.get("moisture_flux", 0),
            features.get("humidity_700", 0),
            lead_time,
        ]])
        corrected = float(self.correctors[regime].predict(X)[0])
        return round(max(0, corrected), 1)

    def save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        path = os.path.join(MODEL_DIR, "bias_corrector.pkl")
        with open(path, "wb") as f:
            pickle.dump({"correctors": self.correctors}, f)

    def load(self):
        path = os.path.join(MODEL_DIR, "bias_corrector.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.correctors = data["correctors"]
            self.is_trained = True
