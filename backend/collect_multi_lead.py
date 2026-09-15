"""Forward multi-lead collector.

The ONLY source of genuine multi-lead forecasts (real GFS skill degradation) is the
current Open-Meteo model run: fetching today's run for valid dates today+1/+2/+3 gives
true T+24/T+48/T+72 predictions for those dates. Reanalysis/archive never contains
lead-varying data (verified: Open-Meteo `past_days` returns archive-identical values).

Each day this script is run it archives, for every district:
    run_date   = the day the model run was issued
    valid_date = the date the forecast is valid (run_date + 1/2/3)
    lead_time  = 24 / 48 / 72

Rows are appended to multi_lead/rows.csv (idempotent: (run_date, valid_date,
district_id, lead_time) is skipped if already present). Once IMD observations for a
valid_date are published, retrain_multi_lead.py joins them in and trains models that
actually learn lead-time dependence.

Usage:
    python collect_multi_lead.py [YYYY-MM-DD]   # default: today
"""
import sys
import os
import json
import time
import argparse
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.all_districts import DISTRICTS
from ml.data_loader import RealDataLoader
from ml.weather_api import ALL_HOURLY, fetch_open_meteo, compute_ml_features_v2

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "multi_lead")
ROWS_CSV = os.path.join(ARCHIVE_DIR, "rows.csv")

MODEL = "gfs_seamless"


def fetch_forecast_window(lat, lon, run_date):
    """Fetch the current run's daily forecast for run_date+1..run_date+3."""
    import requests
    start = (run_date + timedelta(days=1)).isoformat()
    end = (run_date + timedelta(days=3)).isoformat()
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ",".join([
            "precipitation_sum", "temperature_2m_max", "temperature_2m_min",
            "wind_speed_10m_max", "wind_direction_10m_dominant",
            "cape_mean", "surface_pressure_mean", "shortwave_radiation_sum",
        ]),
        "timezone": "Asia/Kolkata",
        "model": MODEL,
        "start_date": start,
        "end_date": end,
    }
    resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def run_date_valid_dates():
    """Today. (We only archive genuine future-run forecasts; the past is reanalysis.)"""
    return date.today()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_date", nargs="?", default=None,
                        help="Model run date (YYYY-MM-DD). Default: today.")
    parser.add_argument("--districts-file", default=None,
                        help="Optional path to a district list JSON (debug).")
    args = parser.parse_args()

    run = datetime.strptime(args.run_date, "%Y-%m-%d").date() if args.run_date else run_date_valid_dates()
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    existing = set()
    if os.path.exists(ROWS_CSV):
        prev = pd.read_csv(ROWS_CSV, dtype={"district_id": int})
        existing = set(zip(prev["run_date"], prev["valid_date"], prev["district_id"], prev["lead_time"]))

    loader = RealDataLoader()
    districts = DISTRICTS

    new_rows = []
    failed = 0
    batch_size = 40
    for i in range(0, len(districts), batch_size):
        batch = districts[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(fetch_forecast_window, d["centroid_lat"], d["centroid_lon"], run): d
                       for d in batch}
            for f in as_completed(futures):
                d = futures[f]
                try:
                    data = f.result()
                except Exception:
                    failed += 1
                    continue
                if "daily" not in data:
                    continue
                daily = data["daily"]
                times = daily.get("time", [])
                for j, valid in enumerate(times):
                    lead = (datetime.strptime(valid, "%Y-%m-%d").date() - run).days * 24
                    if lead not in (24, 48, 72):
                        continue
                    if (run.isoformat(), valid, d["district_id"], lead) in existing:
                        continue
                    point = {"lat": d["centroid_lat"], "lon": d["centroid_lon"]}
                    for key in ["precipitation_sum", "temperature_2m_max", "temperature_2m_min",
                                "wind_speed_10m_max", "wind_direction_10m_dominant",
                                "cape_mean", "surface_pressure_mean", "shortwave_radiation_sum"]:
                        vals = daily.get(key, [])
                        point[key] = vals[j] if j < len(vals) else None
                    features = loader.compute_ml_features(point, valid.replace("-", ""))
                    regime, conf = loader.label_regime(features)
                    new_rows.append({
                        "run_date": run.isoformat(),
                        "valid_date": valid,
                        "district_id": d["district_id"],
                        "name": d.get("district_name", ""),
                        "state": d.get("state_name", ""),
                        "zone": d.get("zone", "central"),
                        "lat": d["centroid_lat"],
                        "lon": d["centroid_lon"],
                        "lead_time": lead,
                        "regime": regime,
                        "regime_confidence": round(conf, 4),
                        **features,
                    })
        time.sleep(0.4)

    if new_rows:
        df = pd.DataFrame(new_rows)
        if os.path.exists(ROWS_CSV):
            df.to_csv(ROWS_CSV, mode="a", header=False, index=False)
        else:
            df.to_csv(ROWS_CSV, index=False)
        print(f"run_date={run.isoformat()} appended {len(df)} new rows -> {ROWS_CSV}")
    else:
        print(f"run_date={run.isoformat()} nothing new (already archived or fetch failed).")

    if failed:
        print(f"WARNING: {failed} district fetches failed.")

    total = pd.read_csv(ROWS_CSV) if os.path.exists(ROWS_CSV) else pd.DataFrame()
    if len(total):
        print(f"Archive total: {len(total)} rows | leads: {total['lead_time'].value_counts().to_dict()}"
              f" | run dates: {sorted(total['run_date'].unique())}")
        vc = total.groupby(["lead_time", "valid_date"]).size()
        sample = vc.loc[[24, 48, 72]] if len(vc) else None
        if sample is not None:
            print("Rows per (lead, valid_date), first 3 valid dates:")
            for lt in (24, 48, 72):
                print(f"  T+{lt}: {sample.loc[lt].head(3).to_dict()}")


if __name__ == "__main__":
    main()