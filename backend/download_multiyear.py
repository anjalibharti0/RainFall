"""
Download ERA5 for 2022-2023 using larger batches (ERA5 supports 500+ coords).
Uses direct connection with generous delays (ERA5 is less aggressive with rate limits than forecast API).
"""
import os, json, time, requests, urllib3, numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"
ERA5_DAILY = "precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_direction_10m_dominant,surface_pressure_mean,shortwave_radiation_sum"

# Use the full NWD grid but with batch_size=500 (ERA5 handles it)
NWD_LATS = np.arange(37.5, 19.75, -0.25).round(4).tolist()
NWD_LONS = np.arange(65, 80.25, 0.25).round(4).tolist()

print_lock = Lock()
counter = {"ok": 0, "fail": 0, "skip": 0}
counter_lock = Lock()

def log(msg=""):
    with print_lock:
        print(msg, flush=True)

def download_batch(args):
    i, batch, start_date, end_date, year_dir, year = args
    outfile = os.path.join(year_dir, f"batch_{i:03d}.json")
    if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
        with counter_lock: counter["skip"] += 1
        return

    lats = [p[0] for p in batch]
    lons = [p[1] for p in batch]
    params = {
        "latitude": ",".join(str(l) for l in lats),
        "longitude": ",".join(str(l) for l in lons),
        "start_date": start_date, "end_date": end_date,
        "daily": ERA5_DAILY, "timezone": "Asia/Kolkata",
    }

    for attempt in range(4):
        try:
            r = requests.get(ERA5_URL, params=params, timeout=180, verify=False)
            if r.status_code == 200:
                with open(outfile, "w") as f:
                    json.dump(r.json(), f)
                with counter_lock: counter["ok"] += 1
                log(f"  [{year} batch {i+1}] OK")
                return
            elif r.status_code == 429:
                wait = 30 * (attempt + 1)
                log(f"  [{year} batch {i+1}] 429 wait {wait}s")
                time.sleep(wait)
            else:
                log(f"  [{year} batch {i+1}] HTTP {r.status_code}")
                time.sleep(5)
        except Exception as e:
            log(f"  [{year} batch {i+1}] Error: {str(e)[:50]}")
            time.sleep(10)

    with counter_lock: counter["fail"] += 1
    log(f"  [{year} batch {i+1}] FAIL")

def download_year(year, start_date, end_date, workers=3):
    all_pts = [(lat, lon) for lat in NWD_LATS for lon in NWD_LONS]
    batch_size = 500  # ERA5 handles large batches
    batches = [all_pts[i:i+batch_size] for i in range(0, len(all_pts), batch_size)]

    year_dir = os.path.join("nwp_data", str(year))
    os.makedirs(year_dir, exist_ok=True)

    existing = len([f for f in os.listdir(year_dir) if f.startswith("batch_") and f.endswith(".json")])
    remaining = [j for j in range(len(batches))
                 if not (os.path.exists(os.path.join(year_dir, f"batch_{j:03d}.json"))
                         and os.path.getsize(os.path.join(year_dir, f"batch_{j:03d}.json")) > 100)]

    log(f"\n  Year {year}: {len(batches)} batches (size {batch_size}), {existing} existing, {len(remaining)} remaining")

    if not remaining:
        log(f"  All done for {year}!")
        return

    tasks = [(j, batches[j], start_date, end_date, year_dir, year) for j in remaining]

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(download_batch, tasks))

if __name__ == "__main__":
    log("Multi-year ERA5 download (full NWD, batch_size=500)")
    log(f"Grid: {len(NWD_LATS)} x {len(NWD_LONS)} = {len(NWD_LATS)*len(NWD_LONS)} points")

    for year, start, end in [(2022, "2022-06-01", "2022-09-30"), (2023, "2023-06-01", "2023-09-30")]:
        download_year(year, start, end, workers=3)

    log(f"\nDONE: {counter['ok']} ok, {counter['fail']} failed, {counter['skip']} skipped")
