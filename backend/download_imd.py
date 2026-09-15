"""
Download IMD 0.25° gridded daily rainfall data (binary .grd format).
Source: IMD Pune via https://imdpune.gov.in/cmpg/Griddata/

Two modes:
  1. Yearly archive (2010-2024): downloads one .grd file per year
  2. Real-time daily (recent months): downloads one .grd file per day

Run:
    python download_imd.py --mode yearly --start 2022 --end 2024
    python download_imd.py --mode realtime --start 2024-06-01 --end 2024-09-30
"""
import os
import sys
import time
import argparse
import requests
import numpy as np
from datetime import datetime, timedelta

# ── Yearly archive download ────────────────────────────────────
# POST to https://imdpune.gov.in/cmpg/Griddata/rainfall.php
# Body: {'rain': <year>} → returns yearly .grd binary

YEARLY_URL = "https://imdpune.gov.in/cmpg/Griddata/rainfall.php"
YEARLY_FILENAME = "Rainfall_ind{year}_rfp25.grd"

# ── Real-time daily download ───────────────────────────────────
# POST to https://imdpune.gov.in/cmpg/Griddata/rainfall_mon.php
# Body: {'rain': 'DD', 'month': 'MM', 'year': 'YYYY'} → returns daily .grd

REALTIME_URL = "https://imdpune.gov.in/cmpg/Griddata/rainfall_mon.php"


def download_yearly(year, output_dir, retries=3):
    """Download a yearly IMD rainfall .grd file."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"rain_ind0.25_{year}.grd"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
        print(f"  {filename} already exists, skipping")
        return True

    for attempt in range(retries):
        try:
            resp = requests.post(YEARLY_URL, data={"rain": year}, timeout=120)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            size_kb = os.path.getsize(filepath) / 1024
            if size_kb > 10:
                print(f"  {filename} OK ({size_kb:.0f} KB)")
                return True
            else:
                os.remove(filepath)
                print(f"  {filename} too small ({size_kb:.1f} KB), retrying...")
        except Exception as e:
            print(f"  {filename} attempt {attempt+1} failed: {e}")
        time.sleep(2)
    return False


def download_realtime_day(date_str, output_dir, retries=3):
    """Download a real-time daily IMD rainfall .grd file."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    year = dt.strftime("%Y")
    month = dt.strftime("%m")
    day = dt.strftime("%d")
    os.makedirs(os.path.join(output_dir, year), exist_ok=True)

    filename = f"rain_ind0.25_{month}_{day}_{year[2:]}.grd"
    filepath = os.path.join(output_dir, year, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
        return True

    for attempt in range(retries):
        try:
            resp = requests.post(
                REALTIME_URL,
                data={"rain": day, "month": month, "year": year},
                timeout=120,
            )
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            size_kb = os.path.getsize(filepath) / 1024
            if size_kb > 10:
                return True
            else:
                os.remove(filepath)
        except Exception:
            pass
        time.sleep(1)
    return False


def download_yearly_range(start_year, end_year, output_dir="imd_data"):
    """Download yearly IMD files for a range of years."""
    print(f"Downloading IMD yearly rainfall: {start_year} to {end_year}")
    print(f"Output: {output_dir}/")
    print(f"URL: {YEARLY_URL}")
    print()

    downloaded = 0
    failed = 0
    for year in range(start_year, end_year + 1):
        print(f"[{year}]", end=" ")
        if download_yearly(year, output_dir):
            downloaded += 1
        else:
            failed += 1
        time.sleep(1)

    print(f"\nDone: {downloaded} downloaded, {failed} failed")
    return downloaded > 0


def download_realtime_range(start_date, end_date, output_dir="imd_data"):
    """Download daily IMD files for a date range."""
    print(f"Downloading IMD real-time rainfall: {start_date} to {end_date}")
    print(f"Output: {output_dir}/")
    print()

    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    downloaded = 0
    failed = 0
    total = (end - current).days + 1

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        idx = downloaded + failed + 1
        print(f"  [{idx}/{total}] {date_str}...", end=" ")
        if download_realtime_day(date_str, output_dir):
            downloaded += 1
            print("OK")
        else:
            failed += 1
            print("FAILED")
        current += timedelta(days=1)
        time.sleep(0.5)

    print(f"\nDone: {downloaded} downloaded, {failed} failed")
    return downloaded > 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download IMD rainfall data")
    parser.add_argument("--mode", choices=["yearly", "realtime"], default="yearly",
                        help="yearly = archive (one file per year), realtime = daily")
    parser.add_argument("--start", default="2022",
                        help="Start: year (yearly mode) or YYYY-MM-DD (realtime mode)")
    parser.add_argument("--end", default="2024",
                        help="End: year (yearly mode) or YYYY-MM-DD (realtime mode)")
    parser.add_argument("--dir", default="imd_data", help="Output directory")
    args = parser.parse_args()

    if args.mode == "yearly":
        download_yearly_range(int(args.start), int(args.end), args.dir)
    else:
        download_realtime_range(args.start, args.end, args.dir)
