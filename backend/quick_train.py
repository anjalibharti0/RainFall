"""Quick train from saved CSV."""
import sys, os, time, json
sys.path.insert(0, ".")
import pandas as pd

df = pd.read_csv("training_data_v2.csv")
print(f"Loaded: {len(df)} rows, {df['date'].nunique()} dates, {df['district_id'].nunique()} districts")
print(f"Regime distribution:\n{df['regime'].value_counts()}\n")

from ml.model_registry import ModelRegistry
registry = ModelRegistry()

t0 = time.time()
was_retrained, version = registry.retrain_if_needed(df, force=True)
elapsed = time.time() - t0

meta = version.load_metadata()
metrics = meta.get("metrics", {})
print(f"\nTraining completed in {elapsed:.1f}s")
print(f"Version: {version.version_name}")
print(f"Regime accuracy: {metrics.get('regime_accuracy', 'N/A')}")
print(f"Raw RMSE: {metrics.get('raw_rmse', 'N/A')}")
print(f"Corrected RMSE: {metrics.get('corrected_rmse', 'N/A')}")
print(f"RMSE improvement: {metrics.get('rmse_improvement_pct', 'N/A')}%")

registry.set_latest(version.version_name)
print(f"Set {version.version_name} as latest")
