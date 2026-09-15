"""Retrain on 3-year dataset (training_data_v3.csv) as v12.
A/B validates v12 vs v11 on the *same* temporally held-out dates."""
import sys, os
import pandas as pd
import numpy as np
sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.model_registry import ModelRegistry, ModelVersion, MODELS_DIR
from ml.regime_classifier import RegimeClassifier
from ml.bias_corrector import BiasCorrector
from ml.probability_estimator import ProbabilityEstimator
from ml.dry_wet_model import DryWetModel

KEEP = [
    "date", "district_id", "name", "state", "zone", "lat", "lon",
    "raw_rainfall", "observed_rainfall", "regime", "regime_confidence", "lead_time",
    "wind_speed", "wind_dir", "cape", "pressure", "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase", "is_peak_monsoon", "latitude", "longitude",
    "p_exceed_7.5", "p_exceed_64.5", "p_exceed_124.5", "p_exceed_244.5",
]

print("Loading training_data_v3.csv...")
df = pd.read_csv("training_data_v3.csv")
df = df[[c for c in KEEP if c in df.columns]]
print(f"Rows: {len(df)}, dates: {df['date'].nunique()}, districts: {df['district_id'].nunique()}")
print(f"Range: {df['date'].min()} -> {df['date'].max()}")

registry = ModelRegistry()
print("\n=== Training v12 on 3-year dataset ===")
retrained, v12 = registry.retrain_if_needed(df, force=True)
print(f"\nv12 created: {v12.version_name}")

# Fixed held-out eval split: last 20% of all dates (identical for both models)
dates = sorted(df["date"].unique())
split_idx = int(len(dates) * 0.8)
test_dates = set(dates[split_idx:])
eval_df = df[df["date"].isin(test_dates)].copy()
print(f"\nShared eval split: {len(test_dates)} dates ({min(test_dates)} -> {max(test_dates)}), {len(eval_df)} rows")

def load_models(version_name):
    v = ModelVersion(os.path.join(MODELS_DIR, version_name))
    rc = RegimeClassifier()
    bc = BiasCorrector()
    pe = ProbabilityEstimator()
    dw = DryWetModel()
    ok = v.load_models(rc, bc, pe, dw)
    return (rc, bc, pe, dw) if ok else (None, None, None, None)

def compare(version_name):
    rc, bc, pe, dw = load_models(version_name)
    if rc is None:
        return {}
    m = ModelVersion(os.path.join(MODELS_DIR, version_name))
    return m.compute_metrics_on_dataset(eval_df, rc, bc, dw)

print("\n=== A/B on identical held-out dates ===")
old = compare("v12")
new = compare(v12.version_name)
for k in ["regime_accuracy", "raw_rmse", "raw_r2", "corrected_rmse", "corrected_r2", "corrected_mae", "rmse_improvement_pct"]:
    print(f"  {k:>22}: v12={old.get(k)}   {v12.version_name}={new.get(k)}")
if "wet_hurdle" in new:
    print(f"  {'wet_hurdle':>22}: v12=n/a   {v12.version_name}={new['wet_hurdle']}")

print("\n=== Per-regime corrected metrics ===")
bc = load_models(v12.version_name)[1]
for regime, met in bc.metrics_.items():
    print(f"  {regime:>22}: rmse={met['rmse']}, r2={met['r2']}, n={met['n_samples']}")

print("\n=== Probability estimator metrics (v12/v13) ===")
pe13 = load_models(v12.version_name)[2]
for th, met in pe13.metrics_.items():
    print(f"  p>={th:>6}: mse={met['mse']}, brier={met['brier']}, n_test={met['n_test']}")

print("\n=== Dry/wet hurdle model (v13) ===")
dw13 = load_models(v12.version_name)[3]
print(f"  {dw13.metrics_}")

meta = v12.load_metadata()
print(f"\nSaved: {v12.version_name} | n_samples={meta.get('n_samples')} | hash={meta.get('dataset_hash')}")
print(f"latest -> {registry.get_latest_version().version_name}")