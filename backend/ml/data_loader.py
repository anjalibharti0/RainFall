"""
Unified data loader for IMD observed rainfall + GFS forecasts.
Creates matched forecast-observation pairs for ML training.

V2: Fixed circular features, added temporal/spatial features, proper probability targets.

Usage:
    loader = RealDataLoader(imd_dir="imd_data", gfs_dir="nwp_data")
    df = loader.build_training_dataset(start_date="2024-06-01", end_date="2024-09-30")
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from ml.imd_reader import read_grd, IMD_GRID
from ml.all_districts import DISTRICTS


NWD_BOUNDS = {"lat_min": 20, "lat_max": 37.5, "lon_min": 65, "lon_max": 80}

# V2 feature set: no circular dependencies, physically meaningful
FEATURE_KEYS = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure",
    "radiation", "temp_range", "temp_mean",
    "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude",
]

REGIME_LABEL_RULES = {
    "active_monsoon": {"min_rainfall_percentile": 70, "min_cape": 1000, "min_wind_speed": 12, "min_moisture_index": 0.6},
    "break_monsoon": {"max_rainfall_percentile": 30, "max_cape": 800, "max_wind_speed": 10, "max_moisture_index": 0.4},
    "depression": {"min_cape": 1500, "min_rainfall_percentile": 80, "min_wind_speed": 20},
    "orographic": {"min_wind_speed": 8, "min_radiation": 15, "min_cape": 500},
    "coastal": {"min_moisture_index": 0.5, "min_wind_speed": 10, "min_cape": 800},
    "western_disturbance": {"min_wind_speed": 15, "max_moisture_index": 0.5, "max_cape": 1000},
}

# IMD monsoon phases (Indian standard)
MONSOON_PHASES = {
    6: 1, 7: 2, 8: 2,  # Onset, Peak, Peak
    9: 3,               # Withdrawal
}
PEAK_MONSOON_MONTHS = {7, 8}


class RealDataLoader:
    def __init__(self, imd_dir="imd_data", gfs_dir="nwp_data"):
        self.imd_dir = imd_dir
        self.gfs_dir = gfs_dir
        self._gfs_cache = {}
        self._climatology = None
        self._realtime_cache = {}
        self._realtime_cache_ts = {}

    # ── IMD Observation Loading ──────────────────────────────────

    def load_imd_date(self, date_str):
        """Load IMD rainfall grid for a date (YYYYMMDD). Returns 135x129 array or None."""
        year = date_str[:4]
        dt = datetime.strptime(date_str, "%Y%m%d")
        dd, mm, yy = dt.strftime("%d"), dt.strftime("%m"), dt.strftime("%y")
        day_of_year = dt.timetuple().tm_yday - 1

        year_file = os.path.join(self.imd_dir, f"rain_ind0.25_{year}.grd")
        if os.path.exists(year_file):
            try:
                import struct as _struct
                with open(year_file, "rb") as f:
                    data = f.read()
                n_floats = len(data) // 4
                floats = _struct.unpack(f"<{n_floats}f", data)
                total_cells = IMD_GRID["nrows"] * IMD_GRID["ncols"]
                n_days = n_floats // total_cells
                if day_of_year < n_days:
                    start = day_of_year * total_cells
                    end = start + total_cells
                    arr = np.array(floats[start:end], dtype=np.float32)
                    return arr.reshape(IMD_GRID["nrows"], IMD_GRID["ncols"])
                return None
            except Exception:
                pass

        candidates = [
            f"rain_ind0.25_{dd}_{mm}_{yy}.grd",
            f"rain_ind0.25_{date_str}.grd",
            f"RF25_{dd}{mm}{year}.grd",
        ]
        for fname in candidates:
            for subdir in [year, ""]:
                path = os.path.join(self.imd_dir, subdir, fname) if subdir else os.path.join(self.imd_dir, fname)
                if os.path.exists(path):
                    try:
                        return read_grd(path)
                    except Exception:
                        continue
        return None

    def get_nearest_imd_value(self, grid, target_lat, target_lon):
        """Get IMD rainfall value nearest to a lat/lon point."""
        lats = np.linspace(IMD_GRID["lat_max"], IMD_GRID["lat_min"], IMD_GRID["nrows"])
        lons = np.linspace(IMD_GRID["lon_min"], IMD_GRID["lon_max"], IMD_GRID["ncols"])
        lat_idx = np.argmin(np.abs(lats - target_lat))
        lon_idx = np.argmin(np.abs(lons - target_lon))
        val = float(grid[lat_idx, lon_idx])
        if val == IMD_GRID["missing"] or val < 0:
            return None
        return val

    def load_imd_for_districts(self, date_str, districts=None):
        """Load IMD observed rainfall for all districts on a given date."""
        if districts is None:
            districts = DISTRICTS
        grid = self.load_imd_date(date_str)
        if grid is None:
            return {}
        results = {}
        for d in districts:
            val = self.get_nearest_imd_value(grid, d["centroid_lat"], d["centroid_lon"])
            if val is not None:
                results[d["district_id"]] = val
        return results

    # ── GFS Forecast Loading ─────────────────────────────────────

    def load_gfs_batch(self, year_dir, batch_idx):
        cache_key = f"{year_dir}_{batch_idx}"
        if cache_key in self._gfs_cache:
            return self._gfs_cache[cache_key]
        batches_dir = os.path.join(self.gfs_dir, year_dir)
        if batch_idx < 0:
            path = os.path.join(batches_dir, "gap_combined.json")
        else:
            path = os.path.join(batches_dir, f"batch_{batch_idx:03d}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            self._gfs_cache[cache_key] = data
            return data
        except Exception:
            return None

    def load_gfs_batch_metadata(self, year_dir):
        batches_dir = os.path.join(self.gfs_dir, year_dir)
        if not os.path.isdir(batches_dir):
            return []
        files = sorted([f for f in os.listdir(batches_dir) if f.startswith("batch_") and f.endswith(".json")])
        if os.path.exists(os.path.join(batches_dir, "gap_combined.json")):
            files.append("gap_combined.json")
        return files

    def extract_gfs_date(self, batch_data, date_str):
        """Extract forecast features for a specific date from a GFS batch."""
        if batch_data is None:
            return None

        if isinstance(batch_data, list):
            results = []
            for loc in batch_data:
                if "daily" not in loc:
                    continue
                daily = loc["daily"]
                dates = daily.get("time", [])
                if date_str not in dates:
                    continue
                idx = dates.index(date_str)
                result = {"lat": loc.get("latitude"), "lon": loc.get("longitude")}
                for key in ["precipitation_sum", "temperature_2m_max", "temperature_2m_min",
                             "wind_speed_10m_max", "wind_direction_10m_dominant",
                             "cape_mean", "surface_pressure_mean", "shortwave_radiation_sum"]:
                    vals = daily.get(key, [])
                    if idx < len(vals):
                        result[key] = vals[idx]
                results.append(result)
            return results if results else None

        if "daily" not in batch_data:
            return None
        daily = batch_data["daily"]
        dates = daily.get("time", [])
        if date_str not in dates:
            return None
        idx = dates.index(date_str)
        result = {}
        for key in ["precipitation_sum", "temperature_2m_max", "temperature_2m_min",
                     "wind_speed_10m_max", "wind_direction_10m_dominant",
                     "cape_mean", "surface_pressure_mean", "shortwave_radiation_sum"]:
            vals = daily.get(key, [])
            if idx < len(vals):
                result[key] = vals[idx]
        return result

    def load_gfs_for_date(self, date_str):
        year = date_str[:4]
        batch_files = self.load_gfs_batch_metadata(year)
        if not batch_files:
            return []

        all_points = []
        for batch_file in batch_files:
            if batch_file == "gap_combined.json":
                batch_idx = -1
            else:
                batch_idx = int(batch_file.replace("batch_", "").replace(".json", ""))
            data = self.load_gfs_batch(year, batch_idx)
            if data is None:
                continue
            extracted = self.extract_gfs_date(data, date_str)
            if extracted is None:
                continue
            if isinstance(extracted, list):
                for point in extracted:
                    if "lat" in point and "lon" in point:
                        all_points.append(point)
            elif isinstance(data, dict):
                lats = data.get("latitude", [])
                lons = data.get("longitude", [])
                if not isinstance(lats, list):
                    lats = [lats]
                if not isinstance(lons, list):
                    lons = [lons]
                for k in range(min(len(lats), len(lons))):
                    point = dict(extracted)
                    point["lat"] = lats[k]
                    point["lon"] = lons[k]
                    all_points.append(point)
        return all_points

    # ── V2 Feature Computation (no circular deps) ────────────────

    def compute_ml_features(self, gfs_point, date_str=None):
        """Derive ML features from a single GFS grid point.
        V2: No circular dependencies. All features derived from independent GFS variables only."""
        def _val(key, default):
            v = gfs_point.get(key)
            if v is None:
                return default
            try:
                v = float(v)
            except (TypeError, ValueError):
                return default
            if np.isnan(v):
                return default
            return v

        precip = _val("precipitation_sum", 0.0)
        cape_raw = gfs_point.get("cape_mean")
        cape = float(cape_raw) if isinstance(cape_raw, (int, float)) and not np.isnan(cape_raw) else np.nan
        tmax = _val("temperature_2m_max", 25.0)
        tmin = _val("temperature_2m_min", 20.0)
        wind = _val("wind_speed_10m_max", 0.0)
        wind_dir = _val("wind_direction_10m_dominant", 0.0)
        pressure = _val("surface_pressure_mean", 1013.0)
        radiation = _val("shortwave_radiation_sum", 15.0)

        def _clip_pos(v):
            return round(max(0, v), 1) if not np.isnan(v) else np.nan

        features = {
            "raw_rainfall": round(precip, 2),
            "wind_speed": round(wind, 2),
            "wind_dir": round(wind_dir, 1),
            "cape": _clip_pos(cape),
            "pressure": round(pressure, 1),
            "radiation": _clip_pos(radiation),
            "temp_range": round(max(0, tmax - tmin), 1),
            "temp_mean": round((tmax + tmin) / 2, 1),
        }

        if date_str and len(date_str) >= 8:
            dt = datetime.strptime(date_str[:8], "%Y%m%d")
            features["day_of_year"] = dt.timetuple().tm_yday
            features["month"] = dt.month
            features["monsoon_phase"] = MONSOON_PHASES.get(dt.month, 0)
            features["is_peak_monsoon"] = 1 if dt.month in PEAK_MONSOON_MONTHS else 0
        else:
            features["day_of_year"] = 180
            features["month"] = 7
            features["monsoon_phase"] = 2
            features["is_peak_monsoon"] = 1

        features["latitude"] = gfs_point.get("lat", 0)
        features["longitude"] = gfs_point.get("lon", 0)

        return features

    # ── V2 Regime Labeling (improved rules) ──────────────────────

    def _compute_moisture_index(self, features):
        """Moisture index from CAPE + wind + pressure (no precipitation dependency)."""
        cape = features.get("cape", 500)
        wind = features.get("wind_speed", 0)
        pressure = features.get("pressure", 1013)
        temp_mean = features.get("temp_mean", 27)
        mi = (cape / 3000) * 0.4 + (wind / 30) * 0.3 + ((1013 - pressure) / 40) * 0.2 + max(0, (temp_mean - 25) / 10) * 0.1
        return round(np.clip(mi, 0, 1), 3)

    def label_regime(self, features, observed_rainfall=None):
        """Classify weather regime from atmospheric features.
        V2: Uses moisture index instead of circular humidity_700."""
        mi = self._compute_moisture_index(features)
        candidates = {}

        score = 0
        if features.get("wind_speed", 0) > 12: score += 1
        if features.get("cape", 0) > 1000: score += 1
        if mi > 0.6: score += 1
        if observed_rainfall and observed_rainfall > 15: score += 1
        candidates["active_monsoon"] = score / 4

        score = 0
        if features.get("wind_speed", 0) < 10: score += 1
        if features.get("cape", 0) < 800: score += 1
        if mi < 0.4: score += 1
        if observed_rainfall is not None and observed_rainfall < 5: score += 1
        candidates["break_monsoon"] = score / 4

        score = 0
        if features.get("cape", 0) > 1500: score += 1
        if features.get("wind_speed", 0) > 20: score += 1
        if mi > 0.5: score += 1
        if observed_rainfall and observed_rainfall > 30: score += 1
        candidates["depression"] = score / 4

        score = 0
        if 8 < features.get("wind_speed", 0) < 20: score += 1
        if features.get("radiation", 0) > 15: score += 1
        if features.get("cape", 0) > 500: score += 1
        candidates["orographic"] = score / 3

        score = 0
        if mi > 0.5: score += 1
        if features.get("wind_speed", 0) > 10: score += 1
        if features.get("cape", 0) > 800: score += 1
        candidates["coastal"] = score / 3

        score = 0
        if features.get("wind_speed", 0) > 15: score += 1
        if mi < 0.5: score += 1
        if features.get("cape", 0) < 1000: score += 1
        candidates["western_disturbance"] = score / 3

        best = max(candidates, key=candidates.get)
        confidence = round(candidates[best], 4)
        return best, confidence

    # ── Climatology for probability targets ───────────────────────

    def build_climatology(self, start_date="2022-06-01", end_date="2024-09-30"):
        """Build rainfall climatology for each district from IMD data.
        Used to compute proper exceedance probability targets."""
        if self._climatology is not None:
            return self._climatology

        print("  Building rainfall climatology from IMD data...")
        clim = {}
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        dates_read = 0

        while current <= end:
            date_str = current.strftime("%Y%m%d")
            month = current.month
            if month in range(6, 10):
                grid = self.load_imd_date(date_str)
                if grid is not None:
                    lats = np.linspace(IMD_GRID["lat_max"], IMD_GRID["lat_min"], IMD_GRID["nrows"])
                    lons = np.linspace(IMD_GRID["lon_min"], IMD_GRID["lon_max"], IMD_GRID["ncols"])
                    for d in DISTRICTS:
                        did = d["district_id"]
                        val = self.get_nearest_imd_value(grid, d["centroid_lat"], d["centroid_lon"])
                        if val is not None:
                            key = (did, month)
                            if key not in clim:
                                clim[key] = []
                            clim[key].append(val)
                    dates_read += 1
            current += timedelta(days=1)

        self._climatology = {}
        for key, values in clim.items():
            arr = np.array(values)
            self._climatology[key] = {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "percentiles": {
                    10: float(np.percentile(arr, 10)),
                    25: float(np.percentile(arr, 25)),
                    50: float(np.percentile(arr, 50)),
                    75: float(np.percentile(arr, 75)),
                    90: float(np.percentile(arr, 90)),
                    95: float(np.percentile(arr, 95)),
                },
                "n": len(arr),
            }
        print(f"  Climatology built for {len(self._climatology)} district-month combos from {dates_read} dates")
        return self._climatology

    def compute_exceedance_probabilities(self, observed, district_id, month, climatology=None):
        """Compute exceedance probability targets using climatological distribution.
        V2: Uses actual IMD rainfall distribution instead of random noise."""
        thresholds = [7.5, 64.5, 124.5, 244.5]
        probs = {}

        if climatology is None:
            climatology = self._climatology or {}

        key = (district_id, month)
        if key in climatology:
            dist = climatology[key]
            pcts = dist["percentiles"]
            for t in thresholds:
                if observed >= pcts[95]:
                    p_exceed = 0.95 + 0.04 * min(1, (observed - pcts[95]) / max(pcts[95], 1))
                elif observed >= pcts[90]:
                    p_exceed = 0.85 + 0.10 * ((observed - pcts[90]) / max(pcts[90] - pcts[75], 1))
                elif observed >= pcts[75]:
                    p_exceed = 0.50 + 0.35 * ((observed - pcts[75]) / max(pcts[75] - pcts[50], 1))
                elif observed >= pcts[50]:
                    p_exceed = 0.20 + 0.30 * ((observed - pcts[50]) / max(pcts[50] - pcts[25], 1))
                elif observed >= pcts[25]:
                    p_exceed = 0.05 + 0.15 * ((observed - pcts[25]) / max(pcts[25] - pcts[10], 1))
                elif observed >= pcts[10]:
                    p_exceed = 0.01 + 0.04 * ((observed - pcts[10]) / max(pcts[10], 1))
                else:
                    p_exceed = max(0.001, 0.01 * (observed / max(pcts[10], 0.1)))
                probs[f"p_exceed_{t}"] = round(float(np.clip(p_exceed, 0, 1)), 4)
        else:
            for t in thresholds:
                if observed > t * 1.5:
                    probs[f"p_exceed_{t}"] = 0.90
                elif observed > t:
                    probs[f"p_exceed_{t}"] = 0.60
                elif observed > t * 0.5:
                    probs[f"p_exceed_{t}"] = 0.20
                elif observed > t * 0.2:
                    probs[f"p_exceed_{t}"] = 0.05
                else:
                    probs[f"p_exceed_{t}"] = 0.01

        return probs

    # ── Dataset Building ─────────────────────────────────────────

    def build_training_dataset(self, start_date, end_date, districts=None, build_clim=True):
        """Build training dataset by pairing IMD observations with GFS forecasts.
        V2: Proper probability targets, temporal/spatial features, no circular deps."""
        if districts is None:
            districts = DISTRICTS

        if build_clim:
            clim_start = str(max(2020, int(start_date[:4]) - 2)) + start_date[4:]
            self.build_climatology(clim_start, end_date)

        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        rows = []
        dates_processed = 0

        while current <= end:
            date_str = current.strftime("%Y%m%d")
            iso_date = current.strftime("%Y-%m-%d")
            month = current.month

            imd_data = self.load_imd_for_districts(date_str, districts)
            if not imd_data:
                current += timedelta(days=1)
                continue

            gfs_points = self.load_gfs_for_date(iso_date)
            gfs_by_location = {}
            for gp in gfs_points:
                g_lat, g_lon = gp.get("lat"), gp.get("lon")
                if g_lat is None or g_lon is None:
                    continue
                key = (round(float(g_lat), 2), round(float(g_lon), 2))
                gfs_by_location[key] = gp

            matched = 0
            for d in districts:
                did = d["district_id"]
                if did not in imd_data:
                    continue

                observed = imd_data[did]
                d_lat, d_lon = d["centroid_lat"], d["centroid_lon"]

                best_gp = None
                best_dist = float("inf")
                for (g_lat, g_lon), gp in gfs_by_location.items():
                    dist = abs(g_lat - d_lat) + abs(g_lon - d_lon)
                    if dist < best_dist:
                        best_dist = dist
                        best_gp = gp

                if best_gp is None or best_dist > 2.0:
                    continue

                features = self.compute_ml_features(best_gp, date_str)
                regime, confidence = self.label_regime(features, observed)

                p_targets = self.compute_exceedance_probabilities(observed, did, month)

                row = {
                    "date": iso_date,
                    "district_id": did,
                    "name": d.get("district_name", ""),
                    "state": d.get("state_name", ""),
                    "zone": d.get("zone", "central"),
                    "lat": d_lat,
                    "lon": d_lon,
                    "raw_rainfall": features["raw_rainfall"],
                    "observed_rainfall": round(observed, 2),
                    "regime": regime,
                    "regime_confidence": confidence,
                    "lead_time": 24,
                    **features,
                    **p_targets,
                }
                rows.append(row)
                matched += 1

            if matched > 0:
                dates_processed += 1
                if dates_processed % 10 == 0:
                    print(f"  Processed {dates_processed} dates, {len(rows)} rows so far...")

            current += timedelta(days=1)

        df = pd.DataFrame(rows)
        print(f"\nDataset built: {len(df)} rows from {dates_processed} dates")
        if len(df) > 0:
            print(f"Regime distribution:\n{df['regime'].value_counts()}")
        return df

    def load_realtime_features(self, districts, date_str):
        """Fetch real-time features from Open-Meteo API for live predictions.
        Results are cached per date for 6 hours (the Open-Meteo rollout of the
        forecast for a given day changes slowly within a day)."""
        import time as _time
        now = _time.time()
        if date_str in self._realtime_cache and (now - self._realtime_cache_ts.get(date_str, 0)) < 6 * 3600:
            return self._realtime_cache[date_str]

        from ml.weather_api import fetch_district_weather, get_aggregate_features

        district_weather = {}
        batch_size = 40
        district_list = list(districts)

        for i in range(0, len(district_list), batch_size):
            batch = district_list[i:i + batch_size]
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = {pool.submit(fetch_district_weather, d, date_str): d["district_id"] for d in batch}
                for f in as_completed(futures):
                    did = futures[f]
                    try:
                        result = f.result()
                        if result:
                            district_weather[did] = result
                    except Exception:
                        pass

        result = (district_weather, get_aggregate_features(district_weather))
        self._realtime_cache[date_str] = result
        self._realtime_cache_ts[date_str] = now
        return result
