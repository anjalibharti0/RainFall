"""Download the missing GFS batches for lat 23-34 (central India gap)."""
import os, json, time, requests, urllib3, numpy as np

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
DAILY_VARS = "precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_direction_10m_dominant,cape_mean,surface_pressure_mean,shortwave_radiation_sum"

gap_lats = np.arange(34, 23, -0.25).round(4).tolist()
all_lons = np.arange(65, 80.25, 0.25).round(4).tolist()
gap_pts = [(lat, lon) for lat in gap_lats for lon in all_lons]
batches = [gap_pts[i:i+100] for i in range(0, len(gap_pts), 100)]

print(f"Gap: {len(gap_lats)} lats x {len(all_lons)} lons = {len(gap_pts)} points, {len(batches)} batches")

data_dir = "nwp_data/2024"
os.makedirs(data_dir, exist_ok=True)

existing = set()
for f in os.listdir(data_dir):
    if f.startswith("batch_") and f.endswith(".json"):
        existing.add(f)

start_date = "2024-06-01"
end_date = "2024-09-30"

ok_count = 0
fail_count = 0

for i, batch in enumerate(batches):
    outfile = os.path.join(data_dir, f"gap_{i:03d}.json")
    if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
        ok_count += 1
        continue

    lats = [p[0] for p in batch]
    lons = [p[1] for p in batch]

    for attempt in range(5):
        try:
            resp = requests.get(API_URL, params={
                "latitude": ",".join(str(l) for l in lats),
                "longitude": ",".join(str(l) for l in lons),
                "start_date": start_date,
                "end_date": end_date,
                "daily": DAILY_VARS,
                "models": "gfs_seamless",
                "timezone": "Asia/Kolkata",
            }, timeout=120, verify=False)

            if resp.status_code == 200:
                data = resp.json()
                with open(outfile, "w") as f:
                    json.dump(data, f)
                print(f"  [{i+1}/{len(batches)}] OK ({len(data)} locs)")
                ok_count += 1
                break
            elif resp.status_code == 429:
                wait = 30 * (2 ** attempt)
                print(f"  [{i+1}/{len(batches)}] 429 wait {wait}s", flush=True)
                time.sleep(wait)
            else:
                print(f"  [{i+1}/{len(batches)}] HTTP {resp.status_code}")
                fail_count += 1
                break
        except Exception as e:
            print(f"  [{i+1}/{len(batches)}] Error: {str(e)[:60]}")
            time.sleep(10)
    else:
        fail_count += 1

    time.sleep(15)

print(f"\nDONE: {ok_count} ok, {fail_count} failed")
