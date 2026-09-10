import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]
FEATURE_NAMES = ["wind_shear", "olr", "cape", "vorticity", "moisture_flux", "humidity_700"]
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models", "regime_classifier.pkl")


class RegimeClassifier:
    def __init__(self):
        self.model = None
        self.is_trained = False

    def train(self, df):
        X = df[FEATURE_NAMES].values
        y = df["regime"].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        return {"accuracy": round(accuracy, 4), "report": report, "n_train": len(X_train), "n_test": len(X_test)}

    def predict(self, features):
        if not self.is_trained:
            self.load()
        X = np.array([[features.get(f, 0) for f in FEATURE_NAMES]])
        probs = self.model.predict_proba(X)[0]
        classes = self.model.classes_
        idx = int(np.argmax(probs))
        return {
            "type": classes[idx],
            "confidence": round(float(probs[idx]), 4),
            "all_probabilities": {c: round(float(p), 4) for c, p in zip(classes, probs)},
        }

    def save(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"model": self.model, "features": FEATURE_NAMES}, f)

    def load(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                data = pickle.load(f)
            self.model = data["model"]
            self.is_trained = True
