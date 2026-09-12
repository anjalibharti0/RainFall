"""
Download GFS historical forecast data for NWD from Open-Meteo.
Free, no login, covers 2022-present.

Run: python download_gfs.py --start 2024-01-01 --end 2026-09-12
"""
import os
import json
import time
import requests
import urllib3
import argparse
import numpy as np
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NWD = {"lat_min": 20, "lat_max": 37.5, "lon_min": 65, "lon_max": 80}
NWD_LATS = np.arange(NWD["lat_max"], NWD["lat_min"] - 0.25, -0.25).round(4).tolist()
NWD_LONS = np.arange(NWD["lon_min"], NWD["lon_max"] + 0.25, 0.25).round(4).tolist()

API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
DAILY_VARS = "precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_direction_10m_dominant,cape_mean,surface_pressure_mean,shortwave_radiation_sum"


def download_batch(lat_batch, lon_batch, start_date, end_date, output_file, retries=5):
    """Download a batch of grid points with retry on rate limit."""
    params = {
        "latitude": ",".join(str(l) for l in lat_batch),
        "longitude": ",".join(str(l) for l in lon_batch),
        "start_date": start_date,
        "end_date": end_date,
        "daily": DAILY_VARS,
        "models": "gfs_seamless",
        "timezone": "Asia/Kolkata",
    }
    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, timeout=120, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                with open(output_file, "w") as f:
                    json.dump(data, f)
                return True, len(data) if isinstance(data, list) else 1
            elif resp.status_code == 429:
                wait = 15 * (2 ** attempt)  # 15, 30, 60, 120, 240
                print("(rate limited, wait {}s)".format(wait), end=" ", flush=True)
                time.sleep(wait)
                continue
            return False, "HTTP {}".format(resp.status_code)
        except Exception as e:
            return False, str(e)[:80]
    return False, "Max retries (429)"


def download_gfs(start_date, end_date, data_dir="nwp_data"):
    os.makedirs(data_dir, exist_ok=True)

    all_points = [(lat, lon) for lat in NWD_LATS for lon in NWD_LONS]
    batch_size = 20
    batches = [all_points[i:i + batch_size] for i in range(0, len(all_points), batch_size)]

    print(f"NWD grid: {len(NWD_LATS)} x {len(NWD_LONS)} = {len(all_points)} points")
    print(f"Batches: {len(batches)} (of {batch_size})")
    print(f"Range: {start_date} to {end_date}")
    print()

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    current_year = start.year
    while current_year <= end.year:
        year_start = max(start, datetime(current_year, 1, 1))
        year_end = min(end, datetime(current_year, 12, 31))
        year_dir = os.path.join(data_dir, str(current_year))
        os.makedirs(year_dir, exist_ok=True)

        sd = year_start.strftime("%Y-%m-%d")
        ed = year_end.strftime("%Y-%m-%d")

        print(f"--- {current_year} ({sd} to {ed}) ---")

        for i, batch in enumerate(batches):
            lats = [p[0] for p in batch]
            lons = [p[1] for p in batch]
            outfile = os.path.join(year_dir, f"batch_{i:03d}.json")

            if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
                continue

            print(f"  Batch {i+1}/{len(batches)}...", end=" ", flush=True)
            ok, result = download_batch(lats, lons, sd, ed, outfile)

            if ok:
                print(f"OK ({result} locs)")
            else:
                print(f"FAIL: {result}")

            time.sleep(8)  # Rate limit - be gentle

        current_year += 1

    print("\nDONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GFS NWD data")
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2026-09-12")
    parser.add_argument("--dir", default="nwp_data")
    args = parser.parse_args()

    download_gfs(args.start, args.end, args.dir)
