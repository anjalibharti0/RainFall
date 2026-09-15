import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]
FEATURE_NAMES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
    "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude",
]
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models", "regime_classifier.pkl")


class RegimeClassifier:
    def __init__(self):
        self.model = None
        self.le = LabelEncoder()
        self.is_trained = False
        self._feature_names = FEATURE_NAMES
        self.cv_scores_ = None
        self.feature_importances_ = None

    def _get_model(self, n_estimators=200, max_depth=15, learning_rate=0.1):
        """Try XGBoost first, fall back to RandomForest."""
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                random_state=42,
                n_jobs=1,
                eval_metric="mlogloss",

            )
        except ImportError:
            return RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )

    @staticmethod
    def _balanced_sample_weights(y):
        """class_weight='balanced' style weights: n_samples / (n_classes * count) per class."""
        counts = np.bincount(y)
        n = len(y)
        n_classes = len(counts)
        return np.array([n / (n_classes * counts[yi]) for yi in y], dtype=np.float64)

    def _cv_fit_score(self, model, X, y, sample_weight, skf):
        """Stratified CV with sample weights; returns mean macro-F1 and std."""
        macro_f1s = []
        for train_idx, val_idx in skf.split(X, y):
            model.fit(X[train_idx], y[train_idx], sample_weight=sample_weight[train_idx])
            pred = model.predict(X[val_idx])
            macro_f1s.append(f1_score(y[val_idx], pred, average="macro", zero_division=0))
        return float(np.mean(macro_f1s)), float(np.std(macro_f1s))

    def train(self, df, tune_hyperparams=True):
        X = df[FEATURE_NAMES].values.astype(np.float64)
        y_raw = df["regime"].values
        y = self.le.fit_transform(y_raw)

        if "date" in df.columns:
            dates = sorted(df["date"].unique())
            split_idx = int(len(dates) * 0.8)
            train_dates = set(dates[:split_idx])
            test_dates = set(dates[split_idx:])
            train_mask = df["date"].isin(train_dates).values
            test_mask = df["date"].isin(test_dates).values
            X_train, X_test = X[train_mask], X[test_mask]
            y_train, y_test = y[train_mask], y[test_mask]
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

        sample_weight = self._balanced_sample_weights(y_train)

        best_model = None
        best_cv = -1
        best_cv_std = 0.0
        best_params = {}

        if tune_hyperparams and len(X_train) > 200:
            configs = [
                {"n_estimators": 200, "max_depth": 12, "learning_rate": 0.1},
                {"n_estimators": 300, "max_depth": 15, "learning_rate": 0.05},
                {"n_estimators": 150, "max_depth": 20, "learning_rate": 0.15},
                {"n_estimators": 400, "max_depth": 10, "learning_rate": 0.08},
            ]
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42) if len(X_train) > 500 else StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

            for params in configs:
                model = self._get_model(**params)
                try:
                    mean_cv, std_cv = self._cv_fit_score(model, X_train, y_train, sample_weight, skf)
                    if mean_cv > best_cv:
                        best_cv = mean_cv
                        best_cv_std = std_cv
                        best_model = model
                        best_params = params
                except Exception:
                    continue
            print(f"  Best CV macro-F1: {best_cv:.4f} (std {best_cv_std:.4f}) with params: {best_params}")
        else:
            best_params = {"n_estimators": 200, "max_depth": 15, "learning_rate": 0.1}
            best_model = self._get_model(**best_params)

        best_model.fit(X_train, y_train, sample_weight=sample_weight)
        self.model = best_model
        self.is_trained = True

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
        report = classification_report(
            self.le.inverse_transform(y_test),
            self.le.inverse_transform(y_pred),
            output_dict=True,
        )

        if hasattr(self.model, "feature_importances_"):
            self.feature_importances_ = dict(zip(FEATURE_NAMES, self.model.feature_importances_.tolist()))

        cv_results = {"accuracy": round(accuracy, 4), "macro_f1": round(macro_f1, 4),
                      "report": report,
                      "n_train": len(X_train), "n_test": len(X_test),
                      "best_params": best_params,
                      "cv_mean": round(best_cv, 4) if best_cv >= 0 else None,
                      "cv_std": round(best_cv_std, 4) if best_cv >= 0 else None,
                      "balanced_classes": True}

        if self.feature_importances_:
            top5 = sorted(self.feature_importances_.items(), key=lambda x: -x[1])[:5]
            cv_results["top_features"] = {k: round(v, 4) for k, v in top5}

        return cv_results

    def predict(self, features):
        if not self.is_trained:
            self.load()
        X = np.array([[features.get(f, 0) for f in FEATURE_NAMES]], dtype=np.float64)
        probs = self.model.predict_proba(X)[0]
        classes = self.le.inverse_transform(self.model.classes_.astype(int))
        idx = int(np.argmax(probs))
        return {
            "type": classes[idx],
            "confidence": round(float(probs[idx]), 4),
            "all_probabilities": {c: round(float(p), 4) for c, p in zip(classes, probs)},
        }

    def save(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({
                "model": self.model,
                "le": self.le,
                "features": FEATURE_NAMES,
                "feature_importances": self.feature_importances_,
            }, f)

    def load(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                data = pickle.load(f)
            self.model = data["model"]
            self.le = data.get("le", LabelEncoder())
            self.feature_importances_ = data.get("feature_importances")
            self.is_trained = True
