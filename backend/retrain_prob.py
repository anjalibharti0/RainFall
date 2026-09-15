"""Train v14: reuses v13 regime/bias/dry_wet models, swaps in the new probability estimator.
Isolates the probability-model change for a clean A/B."""
import sys, os, json
import pandas as pd
import numpy as np
sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.model_registry import ModelRegistry, ModelVersion, MODELS_DIR
from ml.regime_classifier import RegimeClassifier
from ml.bias_corrector import BiasCorrector
from ml.probability_estimator import ProbabilityEstimator
from ml.dry_wet_model import DryWetModel

df = pd.read_csv("training_data_v3.csv")
print(f"df: {len(df)} rows, {df['date'].nunique()} dates")

v13 = ModelVersion(os.path.join(MODELS_DIR, "v13"))
rc, bc, pe_old, dw = RegimeClassifier(), BiasCorrector(), ProbabilityEstimator(), DryWetModel()
v13.load_models(rc, bc, pe_old, dw)
print("Loaded v13 models.")

print("\n=== Training NEW probability estimator ===")
pe = ProbabilityEstimator()
t0 = __import__("time").time()
results = pe.train(df)
print(f"  trained in {__import__('time').time()-t0:.0f}s")

print("\n=== Old v13 vs NEW v14 vs climatology (Brier, held-out dates) ===")
for th, meta in results.items():
    old_meta = pe_old.metrics_.get(th, {})
    print(f"  p>={float(th):>6}: v13_brier={old_meta.get('brier')}  v14_brier={meta['brier']}  clim={meta['clim_brier']}  "
          f"base={meta['base_rate']}  mean_p={meta['mean_prob']}  auc={meta.get('auc')}")

registry = ModelRegistry()
v14 = registry.create_version("v14")
print(f"\nSaving {v14.version_name}...")

dates = sorted(df["date"].unique())
metrics = v14.compute_metrics_on_dataset(df, rc, bc, dw)
metrics["regime_classifier"] = rc.metrics_ if hasattr(rc, "metrics_") else {}
metrics["bias_corrector"] = bc.metrics_
metrics["probability_estimator"] = results
metrics["dry_wet_model"] = dw.metrics_

training_info = {
    "train_dates": f"{df['date'].min()} to {df['date'].max()}",
    "n_districts": int(df["district_id"].nunique()),
    "n_dates": int(df["date"].nunique()),
    "regime_distribution": df["regime"].value_counts().to_dict(),
}

import hashlib
content = f"{len(df)}_{df.columns.tolist()}_{df['regime'].value_counts().to_dict()}"
dataset_hash = hashlib.md5(content.encode()).hexdigest()[:12]

v14.save_models(rc, bc, pe, dw, metadata={
    "metrics": metrics,
    "training_info": training_info,
    "dataset_hash": dataset_hash,
    "n_samples": len(df),
})
registry.set_latest("v14")
print("latest -> v14")
print(f"Overall corrected_rmse={metrics.get('corrected_rmse')}, r2={metrics.get('corrected_r2')} (identical to v13 by design)")