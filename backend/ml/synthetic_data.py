import numpy as np
import pandas as pd

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]

REGIME_FEATURE_PROFILES = {
    "active_monsoon": {
        "wind_shear": (15, 25),
        "olr": (-30, -10),
        "cape": (1000, 2500),
        "vorticity": (1.5, 4.0),
        "moisture_flux": (200, 500),
        "humidity_700": (70, 90),
        "pressure": (998, 1005),
        "sst": (28, 31),
    },
    "break_monsoon": {
        "wind_shear": (5, 12),
        "olr": (0, 15),
        "cape": (200, 800),
        "vorticity": (-0.5, 1.0),
        "moisture_flux": (50, 150),
        "humidity_700": (40, 65),
        "pressure": (1006, 1012),
        "sst": (27, 29),
    },
    "depression": {
        "wind_shear": (10, 20),
        "olr": (-40, -15),
        "cape": (1500, 3500),
        "vorticity": (2.5, 6.0),
        "moisture_flux": (300, 700),
        "humidity_700": (75, 95),
        "pressure": (990, 1000),
        "sst": (29, 32),
    },
    "orographic": {
        "wind_shear": (8, 18),
        "olr": (-20, -5),
        "cape": (500, 1500),
        "vorticity": (0.5, 2.5),
        "moisture_flux": (150, 400),
        "humidity_700": (60, 85),
        "pressure": (1002, 1008),
        "sst": (27, 30),
    },
    "coastal": {
        "wind_shear": (6, 15),
        "olr": (-15, 0),
        "cape": (800, 2000),
        "vorticity": (0.3, 2.0),
        "moisture_flux": (200, 450),
        "humidity_700": (65, 88),
        "pressure": (1003, 1009),
        "sst": (28, 31),
    },
    "western_disturbance": {
        "wind_shear": (12, 22),
        "olr": (-10, 5),
        "cape": (300, 1000),
        "vorticity": (0.8, 3.0),
        "moisture_flux": (100, 300),
        "humidity_700": (45, 70),
        "pressure": (1004, 1012),
        "sst": (24, 28),
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

# Regional effects - some zones get more rainfall
ZONE_EFFECTS = {
    "west_coast": 1.4,
    "central": 1.1,
    "north": 0.9,
    "east": 1.2,
    "south": 1.0,
    "northeast": 1.5,
}

# Lead time degradation - forecasts get worse further out
LEAD_TIME_DEGRADATION = {
    24: 1.0,
    48: 1.15,
    72: 1.35,
    96: 1.60,
    120: 1.90,
}

FEATURE_NAMES = ["wind_shear", "olr", "cape", "vorticity", "moisture_flux", "humidity_700", "pressure", "sst"]


def _sample(profile, size=1):
    lo, hi = profile
    if size == 1:
        return float(np.random.uniform(lo, hi))
    return np.random.uniform(lo, hi, size)


def _correlated_features(regime, rng):
    """Generate correlated features for a regime - not independent."""
    fp = REGIME_FEATURE_PROFILES[regime]

    wind_shear = _sample(fp["wind_shear"])
    olr = _sample(fp["olr"])
    cape = _sample(fp["cape"])
    vorticity = _sample(fp["vorticity"])
    moisture_flux = _sample(fp["moisture_flux"])
    humidity_700 = _sample(fp["humidity_700"])
    pressure = _sample(fp["pressure"])
    sst = _sample(fp["sst"])

    # Add correlations - high wind shear often means high vorticity
    vorticity += (wind_shear - 15) * 0.1 + rng.normal(0, 0.2)
    cape += (humidity_700 - 70) * 15 + rng.normal(0, 50)
    moisture_flux += (humidity_700 - 70) * 5 + rng.normal(0, 20)
    olr -= (cape - 1000) * 0.005 + rng.normal(0, 1)

    return {
        "wind_shear": float(np.clip(wind_shear, 0, 40)),
        "olr": float(np.clip(olr, -50, 25)),
        "cape": float(np.clip(cape, 0, 5000)),
        "vorticity": float(np.clip(vorticity, -2, 8)),
        "moisture_flux": float(np.clip(moisture_flux, 0, 800)),
        "humidity_700": float(np.clip(humidity_700, 20, 100)),
        "pressure": float(np.clip(pressure, 985, 1020)),
        "sst": float(np.clip(sst, 20, 35)),
    }


def _calculate_realistic_rainfall(regime, features, zone, lead_time, rng):
    """Calculate realistic rainfall based on regime, features, zone, and lead time."""
    rp = REGIME_RAINFALL_PROFILES[regime]
    base_rain = _sample(rp)

    # Zone adjustment
    zone_factor = ZONE_EFFECTS.get(zone, 1.0)
    base_rain *= zone_factor

    # Feature-based adjustment
    if features["humidity_700"] > 80:
        base_rain *= 1.3
    elif features["humidity_700"] < 50:
        base_rain *= 0.6

    if features["cape"] > 2000:
        base_rain *= 1.2

    if features["vorticity"] > 3:
        base_rain *= 1.4

    # Lead time makes forecast less accurate
    lt_factor = LEAD_TIME_DEGRADATION.get(lead_time, 1.0)
    noise = rng.normal(0, base_rain * 0.15 * lt_factor)
    base_rain += noise

    # Add occasional extreme events (2% chance)
    if rng.random() < 0.02:
        base_rain *= rng.uniform(2.0, 4.0)

    return float(max(0, min(base_rain, 400)))


def generate_training_data(n_samples=10000, seed=42):
    """Generate strong synthetic training data with realistic patterns."""
    rng = np.random.RandomState(seed)
    rows = []
    regime_weights = [0.25, 0.20, 0.15, 0.20, 0.15, 0.05]
    zones = list(ZONE_EFFECTS.keys())

    for _ in range(n_samples):
        regime_idx = rng.choice(6, p=regime_weights)
        regime = REGIMES[regime_idx]
        zone = zones[rng.choice(len(zones))]
        lead_time = rng.choice([24, 48, 72, 96, 120])

        features = _correlated_features(regime, rng)
        raw_rainfall = _calculate_realistic_rainfall(regime, features, zone, lead_time, rng)

        # Bias correction
        bias = BIAS_FACTORS[regime] + rng.normal(0, 0.1)
        corrected_rainfall = max(0, raw_rainfall / bias + rng.normal(0, raw_rainfall * 0.08))

        row = {
            **features,
            "raw_rainfall": round(raw_rainfall, 2),
            "regime": regime,
            "zone": zone,
            "lead_time": lead_time,
            "corrected_rainfall": round(corrected_rainfall, 2),
        }

        # Calculate exceedance probabilities using logistic function
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
    """Generate synthetic forecast with realistic patterns."""
    rng = np.random.RandomState(hash(forecast_date) % 2**31 + lead_time)
    regime_idx = rng.choice(6, p=[0.25, 0.20, 0.15, 0.20, 0.15, 0.05])
    regime = REGIMES[regime_idx]
    confidence = float(np.clip(rng.uniform(0.70, 0.95), 0.70, 0.95))
    features = _correlated_features(regime, rng)
    regime_info = {"type": regime, "confidence": confidence, "features": features}

    # Read districts from file
    try:
        from ml.all_districts import DISTRICTS
    except ImportError:
        DISTRICTS = []

    lead_factor = LEAD_TIME_DEGRADATION.get(lead_time, 1.0)
    district_forecasts = []

    for d in DISTRICTS:
        zone = d.get("zone", "central")
        raw = _calculate_realistic_rainfall(regime, features, zone, lead_time, rng)
        bias = BIAS_FACTORS[regime] + rng.normal(0, 0.08)
        corrected = float(max(0, raw / bias + rng.normal(0, raw * 0.06)))

        thresholds = {}
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
            thresholds[key] = round(float(np.clip(prob, 0, 1)), 3)

        district_forecasts.append({
            "district_id": d["district_id"],
            "name": d["district_name"],
            "state": d["state_name"],
            "zone": zone,
            "lat": d["centroid_lat"],
            "lon": d["centroid_lon"],
            "raw": round(raw, 1),
            "corrected": round(corrected, 1),
            "regime": regime,
            **thresholds,
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
