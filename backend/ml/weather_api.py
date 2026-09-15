import requests
import numpy as np
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

ALL_HOURLY = ",".join([
    "temperature_2m", "precipitation", "cape",
    "wind_speed_10m", "wind_direction_10m",
    "surface_pressure", "cloud_cover",
    "temperature_700hPa", "relative_humidity_700hPa",
    "wind_speed_700hPa", "wind_direction_700hPa",
    "wind_speed_200hPa", "wind_direction_200hPa",
])

MONSOON_PHASES = {6: 1, 7: 2, 8: 2, 9: 3}
PEAK_MONSOON_MONTHS = {7, 8}


def _safe_mean(values):
    clean = [v for v in values if v is not None]
    return float(np.mean(clean)) if clean else None


def fetch_open_meteo(lat, lon, date):
    from datetime import date as _date
    try:
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": ALL_HOURLY,
            "timezone": "Asia/Kolkata",
        }
        req = datetime.strptime(date[:10], "%Y-%m-%d").date()
        days_ago = (_date.today() - req).days
        if days_ago < 0:
            # future date -> use standard forecast range
            params["start_date"] = date
            params["end_date"] = date
        elif days_ago == 0:
            params["start_date"] = date
            params["end_date"] = date
        elif 0 < days_ago <= 85:
            # past within past_days window: past_days is exclusive with start/end dates
            params["past_days"] = days_ago + 7
        else:
            return None

        resp = requests.get(OPEN_METEO_FORECAST, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "hourly" not in data:
            return None

        if days_ago > 0:
            # Roll the hourly series back to just the requested date.
            hours = data["hourly"]
            times = hours.get("time", [])
            keep = [i for i, t in enumerate(times) if t[:10] == date[:10]]
            if not keep:
                return None
            out = {"time": [times[i] for i in keep]}
            for key, vals in hours.items():
                if key != "time" and len(vals) == len(times):
                    out[key] = [vals[i] for i in keep]
                elif key != "time":
                    out[key] = list(vals)
            data = {"hourly": out}
        return data
    except Exception:
        return None


def compute_ml_features_v2(data, lat=0, lon=0, date_str=None):
    """V2 features: no circular deps, temporal+spatial."""
    if not data or "hourly" not in data:
        return None, None

    h = data["hourly"]

    def safe(key):
        return _safe_mean(h.get(key, []))

    precip = safe("precipitation") or 0
    t2m = safe("temperature_2m") or 27
    wind10 = safe("wind_speed_10m") or 0
    wind_dir = safe("wind_direction_10m") or 0
    cape = safe("cape") or 500
    pressure = safe("surface_pressure") or 1013
    radiation_raw = safe("cloud_cover")

    if radiation_raw is not None:
        radiation = round(max(0, 25 - radiation_raw * 0.25), 1)
    else:
        radiation = 15.0

    features = {
        "raw_rainfall": round(precip, 2),
        "wind_speed": round(wind10, 2),
        "wind_dir": round(wind_dir, 1),
        "cape": round(max(0, cape), 1),
        "pressure": round(pressure, 1),
        "radiation": radiation,
        "temp_range": round(3.0, 1),
        "temp_mean": round(t2m, 1),
    }

    if date_str and len(date_str) >= 8:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        features["day_of_year"] = dt.timetuple().tm_yday
        features["month"] = dt.month
        features["monsoon_phase"] = MONSOON_PHASES.get(dt.month, 0)
        features["is_peak_monsoon"] = 1 if dt.month in PEAK_MONSOON_MONTHS else 0
    else:
        features["day_of_year"] = 180
        features["month"] = 7
        features["monsoon_phase"] = 2
        features["is_peak_monsoon"] = 1

    features["latitude"] = lat
    features["longitude"] = lon

    raw = {
        "precip": precip,
        "temp": t2m,
        "wind": wind10,
        "pressure": pressure,
    }

    return features, raw


def fetch_district_weather(district, date):
    data = fetch_open_meteo(district["centroid_lat"], district["centroid_lon"], date)
    ml, raw = compute_ml_features_v2(
        data,
        lat=district["centroid_lat"],
        lon=district["centroid_lon"],
        date_str=date,
    )
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

        if i + batch_size < len(districts):
            time.sleep(0.3)

    return results


def get_aggregate_features(district_weather):
    """Compute aggregate atmospheric features from all districts."""
    good = [dw["ml_features"] for dw in district_weather.values() if dw and "ml_features" in dw]
    if not good:
        return None

    agg = {}
    for key in ["wind_speed", "wind_dir", "cape", "pressure", "radiation", "temp_range", "temp_mean"]:
        vals = [f[key] for f in good if key in f and f[key] is not None]
        agg[key] = round(float(np.mean(vals)), 2) if vals else 0.0

    agg["raw_rainfall"] = round(np.mean([f.get("raw_rainfall", 0) for f in good]), 2)
    agg["day_of_year"] = good[0].get("day_of_year", 180)
    agg["month"] = good[0].get("month", 7)
    agg["monsoon_phase"] = good[0].get("monsoon_phase", 2)
    agg["is_peak_monsoon"] = good[0].get("is_peak_monsoon", 1)
    agg["latitude"] = round(np.mean([f.get("latitude", 28) for f in good]), 2)
    agg["longitude"] = round(np.mean([f.get("longitude", 77) for f in good]), 2)

    return agg
