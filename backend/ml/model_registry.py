"""
Model versioning, metadata tracking, and retraining pipeline.
V2: Fixed verification metrics, proper model evaluation.

Directory structure:
    trained_models/
    ├── v1/
    │   ├── regime_classifier.pkl
    │   ├── bias_corrector.pkl
    │   ├── probability_estimator.pkl
    │   └── metadata.json
    ├── v2/
    └── latest -> v2
"""

import os
import json
import pickle
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.metrics import (
    accuracy_score, classification_report, mean_squared_error,
    mean_absolute_error, r2_score
)


MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trained_models")


def _hash_dataset(df):
    content = f"{len(df)}_{df.columns.tolist()}_{df['regime'].value_counts().to_dict()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


class ModelVersion:
    def __init__(self, version_dir):
        self.version_dir = version_dir
        self.version_name = os.path.basename(version_dir)
        self.metadata_path = os.path.join(version_dir, "metadata.json")

    def exists(self):
        return os.path.isdir(self.version_dir)

    def has_models(self):
        return all(
            os.path.exists(os.path.join(self.version_dir, f))
            for f in ["regime_classifier.pkl", "bias_corrector.pkl", "probability_estimator.pkl"]
        )

    def save_models(self, regime_clf, bias_corrector, prob_estimator, dry_wet=None, metadata=None):
        os.makedirs(self.version_dir, exist_ok=True)

        with open(os.path.join(self.version_dir, "regime_classifier.pkl"), "wb") as f:
            pickle.dump({
                "model": regime_clf.model,
                "le": regime_clf.le,
                "features": regime_clf._feature_names,
                "feature_importances": regime_clf.feature_importances_,
            }, f)

        with open(os.path.join(self.version_dir, "bias_corrector.pkl"), "wb") as f:
            pickle.dump({"correctors": bias_corrector.correctors, "metrics": bias_corrector.metrics_}, f)

        with open(os.path.join(self.version_dir, "probability_estimator.pkl"), "wb") as f:
            pickle.dump({"models": prob_estimator.models, "metrics": prob_estimator.metrics_}, f)

        if dry_wet is not None:
            with open(os.path.join(self.version_dir, "dry_wet_model.pkl"), "wb") as f:
                pickle.dump({
                    "model": dry_wet.model,
                    "metrics": dry_wet.metrics_,
                    "wet_rate": dry_wet.wet_rate,
                    "zero_threshold": dry_wet.zero_threshold,
                    "features": dry_wet._feature_names,
                }, f)

        meta = {
            "version": self.version_name,
            "created_at": datetime.now().isoformat(),
            "metrics": metadata.get("metrics", {}) if metadata else {},
            "training_info": metadata.get("training_info", {}) if metadata else {},
            "dataset_hash": metadata.get("dataset_hash", "") if metadata else "",
            "n_samples": metadata.get("n_samples", 0) if metadata else 0,
        }
        with open(self.metadata_path, "w") as f:
            json.dump(meta, f, indent=2)

    def load_models(self, regime_clf, bias_corrector, prob_estimator, dry_wet=None):
        rc_path = os.path.join(self.version_dir, "regime_classifier.pkl")
        bc_path = os.path.join(self.version_dir, "bias_corrector.pkl")
        pe_path = os.path.join(self.version_dir, "probability_estimator.pkl")

        if not all(os.path.exists(p) for p in [rc_path, bc_path, pe_path]):
            return False

        with open(rc_path, "rb") as f:
            data = pickle.load(f)
        regime_clf.model = data["model"]
        regime_clf.le = data.get("le", regime_clf.le)
        regime_clf._feature_names = data.get("features", regime_clf._feature_names)
        regime_clf.feature_importances_ = data.get("feature_importances")
        regime_clf.is_trained = True

        with open(bc_path, "rb") as f:
            data = pickle.load(f)
        bias_corrector.correctors = data["correctors"]
        bias_corrector.metrics_ = data.get("metrics", {})
        bias_corrector.is_trained = True

        with open(pe_path, "rb") as f:
            data = pickle.load(f)
        prob_estimator.models = data["models"]
        prob_estimator.metrics_ = data.get("metrics", {})
        prob_estimator.is_trained = True

        if dry_wet is not None:
            dw_path = os.path.join(self.version_dir, "dry_wet_model.pkl")
            if os.path.exists(dw_path):
                from ml.dry_wet_model import DryWetModel
                with open(dw_path, "rb") as f:
                    data = pickle.load(f)
                dry_wet.model = data["model"]
                dry_wet.metrics_ = data.get("metrics", {})
                dry_wet.wet_rate = data.get("wet_rate", 0.0)
                dry_wet.zero_threshold = data.get("zero_threshold", 0.5)
                dry_wet._feature_names = data.get("features", dry_wet._feature_names)
                dry_wet.is_trained = True

        return True

    def load_metadata(self):
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path) as f:
                return json.load(f)
        return {}

    def compute_metrics_on_dataset(self, df, regime_clf=None, bias_corrector=None, dry_wet=None):
        """Compute verification metrics on temporally held-out dates (last 20%)."""
        metrics = {}
        all_feature_cols = [c for c in [
            "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
            "radiation", "temp_range", "temp_mean",
            "day_of_year", "month", "monsoon_phase",
            "is_peak_monsoon", "latitude", "longitude",
            "lead_time",
        ] if c in df.columns]

        if "date" in df.columns and len(df["date"].unique()) > 5:
            dates = sorted(df["date"].unique())
            split_idx = int(len(dates) * 0.8)
            test_dates = set(dates[split_idx:])
            eval_df = df[df["date"].isin(test_dates)].copy()
            metrics["eval_split"] = "temporal"
            metrics["eval_dates"] = len(test_dates)
            metrics["eval_rows"] = len(eval_df)
        else:
            eval_df = df.copy()
            metrics["eval_split"] = "full"

        if regime_clf and regime_clf.is_trained and len(eval_df) > 0:
            rc_features = [f for f in regime_clf._feature_names if f in eval_df.columns]
            X = eval_df[rc_features].values.astype(np.float64)
            y_true = eval_df["regime"].values
            try:
                y_pred_enc = regime_clf.model.predict(X)
                y_pred = regime_clf.le.inverse_transform(y_pred_enc.astype(int))
                metrics["regime_accuracy"] = round(accuracy_score(y_true, y_pred), 4)
                metrics["regime_report"] = classification_report(y_true, y_pred, output_dict=True)
            except Exception:
                metrics["regime_accuracy"] = 0

        if "observed_rainfall" in eval_df.columns and "raw_rainfall" in eval_df.columns:
            raw_rmse = float(np.sqrt(mean_squared_error(eval_df["observed_rainfall"], eval_df["raw_rainfall"])))
            raw_mae = float(mean_absolute_error(eval_df["observed_rainfall"], eval_df["raw_rainfall"]))
            raw_r2 = r2_score(eval_df["observed_rainfall"], eval_df["raw_rainfall"])
            metrics["raw_rmse"] = round(raw_rmse, 2)
            metrics["raw_mae"] = round(raw_mae, 2)
            metrics["raw_r2"] = round(raw_r2, 4)

            if bias_corrector and bias_corrector.is_trained:
                preds = np.zeros(len(eval_df))
                bc_features = [f for f in all_feature_cols if f in eval_df.columns]
                for regime, model in bias_corrector.correctors.items():
                    mask = eval_df["regime"] == regime
                    if mask.sum() == 0:
                        continue
                    X_r = eval_df.loc[mask, bc_features].values.astype(np.float64)
                    preds[mask.values] = model.predict(X_r)

                if dry_wet is not None and dry_wet.is_trained and dry_wet.model is not None:
                    dw_features = [f for f in dry_wet._feature_names if f in eval_df.columns]
                    if len(dw_features) == len(dry_wet._feature_names):
                        X_w = eval_df[dry_wet._feature_names].values.astype(np.float64)
                        wet_prob = dry_wet.model.predict_proba(X_w)[:, 1]
                        zero_mask = (eval_df["raw_rainfall"].values < 2.0) & (wet_prob < dry_wet.zero_threshold)
                        n_zeroed = int(zero_mask.sum())
                        preds = np.where(zero_mask, 0.0, preds)
                        metrics["wet_hurdle"] = {
                            "zero_threshold": dry_wet.zero_threshold,
                            "raw_gate_mm": 2.0,
                            "pct_zeroed": round(n_zeroed / len(eval_df) * 100, 1),
                        }

                corr_rmse = float(np.sqrt(mean_squared_error(eval_df["observed_rainfall"], preds)))
                corr_mae = float(mean_absolute_error(eval_df["observed_rainfall"], preds))
                corr_r2 = r2_score(eval_df["observed_rainfall"], preds)
                metrics["corrected_rmse"] = round(corr_rmse, 2)
                metrics["corrected_mae"] = round(corr_mae, 2)
                metrics["corrected_r2"] = round(corr_r2, 4)
                metrics["rmse_improvement_pct"] = round((1 - corr_rmse / raw_rmse) * 100, 1) if raw_rmse > 0 else 0

        return metrics


class ModelRegistry:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or MODELS_DIR
        os.makedirs(self.base_dir, exist_ok=True)
        self._versions_cache = None

    def list_versions(self):
        if self._versions_cache:
            return self._versions_cache
        versions = []
        for name in sorted(os.listdir(self.base_dir)):
            vdir = os.path.join(self.base_dir, name)
            if os.path.isdir(vdir) and name.startswith("v"):
                mv = ModelVersion(vdir)
                if mv.has_models():
                    versions.append(mv)
        self._versions_cache = versions
        return versions

    def get_latest_version(self):
        pointer_file = os.path.join(self.base_dir, "latest")
        if os.path.exists(pointer_file):
            with open(pointer_file) as f:
                latest_name = f.read().strip()
            vdir = os.path.join(self.base_dir, latest_name)
            mv = ModelVersion(vdir)
            if mv.has_models():
                return mv

        versions = self.list_versions()
        if versions:
            return versions[-1]
        return None

    def create_version(self, version_name=None):
        if version_name is None:
            existing = self.list_versions()
            next_num = len(existing) + 1
            version_name = f"v{next_num}"
        vdir = os.path.join(self.base_dir, version_name)
        return ModelVersion(vdir)

    def set_latest(self, version_name):
        pointer_file = os.path.join(self.base_dir, "latest")
        with open(pointer_file, "w") as f:
            f.write(version_name)
        self._versions_cache = None

    def retrain_if_needed(self, df, force=False):
        from ml.regime_classifier import RegimeClassifier
        from ml.bias_corrector import BiasCorrector
        from ml.probability_estimator import ProbabilityEstimator
        from ml.dry_wet_model import DryWetModel

        latest = self.get_latest_version()
        dataset_hash = _hash_dataset(df)

        if not force and latest:
            meta = latest.load_metadata()
            old_hash = meta.get("dataset_hash", "")
            old_n = meta.get("n_samples", 0)
            new_n = len(df)

            if old_hash == dataset_hash:
                print(f"Models up to date (same dataset hash: {dataset_hash})")
                return False, latest

            if old_n > 0 and new_n < old_n * 1.2:
                print(f"Dataset growth insufficient ({old_n} -> {new_n} samples, need >20% increase)")
                return False, latest

        new_version = self.create_version()
        print(f"Training models in {new_version.version_name}...")

        regime_clf = RegimeClassifier()
        bias_corrector = BiasCorrector()
        prob_estimator = ProbabilityEstimator()
        dry_wet = DryWetModel()

        print("  Training regime classifier...")
        clf_results = regime_clf.train(df)

        print("  Training bias correctors...")
        bc_results = bias_corrector.train(df)

        print("  Training probability estimators...")
        pe_results = prob_estimator.train(df)

        print("  Training dry/wet hurdle model...")
        dw_results = dry_wet.train(df)

        print("  Computing verification metrics...")
        metrics = new_version.compute_metrics_on_dataset(df, regime_clf, bias_corrector, dry_wet)
        metrics["regime_classifier"] = clf_results
        metrics["bias_corrector"] = bc_results
        metrics["probability_estimator"] = pe_results
        metrics["dry_wet_model"] = dw_results

        training_info = {
            "train_dates": f"{df['date'].min()} to {df['date'].max()}" if "date" in df.columns else "unknown",
            "n_districts": df["district_id"].nunique() if "district_id" in df.columns else 0,
            "n_dates": df["date"].nunique() if "date" in df.columns else 0,
            "regime_distribution": df["regime"].value_counts().to_dict() if "regime" in df.columns else {},
        }

        new_version.save_models(regime_clf, bias_corrector, prob_estimator, dry_wet, metadata={
            "metrics": metrics,
            "training_info": training_info,
            "dataset_hash": dataset_hash,
            "n_samples": len(df),
        })
        self.set_latest(new_version.version_name)

        print(f"  Saved to {new_version.version_name}")
        print(f"  Regime accuracy: {metrics.get('regime_accuracy', 'N/A')}")
        print(f"  Raw RMSE: {metrics.get('raw_rmse', 'N/A')}")
        print(f"  Corrected RMSE: {metrics.get('corrected_rmse', 'N/A')}")
        print(f"  RMSE improvement: {metrics.get('rmse_improvement_pct', 'N/A')}%")

        return True, new_version

    def get_comparison_table(self):
        rows = []
        for v in self.list_versions():
            meta = v.load_metadata()
            row = {
                "version": v.version_name,
                "created": meta.get("created_at", "unknown"),
                "n_samples": meta.get("n_samples", 0),
                "dataset_hash": meta.get("dataset_hash", ""),
            }
            metrics = meta.get("metrics", {})
            if isinstance(metrics, dict):
                for k, val in metrics.items():
                    if not isinstance(val, dict):
                        row[k] = val
            rows.append(row)
        return rows
