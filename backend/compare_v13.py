"""Authoritative A/B: v12 (no hurdle) vs v13 (hurdle) on identical internal temporal split."""
import sys, os
import pandas as pd
sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.model_registry import ModelRegistry, ModelVersion, MODELS_DIR
from ml.regime_classifier import RegimeClassifier
from ml.bias_corrector import BiasCorrector
from ml.probability_estimator import ProbabilityEstimator
from ml.dry_wet_model import DryWetModel

df = pd.read_csv("training_data_v3.csv")
print(f"Full df: {len(df)} rows, {df['date'].nunique()} dates")

def load(version_name):
    v = ModelVersion(os.path.join(MODELS_DIR, version_name))
    rc, bc, pe, dw = RegimeClassifier(), BiasCorrector(), ProbabilityEstimator(), DryWetModel()
    v.load_models(rc, bc, pe, dw)
    return v, rc, bc, pe, dw

v12, rc12, bc12, _, _ = load("v12")
v13, v13_rclf, v13_bc, _, dw13 = load("v13")

print("\n=== Internal temporal split on FULL df (identical for both) ===")
m12 = v12.compute_metrics_on_dataset(df, rc12, bc12, None)
m13 = v13.compute_metrics_on_dataset(df, v13_rclf, v13_bc, dw13)
for k in ["eval_dates", "eval_rows", "regime_accuracy", "corrected_rmse", "corrected_r2", "corrected_mae", "rmse_improvement_pct"]:
    print(f"  {k:>20}: v12={m12.get(k)}   v13={m13.get(k)}")
print(f"  {'wet_hurdle':>20}: v12=off   v13={m13.get('wet_hurdle')}")
print(f"  {'dry_wet_auc':>20}: v12=n/a   v13={dw13.metrics_.get('auc')}")