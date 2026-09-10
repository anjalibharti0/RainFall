import numpy as np
import pandas as pd

REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]

DISTRICTS = [
    {"district_id": 1, "district_name": "Mumbai", "state_name": "Maharashtra", "centroid_lat": 19.076, "centroid_lon": 72.8777, "zone": "west_coast"},
    {"district_id": 2, "district_name": "Pune", "state_name": "Maharashtra", "centroid_lat": 18.5204, "centroid_lon": 73.8567, "zone": "west_coast"},
    {"district_id": 3, "district_name": "Nagpur", "state_name": "Maharashtra", "centroid_lat": 21.1458, "centroid_lon": 79.0882, "zone": "central"},
    {"district_id": 4, "district_name": "Delhi", "state_name": "Delhi", "centroid_lat": 28.7041, "centroid_lon": 77.1025, "zone": "north"},
    {"district_id": 5, "district_name": "Kolkata", "state_name": "West Bengal", "centroid_lat": 22.5726, "centroid_lon": 88.3639, "zone": "east"},
    {"district_id": 6, "district_name": "Chennai", "state_name": "Tamil Nadu", "centroid_lat": 13.0827, "centroid_lon": 80.2707, "zone": "south"},
    {"district_id": 7, "district_name": "Bengaluru", "state_name": "Karnataka", "centroid_lat": 12.9716, "centroid_lon": 77.5946, "zone": "south"},
    {"district_id": 8, "district_name": "Hyderabad", "state_name": "Telangana", "centroid_lat": 17.385, "centroid_lon": 78.4867, "zone": "south"},
    {"district_id": 9, "district_name": "Ahmedabad", "state_name": "Gujarat", "centroid_lat": 23.0225, "centroid_lon": 72.5714, "zone": "west"},
    {"district_id": 10, "district_name": "Jaipur", "state_name": "Rajasthan", "centroid_lat": 26.9124, "centroid_lon": 75.7873, "zone": "north"},
    {"district_id": 11, "district_name": "Lucknow", "state_name": "Uttar Pradesh", "centroid_lat": 26.8467, "centroid_lon": 80.9462, "zone": "north"},
    {"district_id": 12, "district_name": "Patna", "state_name": "Bihar", "centroid_lat": 25.6093, "centroid_lon": 85.1376, "zone": "north"},
    {"district_id": 13, "district_name": "Bhopal", "state_name": "Madhya Pradesh", "centroid_lat": 23.2599, "centroid_lon": 77.4126, "zone": "central"},
    {"district_id": 14, "district_name": "Guwahati", "state_name": "Assam", "centroid_lat": 26.1445, "centroid_lon": 91.7362, "zone": "northeast"},
    {"district_id": 15, "district_name": "Srinagar", "state_name": "Jammu & Kashmir", "centroid_lat": 34.0837, "centroid_lon": 74.7973, "zone": "north"},
    {"district_id": 16, "district_name": "Thiruvananthapuram", "state_name": "Kerala", "centroid_lat": 8.5241, "centroid_lon": 76.9366, "zone": "south"},
    {"district_id": 17, "district_name": "Visakhapatnam", "state_name": "Andhra Pradesh", "centroid_lat": 17.6868, "centroid_lon": 83.2185, "zone": "east"},
    {"district_id": 18, "district_name": "Indore", "state_name": "Madhya Pradesh", "centroid_lat": 22.7196, "centroid_lon": 75.8577, "zone": "central"},
    {"district_id": 19, "district_name": "Chandigarh", "state_name": "Chandigarh", "centroid_lat": 30.7333, "centroid_lon": 76.7794, "zone": "north"},
    {"district_id": 20, "district_name": "Shimla", "state_name": "Himachal Pradesh", "centroid_lat": 31.1048, "centroid_lon": 77.1734, "zone": "north"},
]

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


def generate_synthetic_forecast(forecast_date="2026-09-09", lead_time=24):
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
