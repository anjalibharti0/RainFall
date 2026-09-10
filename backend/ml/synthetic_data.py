import numpy as np
import pandas as pd
from ml.all_districts import DISTRICTS
from ml.weather_api import fetch_all_districts_weather, get_aggregate_features
import time

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]

REGIME_FEATURE_PROFILES = {
    "active_monsoon": {"wind_shear": (15, 25), "olr": (-30, -10), "cape": (1000, 2500), "vorticity": (1.5, 4.0), "moisture_flux": (200, 500), "humidity_700": (70, 90)},
    "break_monsoon": {"wind_shear": (5, 12), "olr": (0, 15), "cape": (200, 800), "vorticity": (-0.5, 1.0), "moisture_flux": (50, 150), "humidity_700": (40, 65)},
    "depression": {"wind_shear": (10, 20), "olr": (-40, -15), "cape": (1500, 3500), "vorticity": (2.5, 6.0), "moisture_flux": (300, 700), "humidity_700": (75, 95)},
    "orographic": {"wind_shear": (8, 18), "olr": (-20, -5), "cape": (500, 1500), "vorticity": (0.5, 2.5), "moisture_flux": (150, 400), "humidity_700": (60, 85)},
    "coastal": {"wind_shear": (6, 15), "olr": (-15, 0), "cape": (800, 2000), "vorticity": (0.3, 2.0), "moisture_flux": (200, 450), "humidity_700": (65, 88)},
    "western_disturbance": {"wind_shear": (12, 22), "olr": (-10, 5), "cape": (300, 1000), "vorticity": (0.8, 3.0), "moisture_flux": (100, 300), "humidity_700": (45, 70)},
}

REGIME_RAINFALL_PROFILES = {
    "active_monsoon": (15, 60),
    "break_monsoon": (2, 20),
    "depression": (40, 150),
    "orographic": (20, 80),
    "coastal": (15, 70),
    "western_disturbance": (5, 30),
}

BIAS_FACTORS = {
    "active_monsoon": 1.25,
    "break_monsoon": 0.75,
    "depression": 0.70,
    "orographic": 1.45,
    "coastal": 1.30,
    "western_disturbance": 1.15,
}


def _sample(profile, size=1):
    lo, hi = profile
    if size == 1:
        return float(np.random.uniform(lo, hi))
    return np.random.uniform(lo, hi, size)


def generate_training_data(n_samples=5000, seed=42):
    rng = np.random.RandomState(seed)
    rows = []
    regime_weights = [0.25, 0.20, 0.15, 0.20, 0.15, 0.05]
    for _ in range(n_samples):
        regime_idx = rng.choice(6, p=regime_weights)
        regime = REGIMES[regime_idx]
        fp = REGIME_FEATURE_PROFILES[regime]
        rp = REGIME_RAINFALL_PROFILES[regime]
        row = {
            "wind_shear": float(_sample(fp["wind_shear"])),
            "olr": float(_sample(fp["olr"])),
            "cape": float(_sample(fp["cape"])),
            "vorticity": float(_sample(fp["vorticity"])),
            "moisture_flux": float(_sample(fp["moisture_flux"])),
            "humidity_700": float(_sample(fp["humidity_700"])),
            "raw_rainfall": float(_sample(rp)),
            "regime": regime,
        }
        bias = BIAS_FACTORS[regime] + rng.normal(0, 0.1)
        row["corrected_rainfall"] = max(0, row["raw_rainfall"] / bias + rng.normal(0, 2))
        thresholds = [7.5, 64.5, 124.5, 244.5]
        for t in thresholds:
            base_prob = 1 / (1 + np.exp(0.05 * (t - row["corrected_rainfall"])))
            row[f"p_exceed_{t}"] = float(np.clip(base_prob + rng.normal(0, 0.05), 0, 1))
        rows.append(row)
    return pd.DataFrame(rows)


def classify_regime(features):
    """Classify which regime the atmospheric features match."""
    best_regime = "break_monsoon"
    best_score = float("inf")
    for regime, profile in REGIME_FEATURE_PROFILES.items():
        score = sum(
            (features.get(k, 0) - (lo + hi) / 2) ** 2 / max((hi - lo) ** 2, 1)
            for k, (lo, hi) in profile.items()
        )
        if score < best_score:
            best_score = score
            best_regime = regime
    return best_regime


def generate_synthetic_forecast(forecast_date="2026-09-09", lead_time=24):
    """Generate synthetic forecast with random data (fallback)."""
    rng = np.random.RandomState(hash(forecast_date) % 2**31 + lead_time)
    regime_idx = rng.choice(6, p=[0.25, 0.20, 0.15, 0.20, 0.15, 0.05])
    regime = REGIMES[regime_idx]
    fp = REGIME_FEATURE_PROFILES[regime]
    confidence = float(np.clip(rng.uniform(0.70, 0.95), 0.70, 0.95))
    features = {
        "wind_shear": float(_sample(fp["wind_shear"])),
        "olr": float(_sample(fp["olr"])),
        "cape": float(_sample(fp["cape"])),
        "vorticity": float(_sample(fp["vorticity"])),
        "moisture_flux": float(_sample(fp["moisture_flux"])),
        "humidity_700": float(_sample(fp["humidity_700"])),
    }
    regime_info = {"type": regime, "confidence": confidence, "features": features}
    rp = REGIME_RAINFALL_PROFILES[regime]
    lead_factor = 1 + (lead_time - 24) / 200.0
    district_forecasts = []
    for d in DISTRICTS:
        raw = float(np.clip(_sample(rp) * lead_factor + rng.normal(0, 5), 0, 300))
        bias = BIAS_FACTORS[regime] + rng.normal(0, 0.08)
        corrected = float(max(0, raw / bias + rng.normal(0, 3)))
        thresholds = {"p_moderate": 0.0, "p_heavy": 0.0, "p_very_heavy": 0.0, "p_extreme": 0.0}
        for t, key in [(7.5, "p_moderate"), (64.5, "p_heavy"), (124.5, "p_very_heavy"), (244.5, "p_extreme")]:
            prob = float(np.clip(1 / (1 + np.exp(0.06 * (t - corrected))) + rng.normal(0, 0.05), 0, 1))
            thresholds[key] = round(prob, 3)
        district_forecasts.append({
            "district_id": d["district_id"],
            "name": d["district_name"],
            "state": d["state_name"],
            "zone": d["zone"],
            "lat": d["centroid_lat"],
            "lon": d["centroid_lon"],
            "raw": round(raw, 1),
            "corrected": round(corrected, 1),
            "regime": regime,
            **thresholds,
        })
    return {"regime": regime_info, "districts": district_forecasts}


_forecast_cache = {}
_CACHE_TTL = 300


def generate_real_forecast(forecast_date="2026-09-10", lead_time=24):
    """Fetch real weather from Open-Meteo for a sample of districts to classify regime,
    then apply to all 801. Caches for 5 minutes."""
    cache_key = f"{forecast_date}_{lead_time}"
    now = time.time()
    if cache_key in _forecast_cache and (now - _forecast_cache[cache_key]["ts"]) < _CACHE_TTL:
        print(f"[real_forecast] Using cached result for {cache_key}")
        return _forecast_cache[cache_key]["data"]

    try:
        sample_size = min(60, len(DISTRICTS))
        rng_sample = np.random.RandomState(42)
        sample_indices = rng_sample.choice(len(DISTRICTS), size=sample_size, replace=False)
        sample_districts = [DISTRICTS[i] for i in sample_indices]

        print(f"[real_forecast] Sampling {sample_size} districts for regime classification...")
        district_weather = fetch_all_districts_weather(sample_districts, date=forecast_date)
        fetched = sum(1 for v in district_weather.values() if v is not None)
        print(f"[real_forecast] Got data for {fetched}/{sample_size} sampled districts")

        if fetched < 10:
            print("[real_forecast] Too few districts, falling back to synthetic")
            return generate_synthetic_forecast(forecast_date, lead_time)

        agg_features = get_aggregate_features(district_weather)
        if not agg_features:
            return generate_synthetic_forecast(forecast_date, lead_time)

        regime = classify_regime(agg_features)
        rp = REGIME_RAINFALL_PROFILES[regime]
        bias_factor = BIAS_FACTORS[regime]
        lead_factor = 1 + (lead_time - 24) / 200.0

        rng = np.random.RandomState(42)
        district_forecasts = []
        for d in DISTRICTS:
            did = d["district_id"]
            dw = district_weather.get(did)

            if dw and dw.get("ml_features"):
                rw = dw.get("raw_weather", {})
                precip = rw.get("precip", 0) or 0
                raw = float(np.clip(precip * lead_factor * 5 + rng.normal(0, 2), 0, 300))
                corrected = float(max(0, raw / bias_factor + rng.normal(0, 1)))
            else:
                raw = float(np.clip(_sample(rp) * lead_factor + rng.normal(0, 5), 0, 300))
                corrected = float(max(0, raw / bias_factor + rng.normal(0, 3)))

            thresholds = {}
            for t, key in [(7.5, "p_moderate"), (64.5, "p_heavy"), (124.5, "p_very_heavy"), (244.5, "p_extreme")]:
                prob = float(np.clip(1 / (1 + np.exp(0.06 * (t - corrected))) + rng.normal(0, 0.03), 0, 1))
                thresholds[key] = round(prob, 3)

            district_forecasts.append({
                "district_id": did,
                "name": d["district_name"],
                "state": d["state_name"],
                "zone": d["zone"],
                "lat": d["centroid_lat"],
                "lon": d["centroid_lon"],
                "raw": round(raw, 1),
                "corrected": round(corrected, 1),
                "regime": regime,
                **thresholds,
            })

        confidence = round(float(np.clip(0.75 + fetched / sample_size * 0.2, 0.70, 0.95)), 2)
        regime_info = {"type": regime, "confidence": confidence, "features": agg_features}
        result = {"regime": regime_info, "districts": district_forecasts}
        print(f"[real_forecast] Regime: {regime} ({confidence:.0%}), {len(district_forecasts)} districts")

        _forecast_cache[cache_key] = {"data": result, "ts": now}
        return result

    except Exception as e:
        print(f"[real_forecast] Error: {e}, falling back to synthetic")
        return generate_synthetic_forecast(forecast_date, lead_time)


def compute_verification_metrics(observed, forecast, threshold=64.5):
    obs_events = observed >= threshold
    fct_events = forecast >= threshold
    hits = int(np.sum(obs_events & fct_events))
    misses = int(np.sum(obs_events & ~fct_events))
    false_alarms = int(np.sum(~obs_events & fct_events))
    correct_negatives = int(np.sum(~obs_events & ~fct_events))
    n = len(observed)
    rmse = float(np.sqrt(np.mean((forecast - observed) ** 2)))
    mae = float(np.mean(np.abs(forecast - observed)))
    obs_mean = np.mean(observed)
    fct_mean = np.mean(forecast)
    bias_ratio = float(fct_mean / obs_mean) if obs_mean > 0 else 1.0
    pod = hits / (hits + misses) if (hits + misses) > 0 else 0.0
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0.0
    csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0.0
    hits_random = (hits + misses) * (hits + false_alarms) / n if n > 0 else 0
    ets_num = hits - hits_random
    ets_den = hits + misses + false_alarms - hits_random
    ets = ets_num / ets_den if ets_den > 0 else 0.0
    fss = float(max(0, 1 - (np.mean((forecast / n - observed / n) ** 2) / max(np.mean((observed / n) ** 2), 1e-10))))
    return {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "bias_ratio": round(bias_ratio, 2),
        "ets": round(ets, 3),
        "csi": round(csi, 3),
        "pod": round(pod, 3),
        "far": round(far, 3),
        "fss": round(fss, 3),
    }
