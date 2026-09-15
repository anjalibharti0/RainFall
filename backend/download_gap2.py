"""Download remaining gap batches for lat 23-30.75."""
import os, json, time, requests, urllib3, numpy as np

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
DAILY_VARS = "precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_direction_10m_dominant,cape_mean,surface_pressure_mean,shortwave_radiation_sum"

gap_lats = np.arange(30.5, 23, -0.25).round(4).tolist()
all_lons = np.arange(65, 80.25, 0.25).round(4).tolist()
gap_pts = [(lat, lon) for lat in gap_lats for lon in all_lons]
batches = [gap_pts[i:i+100] for i in range(0, len(gap_pts), 100)]
print(f"Remaining: {len(gap_lats)} lats, {len(gap_pts)} points, {len(batches)} batches")

data_dir = "nwp_data/2024"
start_date = "2024-06-01"
end_date = "2024-09-30"
ok = 0
fail = 0

for i, batch in enumerate(batches):
    outfile = os.path.join(data_dir, f"gap2_{i:03d}.json")
    if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
        ok += 1
        continue

    lats = [p[0] for p in batch]
    lons = [p[1] for p in batch]
    for attempt in range(5):
        try:
            resp = requests.get(API_URL, params={
                "latitude": ",".join(str(l) for l in lats),
                "longitude": ",".join(str(l) for l in lons),
                "start_date": start_date, "end_date": end_date,
                "daily": DAILY_VARS, "models": "gfs_seamless", "timezone": "Asia/Kolkata",
            }, timeout=120, verify=False)
            if resp.status_code == 200:
                with open(outfile, "w") as f:
                    json.dump(resp.json(), f)
                print(f"  [{i+1}/{len(batches)}] OK")
                ok += 1
                break
            elif resp.status_code == 429:
                wait = 30 * (2 ** attempt)
                print(f"  [{i+1}/{len(batches)}] 429 wait {wait}s", flush=True)
                time.sleep(wait)
            else:
                print(f"  [{i+1}/{len(batches)}] HTTP {resp.status_code}")
                fail += 1
                break
        except Exception as e:
            print(f"  [{i+1}/{len(batches)}] Error: {str(e)[:60]}")
            time.sleep(10)
    else:
        fail += 1
    time.sleep(15)

print(f"\nDONE: {ok} ok, {fail} failed")
