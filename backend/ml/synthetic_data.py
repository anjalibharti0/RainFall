import numpy as np
import pandas as pd

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]

REGIME_FEATURE_PROFILES = {
    "active_monsoon": {
        "wind_speed": (15, 30),
        "cape": (1000, 2500),
        "pressure": (998, 1005),
        "radiation": (5, 15),
        "temp_range": (2, 6),
    },
    "break_monsoon": {
        "wind_speed": (3, 10),
        "cape": (200, 800),
        "pressure": (1006, 1012),
        "radiation": (15, 25),
        "temp_range": (5, 12),
    },
    "depression": {
        "wind_speed": (20, 40),
        "cape": (1500, 3500),
        "pressure": (990, 1000),
        "radiation": (2, 10),
        "temp_range": (1, 4),
    },
    "orographic": {
        "wind_speed": (8, 20),
        "cape": (500, 1500),
        "pressure": (1002, 1008),
        "radiation": (10, 20),
        "temp_range": (4, 10),
    },
    "coastal": {
        "wind_speed": (10, 22),
        "cape": (800, 2000),
        "pressure": (1003, 1009),
        "radiation": (8, 18),
        "temp_range": (3, 7),
    },
    "western_disturbance": {
        "wind_speed": (12, 28),
        "cape": (300, 1000),
        "pressure": (1004, 1012),
        "radiation": (12, 22),
        "temp_range": (6, 14),
    },
}

REGIME_RAINFALL_PROFILES = {
    "active_monsoon": (15, 80),
    "break_monsoon": (0, 15),
    "depression": (50, 200),
    "orographic": (20, 100),
    "coastal": (15, 90),
    "western_disturbance": (5, 40),
}

BIAS_FACTORS = {
    "active_monsoon": 1.25,
    "break_monsoon": 0.75,
    "depression": 0.70,
    "orographic": 1.45,
    "coastal": 1.30,
    "western_disturbance": 1.15,
}

ZONE_EFFECTS = {
    "west_coast": 1.4,
    "central": 1.1,
    "north": 0.9,
    "east": 1.2,
    "south": 1.0,
    "northeast": 1.5,
}

LEAD_TIME_DEGRADATION = {
    24: 1.0,
    48: 1.15,
    72: 1.35,
    96: 1.60,
    120: 1.90,
}

FEATURE_NAMES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
    "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude",
]

MONSOON_PHASES = {6: 1, 7: 2, 8: 2, 9: 3}
PEAK_MONSOON_MONTHS = {7, 8}


def _sample(profile, size=1):
    lo, hi = profile
    if size == 1:
        return float(np.random.uniform(lo, hi))
    return np.random.uniform(lo, hi, size)


def _correlated_features_v2(regime, rng, lat=28.0, lon=77.0, month=7):
    """Generate correlated V2 features for a regime."""
    fp = REGIME_FEATURE_PROFILES[regime]

    wind_speed = _sample(fp["wind_speed"])
    cape = _sample(fp["cape"])
    pressure = _sample(fp["pressure"])
    radiation = _sample(fp["radiation"])
    temp_range = _sample(fp["temp_range"])

    wind_dir = float(rng.uniform(0, 360))
    temp_mean = float(rng.uniform(24, 35))

    features = {
        "raw_rainfall": 0.0,
        "wind_speed": float(np.clip(wind_speed, 0, 50)),
        "wind_dir": wind_dir,
        "cape": float(np.clip(cape, 0, 5000)),
        "pressure": float(np.clip(pressure, 985, 1020)),
        "radiation": float(np.clip(radiation, 0, 30)),
        "temp_range": float(np.clip(temp_range, 0, 20)),
        "temp_mean": float(np.clip(temp_mean, 15, 42)),
        "day_of_year": 180,
        "month": month,
        "monsoon_phase": MONSOON_PHASES.get(month, 0),
        "is_peak_monsoon": 1 if month in PEAK_MONSOON_MONTHS else 0,
        "latitude": lat,
        "longitude": lon,
    }
    return features


def _calculate_realistic_rainfall(regime, features, zone, lead_time, rng):
    rp = REGIME_RAINFALL_PROFILES[regime]
    base_rain = _sample(rp)
    zone_factor = ZONE_EFFECTS.get(zone, 1.0)
    base_rain *= zone_factor

    if features["cape"] > 2000:
        base_rain *= 1.2
    if features["wind_speed"] > 25:
        base_rain *= 1.3
    if features["pressure"] < 998:
        base_rain *= 1.2
    if features["is_peak_monsoon"]:
        base_rain *= 1.15

    lt_factor = LEAD_TIME_DEGRADATION.get(lead_time, 1.0)
    noise = rng.normal(0, base_rain * 0.15 * lt_factor)
    base_rain += noise

    if rng.random() < 0.02:
        base_rain *= rng.uniform(2.0, 4.0)

    return float(max(0, min(base_rain, 400)))


def generate_training_data(n_samples=10000, seed=42):
    rng = np.random.RandomState(seed)
    rows = []
    regime_weights = [0.25, 0.20, 0.15, 0.20, 0.15, 0.05]
    zones = list(ZONE_EFFECTS.keys())

    for _ in range(n_samples):
        regime_idx = rng.choice(6, p=regime_weights)
        regime = REGIMES[regime_idx]
        zone = zones[rng.choice(len(zones))]
        lead_time = rng.choice([24, 48, 72, 96, 120])
        month = rng.choice([6, 7, 8, 9])
        lat = float(rng.uniform(20, 37.5))
        lon = float(rng.uniform(65, 80))

        features = _correlated_features_v2(regime, rng, lat, lon, month)
        raw_rainfall = _calculate_realistic_rainfall(regime, features, zone, lead_time, rng)
        features["raw_rainfall"] = round(raw_rainfall, 2)

        bias = BIAS_FACTORS[regime] + rng.normal(0, 0.1)
        corrected_rainfall = max(0, raw_rainfall / bias + rng.normal(0, raw_rainfall * 0.08))

        row = {
            **features,
            "regime": regime,
            "zone": zone,
            "lead_time": lead_time,
            "observed_rainfall": round(corrected_rainfall, 2),
        }

        for t in [7.5, 64.5, 124.5, 244.5]:
            if corrected_rainfall > t * 1.5:
                prob = rng.uniform(0.85, 0.99)
            elif corrected_rainfall > t:
                prob = rng.uniform(0.50, 0.85)
            elif corrected_rainfall > t * 0.7:
                prob = rng.uniform(0.25, 0.50)
            elif corrected_rainfall > t * 0.4:
                prob = rng.uniform(0.05, 0.25)
            else:
                prob = rng.uniform(0.001, 0.05)
            row[f"p_exceed_{t}"] = float(np.clip(prob, 0, 1))

        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"Generated {n_samples} training samples")
    print(f"Regime distribution:\n{df['regime'].value_counts()}")
    return df


def classify_regime(features):
    best_regime = "break_monsoon"
    best_score = float("inf")
    for regime, profile in REGIME_FEATURE_PROFILES.items():
        score = sum(
            (features.get(k, 0) - (lo + hi) / 2) ** 2 / max((hi - lo) ** 2, 1)
            for k, (lo, hi) in profile.items()
            if k in features
        )
        if score < best_score:
            best_score = score
            best_regime = regime
    return best_regime


def generate_synthetic_forecast(forecast_date="2026-09-09", lead_time=24):
    rng = np.random.RandomState(hash(forecast_date) % 2**31 + lead_time)
    regime_idx = rng.choice(6, p=[0.25, 0.20, 0.15, 0.20, 0.15, 0.05])
    regime = REGIMES[regime_idx]
    confidence = float(np.clip(rng.uniform(0.70, 0.95), 0.70, 0.95))

    from datetime import datetime
    try:
        dt = datetime.strptime(forecast_date[:10], "%Y-%m-%d")
        month = dt.month
    except Exception:
        month = 7

    features = _correlated_features_v2(regime, rng, lat=28.0, lon=77.0, month=month)
    regime_info = {"type": regime, "confidence": confidence, "features": features}

    try:
        from ml.all_districts import DISTRICTS
    except ImportError:
        DISTRICTS = []

    district_forecasts = []

    for d in DISTRICTS:
        zone = d.get("zone", "central")
        dlat = d["centroid_lat"]
        dlon = d["centroid_lon"]
        raw = _calculate_realistic_rainfall(regime, features, zone, lead_time, rng)
        bias = BIAS_FACTORS[regime] + rng.normal(0, 0.08)
        corrected = float(max(0, raw / bias + rng.normal(0, raw * 0.06)))

        district_features = _correlated_features_v2(regime, rng, dlat, dlon, month)
        district_features["raw_rainfall"] = round(raw, 2)
        district_regime = classify_regime(district_features)

        probs = {}
        for t, key in [(7.5, "p_moderate"), (64.5, "p_heavy"), (124.5, "p_very_heavy"), (244.5, "p_extreme")]:
            if corrected > t * 1.5:
                prob = rng.uniform(0.85, 0.99)
            elif corrected > t:
                prob = rng.uniform(0.50, 0.85)
            elif corrected > t * 0.7:
                prob = rng.uniform(0.25, 0.50)
            elif corrected > t * 0.4:
                prob = rng.uniform(0.05, 0.25)
            else:
                prob = rng.uniform(0.001, 0.05)
            probs[key] = round(float(np.clip(prob, 0, 1)), 3)

        district_forecasts.append({
            "district_id": d["district_id"],
            "name": d["district_name"],
            "state": d["state_name"],
            "zone": zone,
            "lat": dlat,
            "lon": dlon,
            "raw": round(raw, 1),
            "corrected": round(corrected, 1),
            "regime": district_regime,
            **probs,
        })

    return {"regime": regime_info, "districts": district_forecasts}


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
