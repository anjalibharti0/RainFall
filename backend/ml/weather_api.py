import requests
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

ML_FEATURE_KEYS = ["wind_shear", "olr", "cape", "vorticity", "moisture_flux", "humidity_700"]

ALL_HOURLY = ",".join([
    "temperature_2m", "precipitation", "cape",
    "wind_speed_10m", "wind_direction_10m",
    "surface_pressure", "cloud_cover",
    "temperature_700hPa", "relative_humidity_700hPa",
    "wind_speed_700hPa", "wind_direction_700hPa",
    "wind_speed_200hPa", "wind_direction_200hPa",
])


def _safe_mean(values):
    clean = [v for v in values if v is not None]
    return float(np.mean(clean)) if clean else None


def fetch_open_meteo(lat, lon, date):
    """Single API call for surface + pressure level data."""
    try:
        resp = requests.get(OPEN_METEO_FORECAST, params={
            "latitude": lat, "longitude": lon,
            "start_date": date, "end_date": date,
            "hourly": ALL_HOURLY,
            "timezone": "Asia/Kolkata",
        }, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def compute_ml_features(data):
    """Derive 6 ML features from a single Open-Meteo response."""
    if not data or "hourly" not in data:
        return None, None

    h = data["hourly"]

    def safe(key):
        return _safe_mean(h.get(key, []))

    w10 = safe("wind_speed_10m")
    wd10 = safe("wind_direction_10m")
    w700 = safe("wind_speed_700hPa")
    wd700 = safe("wind_direction_700hPa")
    w200 = safe("wind_speed_200hPa")
    cape = safe("cape")
    rh700 = safe("relative_humidity_700hPa")
    temp700 = safe("temperature_700hPa")

    ml = {}

    w10v = w10 or 0
    w200v = w200 or 0
    ml["wind_shear"] = round(max(0, w200v - w10v), 2)

    ml["cape"] = round(cape, 1) if cape and cape > 0 else 500.0
    ml["humidity_700"] = round(rh700, 1) if rh700 is not None else 60.0

    if w700 is not None and rh700 is not None:
        ml["moisture_flux"] = round(w700 * (rh700 / 100.0) * 15, 1)
    elif w700 is not None:
        ml["moisture_flux"] = round(w700 * 8, 1)
    else:
        ml["moisture_flux"] = 200.0

    if temp700 is not None:
        ml["olr"] = round(-5 - (temp700 - 5) * 1.5, 1)
    else:
        ml["olr"] = -10.0

    if w700 is not None and wd700 is not None:
        ml["vorticity"] = round((w700 / 50) * np.sin(np.radians(wd700)), 2)
    else:
        ml["vorticity"] = 1.0

    raw = {
        "precip": safe("precipitation") or 0,
        "temp": safe("temperature_2m") or 0,
        "cloud": safe("cloud_cover") or 0,
        "pressure": safe("surface_pressure") or 1013,
        "rh_sfc": safe("relative_humidity_2m") if "relative_humidity_2m" in h else (safe("temperature_2m") or 50),
    }

    return ml, raw


def fetch_district_weather(district, date):
    """Fetch real weather for one district (single API call)."""
    data = fetch_open_meteo(district["centroid_lat"], district["centroid_lon"], date)
    ml, raw = compute_ml_features(data)
    if ml:
        return {
            "district_id": district["district_id"],
            "lat": district["centroid_lat"],
            "lon": district["centroid_lon"],
            "ml_features": ml,
            "raw_weather": raw,
        }
    return None


def fetch_all_districts_weather(districts, date, max_workers=8):
    """Fetch real weather for all districts in parallel with batching."""
    results = {}
    batch_size = 40

    for i in range(0, len(districts), batch_size):
        batch = districts[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(fetch_district_weather, d, date): d["district_id"] for d in batch}
            for f in as_completed(futures):
                did = futures[f]
                try:
                    result = f.result()
                    if result:
                        results[did] = result
                except Exception:
                    pass

        fetched_so_far = len(results)
        if i + batch_size < len(districts):
            time.sleep(0.3)

    return results


def get_aggregate_features(district_weather):
    """Compute aggregate atmospheric features from all districts."""
    good = [dw["ml_features"] for dw in district_weather.values() if dw and "ml_features" in dw]
    if not good:
        return None
    agg = {}
    for key in ML_FEATURE_KEYS:
        vals = [f[key] for f in good if key in f and f[key] is not None]
        agg[key] = round(float(np.mean(vals)), 2) if vals else 0.0
    return agg
