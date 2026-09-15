"""
Fill GFS gap (lat 23-30) using ERA5 reanalysis data with proxy rotation + concurrency.

Run:
    python download_gap_era5.py
    python download_gap_era5.py --start 2024-06-01 --end 2024-09-30 --workers 8
"""
import os
import json
import time
import random
import requests
import urllib3
import argparse
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"
ERA5_DAILY = (
    "precipitation_sum,"
    "temperature_2m_max,"
    "temperature_2m_min,"
    "wind_speed_10m_max,"
    "wind_direction_10m_dominant,"
    "surface_pressure_mean,"
    "shortwave_radiation_sum"
)

GAP_LAT_MIN = 23.0
GAP_LAT_MAX = 30.5
GAP_LON_MIN = 65.0
GAP_LON_MAX = 80.0

ALL_LATS = np.arange(GAP_LAT_MAX, GAP_LAT_MIN - 0.25, -0.25).round(4).tolist()
ALL_LONS = np.arange(GAP_LON_MIN, GAP_LON_MAX + 0.25, 0.25).round(4).tolist()

print_lock = Lock()
counter_lock = Lock()
ok_count = [0]
fail_count = [0]


def log(msg=""):
    with print_lock:
        print(msg, flush=True)


def fetch_proxies():
    """Fetch fresh free HTTP proxies from multiple sources."""
    proxy_urls = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ]
    proxies = []
    for url in proxy_urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                lines = [l.strip() for l in resp.text.splitlines() if l.strip() and ":" in l]
                proxies.extend(lines)
                log(f"  Fetched {len(lines)} proxies from {url.split('/')[-1]}")
        except Exception:
            pass
    proxies = list(set(proxies))
    log(f"  Total unique proxies: {len(proxies)}")
    return proxies


def test_proxy(proxy, timeout=10):
    """Quick test if a proxy works with Open-Meteo."""
    try:
        resp = requests.get(
            ERA5_URL,
            params={"latitude": "28", "longitude": "77", "start_date": "2024-07-01", "end_date": "2024-07-02", "daily": "precipitation_sum", "timezone": "UTC"},
            proxies={"https": f"http://{proxy}", "http": f"http://{proxy}"},
            timeout=timeout,
            verify=False,
        )
        return resp.status_code == 200
    except Exception:
        return False


def warm_proxies(raw_proxies, max_test=150):
    """Test proxies in parallel and keep only working ones."""
    log(f"  Testing top {min(max_test, len(raw_proxies))} proxies...")
    random.shuffle(raw_proxies)
    tested = raw_proxies[:max_test]
    working = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(test_proxy, p): p for p in tested}
        for f in as_completed(futures):
            p = futures[f]
            if f.result():
                working.append(p)
    log(f"  Working proxies: {len(working)}/{len(tested)}")
    return working


class ProxyPool:
    def __init__(self, proxies):
        self.proxies = list(proxies)
        self.idx = 0
        self.lock = Lock()

    def next(self):
        with self.lock:
            if not self.proxies:
                return None
            p = self.proxies[self.idx % len(self.proxies)]
            self.idx += 1
            return p

    def remove(self, proxy):
        with self.lock:
            if proxy in self.proxies:
                self.proxies.remove(proxy)


def download_batch(lats, lons, start_date, end_date, outfile, pool: ProxyPool, retries=6):
    """Download batch with proxy rotation."""
    params = {
        "latitude": ",".join(str(l) for l in lats),
        "longitude": ",".join(str(l) for l in lons),
        "start_date": start_date,
        "end_date": end_date,
        "daily": ERA5_DAILY,
        "timezone": "Asia/Kolkata",
    }

    for attempt in range(retries):
        proxy = pool.next()
        proxy_str = f"http://{proxy}" if proxy else None
        proxies = {"https": proxy_str, "http": proxy_str} if proxy_str else None

        try:
            resp = requests.get(ERA5_URL, params=params, timeout=60, verify=False, proxies=proxies)
            if resp.status_code == 200:
                data = resp.json()
                with open(outfile, "w") as f:
                    json.dump(data, f)
                n = len(data) if isinstance(data, list) else 1
                return True, n
            elif resp.status_code == 429:
                if proxy:
                    pool.remove(proxy)
                wait = random.uniform(2, 6)
                time.sleep(wait)
                continue
            elif resp.status_code == 403:
                if proxy:
                    pool.remove(proxy)
                continue
            else:
                continue
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if proxy:
                pool.remove(proxy)
            continue
        except Exception:
            if proxy:
                pool.remove(proxy)
            continue

    return False, "Max retries"


def download_one_batch(args):
    """Worker function for ThreadPoolExecutor."""
    i, batch, start_date, end_date, year_dir, pool = args
    outfile = os.path.join(year_dir, f"era5_gap_{i:03d}.json")

    if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
        with counter_lock:
            ok_count[0] += 1
        return True, "skipped"

    lats = [p[0] for p in batch]
    lons = [p[1] for p in batch]

    success, result = download_batch(lats, lons, start_date, end_date, outfile, pool)

    with counter_lock:
        if success:
            ok_count[0] += 1
        else:
            fail_count[0] += 1

    tag = "OK" if success else "FAIL"
    log(f"  [{i+1}] {tag}: {result}")
    return success, result


def download_gap_era5(start_date, end_date, data_dir="nwp_data", workers=8):
    os.makedirs(data_dir, exist_ok=True)

    all_points = [(lat, lon) for lat in ALL_LATS for lon in ALL_LONS]
    batch_size = 100
    batches = [all_points[i:i + batch_size] for i in range(0, len(all_points), batch_size)]

    log(f"ERA5 gap fill: lat {GAP_LAT_MIN}-{GAP_LAT_MAX}, lon {GAP_LON_MIN}-{GAP_LON_MAX}")
    log(f"Grid: {len(ALL_LATS)} x {len(ALL_LONS)} = {len(all_points)} points")
    log(f"Batches: {len(batches)} (size {batch_size}), workers: {workers}")
    log(f"Date range: {start_date} to {end_date}")
    log()

    # Fetch and warm proxies
    raw_proxies = fetch_proxies()
    if not raw_proxies:
        log("No proxies fetched, trying direct connection...")
        working_proxies = []
    else:
        working_proxies = warm_proxies(raw_proxies)
        if not working_proxies:
            log("No working proxies, falling back to direct connection...")
            working_proxies = []

    # Add direct as fallback
    pool = ProxyPool(working_proxies)

    year = datetime.strptime(start_date, "%Y-%m-%d").year
    year_dir = os.path.join(data_dir, str(year))
    os.makedirs(year_dir, exist_ok=True)

    # Build task list (skip existing)
    tasks = []
    for i, batch in enumerate(batches):
        outfile = os.path.join(year_dir, f"era5_gap_{i:03d}.json")
        if os.path.exists(outfile) and os.path.getsize(outfile) > 100:
            with counter_lock:
                ok_count[0] += 1
            continue
        tasks.append((i, batch, start_date, end_date, year_dir, pool))

    log(f"  Remaining: {len(tasks)} batches to download")
    log()

    if workers <= 1:
        for task in tasks:
            download_one_batch(task)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(download_one_batch, tasks))

    log(f"\nDONE: {ok_count[0]} ok, {fail_count[0]} failed")
    return ok_count[0], fail_count[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download ERA5 gap data with proxies")
    parser.add_argument("--start", default="2024-06-01")
    parser.add_argument("--end", default="2024-09-30")
    parser.add_argument("--dir", default="nwp_data")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent download workers")
    args = parser.parse_args()

    download_gap_era5(args.start, args.end, args.dir, args.workers)
