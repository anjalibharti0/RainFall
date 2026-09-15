"""Rebuild a multi-lead training set from the forward collector archive and retrain.

Joins multi_lead/rows.csv forecasts against IMD observations for their valid_date.
Because the archive is collected daily from genuine model runs, each valid date ends
up with THREE rows (T+24, T+48, T+72) at different lead times with real skill variance.

Data sources can be combined:
  - `--archive` : multi_lead/rows.csv (real multi-lead, going forward)
  - `--legacy`  : training_data_v3.csv (2022-2025 reanalysis-matched pairs, lead 24)

Once an archive row has an observed value, it becomes a training row whose lead_time
feature is real and varying -> models can finally learn lead dependence.

Usage:
    python retrain_multi_lead.py                          # archive only
    python retrain_multi_lead.py --legacy                 # archive + v3 rows
    python retrain_multi_lead.py --check                  # just show matched/obs coverage
"""
import sys
import os
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.data_loader import RealDataLoader
from ml.model_registry import ModelRegistry
from ml.dry_wet_model import DryWetModel

MODELS_DIR = os.path.join(os.path.dirname(__file__), "trained_models")
ARCHIVE = os.path.join(os.path.dirname(__file__), "multi_lead", "rows.csv")

KEEP = [
    "date", "district_id", "name", "state", "zone", "lat", "lon",
    "raw_rainfall", "observed_rainfall", "regime", "regime_confidence", "lead_time",
    "wind_speed", "wind_dir", "cape", "pressure", "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase", "is_peak_monsoon", "latitude", "longitude",
]


def load_archive(loader, archive_path):
    if not os.path.exists(archive_path):
        print(f"No archive at {archive_path} — nothing to do.")
        return None
    df = pd.read_csv(archive_path)
    if not len(df):
        return None

    valid_dates = sorted(df["valid_date"].unique())
    obs_by_district_date = {}
    for v in valid_dates:
        yd = v.replace("-", "")
        dvals = loader.load_imd_for_districts(yd)
        if dvals:
            obs_by_district_date[v] = dvals

    df["observed_rainfall"] = np.nan
    matched = 0
    for v, dvals in obs_by_district_date.items():
        mask = df["valid_date"] == v
        for did, obs in dvals.items():
            subm = mask & (df["district_id"] == did)
            df.loc[subm, "observed_rainfall"] = obs
            matched += int(subm.sum())
    df = df[df["observed_rainfall"] >= 0].copy()
    print(f"Archive: {len(df)} rows matched to IMD obs ({matched} district-date obs)")

    if not len(df):
        return None
    df = df.rename(columns={"valid_date": "date"})
    return df[KEEP]


def eval_by_lead(registry, version, test_df):
    """Per-lead verification on the temporal holdout of the multi-lead set."""
    from ml.regime_classifier import RegimeClassifier
    from ml.bias_corrector import BiasCorrector
    from ml.probability_estimator import ProbabilityEstimator

    vdir = os.path.join(MODELS_DIR, version.version_name)
    from ml.model_registry import ModelVersion
    mv = ModelVersion(vdir)
    rc, bc, pe, dw = RegimeClassifier(), BiasCorrector(), ProbabilityEstimator(), DryWetModel()
    if not mv.load_models(rc, bc, pe, dw):
        print("  (could not load models for per-lead eval)")
        return

    out = []
    for lt, g in test_df.groupby("lead_time"):
        if len(g) < 5:
            continue
        preds = []
        for _, row in g.iterrows():
            feats = {
                "raw_rainfall": row["raw_rainfall"], "wind_speed": row["wind_speed"],
                "wind_dir": row["wind_dir"], "cape": row["cape"], "pressure": row["pressure"],
                "radiation": row["radiation"], "temp_range": row["temp_range"],
                "temp_mean": row["temp_mean"], "day_of_year": row["day_of_year"],
                "month": row["month"], "monsoon_phase": row["monsoon_phase"],
                "is_peak_monsoon": row["is_peak_monsoon"], "latitude": row["latitude"],
                "longitude": row["longitude"],
            }
            reg = {"type": row["regime"], "all_probabilities": {
                row["regime"]: max(row["regime_confidence"], 0.3),
                "active_monsoon": 0.5, "break_monsoon": 0.1, "depression": 0.1,
                "orographic": 0.2, "coastal": 0.05, "western_disturbance": 0.05}}
            wet = dw.predict_wet_prob(row["raw_rainfall"], feats, int(lt))
            corr = bc.predict_soft(row["raw_rainfall"], feats, reg["all_probabilities"], int(lt))
            if row["raw_rainfall"] < 2.0 and wet < dw.zero_threshold:
                corr = 0.0
            preds.append(corr)
        obs = g["observed_rainfall"].values
        preds = np.array(preds)
        rmse = float(np.sqrt(np.mean((obs - preds) ** 2)))
        raw_rmse = float(np.sqrt(np.mean((obs - g["raw_rainfall"].values) ** 2)))
        out.append({"lead": int(lt), "n": len(g),
                    "raw_rmse": round(raw_rmse, 2), "corrected_rmse": round(rmse, 2),
                    "bias": round(float(np.mean(preds - obs)), 2)})
    if out:
        print("  Per-lead corrected RMSE (temporal holdout):")
        for row in out:
            print(f"    T+{row['lead']}: n={row['n']:<5} raw_rmse={row['raw_rmse']:<7} "
                  f"corrected_rmse={row['corrected_rmse']:<7} bias={row['bias']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy", action="store_true", help="also include training_data_v3.csv")
    parser.add_argument("--check", action="store_true", help="report obs coverage and exit")
    parser.add_argument("--force", action="store_true", help="retrain even without 20% growth")
    args = parser.parse_args()

    loader = RealDataLoader()
    df = load_archive(loader, ARCHIVE)
    if df is None and not args.legacy:
        print("Nothing to train.")
        return

    if args.legacy:
        legacy = pd.read_csv("training_data_v3.csv")
        keep = [c for c in KEEP if c in legacy.columns]
        legacy = legacy[keep]
        if df is not None:
            df = pd.concat([df, legacy], ignore_index=True)
        else:
            df = legacy
        print(f"Combined with legacy v3: {len(df)} total rows")

    if df is None or not len(df):
        print("Nothing to train.")
        return

    print(f"Lead distribution: {df['lead_time'].value_counts().to_dict()}")
    print(f"Dates: {df['date'].min()} -> {df['date'].max()} | districts: {df['district_id'].nunique()}")

    if args.check:
        return

    registry = ModelRegistry()
    retrained, version = registry.retrain_if_needed(df, force=args.force)

    if args.legacy and not retrained and len(df) > 0:
        # mixed set: still report
        pass

    dates = sorted(df["date"].unique())
    split_idx = int(len(dates) * 0.8)
    test_dates = set(dates[split_idx:])
    test_df = df[df["date"].isin(test_dates)]
    if len(test_df):
        eval_by_lead(registry, version, test_df)


if __name__ == "__main__":
    main()