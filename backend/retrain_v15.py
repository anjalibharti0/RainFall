"""v15: Class-imbalance fix - balanced sample weights + macro-F1 model selection
for the regime classifier. A/B against v14 on the SAME temporally held-out dates."""
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
print("\n=== Training v15 (balanced regime classifier) ===")
retrained, v = registry.retrain_if_needed(df, force=True)
print(f"\nCreated: {v.version_name}")

dates = sorted(df["date"].unique())
split_idx = int(len(dates) * 0.8)
test_dates = set(dates[split_idx:])
eval_df = df[df["date"].isin(test_dates)].copy()
print(f"\nShared eval split: {len(test_dates)} dates ({min(test_dates)} -> {max(test_dates)}), {len(eval_df)} rows")


def load_models(version_name):
    vdir = os.path.join(MODELS_DIR, version_name)
    mv = ModelVersion(vdir)
    rc = RegimeClassifier()
    bc = BiasCorrector()
    pe = ProbabilityEstimator()
    dw = DryWetModel()
    ok = mv.load_models(rc, bc, pe, dw)
    return (rc, bc, pe, dw) if ok else (None, None, None, None)


def abl(version_name):
    rc, bc, pe, dw = load_models(version_name)
    if rc is None:
        return {}
    mv = ModelVersion(os.path.join(MODELS_DIR, version_name))
    out = mv.compute_metrics_on_dataset(eval_df, rc, bc, dw)
    rc_labels = [f for f in rc._feature_names if f in eval_df.columns]
    X = eval_df[rc_labels].values.astype(np.float64)
    y_true = eval_df["regime"].values
    y_pred = rc.le.inverse_transform(rc.model.predict(X).astype(int))
    from sklearn.metrics import classification_report, f1_score, balanced_accuracy_score
    rep = classification_report(y_true, y_pred, output_dict=True)
    out["macro_f1"] = round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4)
    out["balanced_acc"] = round(balanced_accuracy_score(y_true, y_pred), 4)
    class_f1 = {}
    class_recall = {}
    for c in ["active_monsoon", "break_monsoon", "depression", "coastal", "orographic", "western_disturbance"]:
        r = rep.get(c)
        class_f1[c] = round(r["f1-score"], 4) if r else None
        class_recall[c] = round(r["recall"], 4) if r else None
    out["class_f1"] = class_f1
    out["class_recall"] = class_recall
    return out


print("\n=== A/B on identical held-out dates ===")
old = abl("v14")
new = abl(v.version_name)
print(f"{'metric':>22}  {'v14':>10}  {v.version_name:>10}")
for k in ["regime_accuracy", "balanced_acc", "macro_f1", "raw_rmse", "corrected_rmse", "corrected_mae",
          "corrected_r2", "rmse_improvement_pct"]:
    print(f"  {k:>22}: {old.get(k)}    {new.get(k)}")
if "wet_hurdle" in new:
    print(f"  {'wet_hurdle':>22}: n/a    {new['wet_hurdle']}")

print("\n=== Per-class F1 (recall) ===")
print(f"  {'class':>22}: {'v14 f1':>10} {'v15 f1':>10} | {'v14 rec':>8} {'v15 rec':>8}")
for c in ["depression", "active_monsoon", "break_monsoon", "coastal", "orographic", "western_disturbance"]:
    print(f"  {c:>22}: {old['class_f1'][c]:>10} {new['class_f1'][c]:>10} | "
          f"{old['class_recall'][c]:>8} {new['class_recall'][c]:>8}")

meta = v.load_metadata()
print(f"\nSaved: {v.version_name} | n_samples={meta.get('n_samples')} | hash={meta.get('dataset_hash')}")
print(f"latest -> {registry.get_latest_version().version_name}")