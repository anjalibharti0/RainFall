"""PAST-YEAR REAL-WORLD VERIFICATION: exact served pipeline (v15 + damp) vs
actual IMD observed rainfall for every day of 2025, at T+24 AND T+72.

Method (identical to the served path / verify_all.py, vectorized for speed):
  * Raw NWP features per district are reconstructed from the ERA5 reanalysis
    archive (same source/grid as the era5_gap training files), at each district
    centroid for 2025-01-01..2025-12-31.
  * Features computed with the SAME compute_ml_features() used by the API.
  * Observed = IMD 0.25deg grid (rain_ind0.25_2025.grd), same
    get_nearest_imd_value() as everywhere.
  * Predictions = the same math as main._predict_district():
      regime_probs -> regime-weighted soft bias correction -> dry/wet hurdle ->
      probability estimator (scaled by wet_prob) -> consistency damp.
    implemented vector-over-matrix so it mirrors main.py exactly while being fast.
"""
import sys
import os
import time
import json
import requests
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.all_districts import DISTRICTS
from ml.data_loader import RealDataLoader
from ml.model_registry import ModelRegistry
from ml.regime_classifier import RegimeClassifier, REGIMES
from ml.bias_corrector import BiasCorrector
from ml.probability_estimator import ProbabilityEstimator, THRESHOLDS
import ml.probability_estimator as pemod
from ml.dry_wet_model import DryWetModel
from ml.synthetic_data import compute_verification_metrics
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             brier_score_loss, roc_auc_score, r2_score, confusion_matrix)
from scipy.stats import pearsonr, spearmanr

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
ERA5_DAILY = [
    "precipitation_sum", "temperature_2m_max", "temperature_2m_min",
    "wind_speed_10m_max", "wind_direction_10m_dominant",
    "cape_mean", "surface_pressure_mean", "shortwave_radiation_sum",
]
START, END = "2025-01-01", "2025-12-31"
BC_FEATURES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure", "radiation",
    "temp_range", "temp_mean", "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude", "lead_time",
]


def fetch_era5_batch(lats, lons, retries=10):
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(ARCHIVE_URL, params={
                "latitude": lats, "longitude": lons,
                "start_date": START, "end_date": END,
                "daily": ",".join(ERA5_DAILY),
                "timezone": "Asia/Kolkata",
            }, timeout=90)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            last = e
            if e.response is not None and e.response.status_code == 429:
                time.sleep(6.0 * (attempt + 1))
            else:
                time.sleep(2.0 * (attempt + 1))
        except Exception as e:
            last = e
            time.sleep(2.0 * (attempt + 1))
    print(f"  WARN: batch failed after {retries} tries: {last}")
    return None


def build_features(district, daily, date_iso, compute):
    """Compute features exactly like the served pipeline for one district+date."""
    i = daily["time"].index(date_iso) if date_iso in daily["time"] else None
    if i is None:
        return None
    gp = {"lat": district["centroid_lat"], "lon": district["centroid_lon"]}
    for key in ERA5_DAILY:
        vals = daily.get(key, [])
        gp[key] = vals[i] if i < len(vals) else None
    return compute(gp, date_iso.replace("-", ""))


def main():
    registry = ModelRegistry()
    latest = registry.get_latest_version()
    rc = RegimeClassifier(); bc = BiasCorrector(); pe = ProbabilityEstimator(); dw = DryWetModel()
    latest.load_models(rc, bc, pe, dw)
    print(f"MODEL: {latest.version_name}")

    data_loader = RealDataLoader()

    # ---- 1) fetch ERA5 features for all districts (batched, disk-cached) ----
    cache_dir = "era5_cache_2025"
    os.makedirs(cache_dir, exist_ok=True)
    print(f"Fetching ERA5 reanalysis features for {len(DISTRICTS)} districts, {START}..{END}...")
    era5 = {}
    for f in sorted(os.listdir(cache_dir)):
        did = f.replace(".json", "")
        try:
            with open(os.path.join(cache_dir, f)) as fh:
                era5[int(did)] = json.load(fh)
        except Exception:
            pass
    print(f"  cache: {len(era5)} districts")
    B = 50
    todo = [d for d in DISTRICTS if d["district_id"] not in era5]
    fetched = 0
    if os.environ.get("SKIP_FETCH") == "1":
        print(f"  skip-fetch: using {len(era5)} cached districts only, todo={len(todo)}")
    if os.environ.get("SKIP_FETCH") != "1":
        for start in range(0, len(todo), B):
            chunk = todo[start:start + B]
            lats = ",".join(str(d["centroid_lat"]) for d in chunk)
            lons = ",".join(str(d["centroid_lon"]) for d in chunk)
            res = fetch_era5_batch(lats, lons)
            if res is None:
                continue
            for d, elem in zip(chunk, res):
                daily = elem.get("daily") if isinstance(elem, dict) else None
                if daily and daily.get("time"):
                    era5[d["district_id"]] = daily
                    with open(os.path.join(cache_dir, f"{d['district_id']}.json"), "w") as fh:
                        json.dump(daily, fh)
                    fetched += 1
            print(f"  era5 fetched {len(era5)}/{len(DISTRICTS)} districts")
            time.sleep(1.2)

    # ---- 2) build one big feature matrix over available dates ----
    print("Building feature matrix + observed...")
    dates = pd.date_range(START, END).strftime("%Y%m%d").tolist()
    recs = []
    ndates = 0
    for dd in dates:
        imd_grid = data_loader.load_imd_date(dd)
        if imd_grid is None:
            continue
        iso = dd[:4] + "-" + dd[4:6] + "-" + dd[6:8]
        for d in DISTRICTS:
            daily = era5.get(d["district_id"])
            if not daily:
                continue
            feats = build_features(d, daily, iso, data_loader.compute_ml_features)
            if feats is None:
                continue
            obs = data_loader.get_nearest_imd_value(imd_grid, d["centroid_lat"], d["centroid_lon"])
            if obs is None:
                continue
            recs.append({
                "date": iso,
                "district_id": d["district_id"],
                "name": d.get("district_name", ""),
                "state": d.get("state_name", ""),
                "zone": d.get("zone", ""),
                "observed": round(float(obs), 2),
                **feats,
            })
        ndates += 1
        if ndates % 30 == 0:
            print(f"  rows so far: {len(recs)} ({ndates} dates)")
    df = pd.DataFrame(recs)
    df = df.sort_values(["date", "district_id"]).reset_index(drop=True)
    print(f"RECORDS: {len(df)} district-days over {df['date'].nunique()} dates")

    # ---- 3) served pipeline (vectorized, mirrors main._predict_district) ----
    results = {}
    for lt in (24, 72):
        ev = df.copy()
        ev["lead_time"] = lt
        obs = ev["observed"].values.astype(np.float64)
        raw = ev["raw_rainfall"].values.astype(np.float64)

        Xrc = ev[rc._feature_names].values.astype(np.float64)
        probs_all = rc.model.predict_proba(Xrc)
        classes = rc.le.inverse_transform(rc.model.classes_.astype(int)).tolist()
        idx_of = {c: j for j, c in enumerate(classes)}
        reg_list = list(bc.correctors.keys())
        pM = np.zeros((len(ev), len(reg_list)))
        for j, c in enumerate(reg_list):
            if c in idx_of:
                pM[:, j] = probs_all[:, idx_of[c]]
        pM /= pM.sum(axis=1, keepdims=True)

        Xb = ev[BC_FEATURES].values.astype(np.float64)
        corr = np.zeros((len(ev), len(reg_list)))
        for j, c in enumerate(reg_list):
            corr[:, j] = np.clip(bc.correctors[c].predict(Xb), 0, None)
        soft = np.sum(pM * corr, axis=1)

        Xdw = ev[dw._feature_names].values.astype(np.float64)
        wet_prob = dw.model.predict_proba(Xdw)[:, 1]
        zero_mask = (raw < 2.0) & (wet_prob < dw.zero_threshold)
        soft = soft.copy()
        soft[zero_mask] = 0.0

        # Served path feeds the CORRECTED value into the probability estimator:
        #   probs = prob_est.predict(corrected, ...)
        def _pe_probs_at(x):
            Xpe = ev[pemod.FEATURE_NAMES].values.astype(np.float64)
            Xpe[:, 0] = x
            out = {}
            for t in THRESHOLDS:
                if t in pe.models:
                    p = pe.models[t].predict_proba(Xpe)[:, 1]
                else:
                    p = 1 / (1 + np.exp(0.06 * (t - raw)))
                out[t] = np.clip(p, 0, 1)
            return out

        p_scale = np.minimum(1.0, wet_prob)
        probsA = _pe_probs_at(soft)                      # probs at corrected (pre-damp)
        damp = (raw < 2.0) & (soft > raw) & (probsA[7.5] * p_scale < 0.5) & (probsA[64.5] * p_scale < 0.05)
        served = soft.copy()
        served[damp] = raw[damp] + (soft[damp] - raw[damp]) * (probsA[7.5][damp] * p_scale[damp] / 0.5)
        probsB = _pe_probs_at(served)                    # final served probabilities (at damped value)
        probsB = {t: np.clip(p, 0, 1) * p_scale for t, p in probsB.items()}

        results[lt] = {"df": ev, "obs": obs, "raw": raw, "served": served,
                       "probs": probsB, "params": {"zero_mask_n": int(zero_mask.sum()),
                                                   "damp_n": int(damp.sum())}}
        print(f"  T+{lt}: damp applied on {int(damp.sum())} rows, zeroed {int(zero_mask.sum())}")

    # ---- 4) report each lead time ----
    from scipy.stats import norm
    for lt in (24, 72):
        ev = results[lt]["df"]; obs = results[lt]["obs"]; raw = results[lt]["raw"]
        served = results[lt]["served"]; probs = results[lt]["probs"]
        n = len(ev)
        print("\n" + "#" * 84)
        print(f"# 2025 FULL-YEAR REAL-WORLD VERIFICATION (served v15 pipeline)  ->  T+{lt}h")
        print("#" * 84)
        print(f"  matched district-days: {n}  (dates {ev['date'].min()} .. {ev['date'].max()}, "
              f"{ev['date'].nunique()} dates, {ev['district_id'].nunique()} districts)")

        # continuous
        print("\n  -- continuous accuracy (vs exact IMD observed) --")
        def kge(y, f):
            r = pearsonr(y, f)[0] if np.std(y) and np.std(f) else 0
            a = np.std(f) / np.std(y) if np.std(y) else 1
            b = np.mean(f) / np.mean(y) if np.mean(y) else 1
            return 1 - np.sqrt((r - 1) ** 2 + (a - 1) ** 2 + (b - 1) ** 2)
        print(f"  {'':>9}{'RMSE':>8}{'MAE':>7}{'medAE':>7}{'P90':>8}{'P99':>8}{'MAX':>8}{'R2':>8}{'r':>7}{'rho':>7}{'bias':>7}{'KGE':>7}")
        for nm, f in (("raw", raw), ("served", served)):
            ae = np.abs(f - obs)
            rmse = float(np.sqrt(np.mean((f - obs) ** 2)))
            print(f"  {nm:>9}{rmse:>8.2f}{np.mean(ae):>7.2f}{np.median(ae):>7.2f}"
                  f"{np.quantile(ae, .9):>8.2f}{np.quantile(ae, .99):>8.2f}{np.max(ae):>8.1f}"
                  f"{r2_score(obs, f):>8.3f}{pearsonr(obs, f)[0]:>7.3f}"
                  f"{spearmanr(obs, f)[0]:>7.3f}"
                  f"{np.mean(f)/np.mean(obs) if np.mean(obs) else 1:>7.2f}"
                  f"{kge(obs, f):>7.3f}")

        # classification accuracy / precision / recall / F1 (wet vs dry)
        print("\n  -- wet-day classification (threshold 2.5mm) --")
        y = obs >= 2.5
        for nm, f in (("raw", raw), ("served", served)):
            pred = f >= 2.5
            print(f"  {nm:>8}: accuracy={accuracy_score(y, pred):.4f}  "
                  f"precision={precision_score(y, pred, zero_division=0):.4f}  "
                  f"recall={recall_score(y, pred, zero_division=0):.4f}  "
                  f"F1={f1_score(y, pred, zero_division=0):.4f}  "
                  f"obs_wet={int(y.sum())}({100*np.mean(y):.1f}%) pred_wet={int(pred.sum())}")

        # categorical contingency per threshold
        print("\n  -- threshold contingency verification --")
        print(f"  {'thr':>8}{'meth':>8}{'ev':>7}{'POD':>7}{'FAR':>7}{'CSI':>7}{'ETS':>7}{'freqB':>9}")
        for t in [7.5, 24.5, 64.5, 124.5, 244.5]:
            yt = obs >= t; nev = int(yt.sum())
            for nm, f in (("raw", raw), ("served", served)):
                m = compute_verification_metrics(obs, f, threshold=t)
                fct = int(np.sum(f >= t))
                print(f"  {t:>7}mm{nm:>8}{nev:>7}{m['pod']:>7.3f}{m['far']:>7.3f}{m['csi']:>7.3f}"
                      f"{m['ets']:>7.3f}{fct/max(nev,1):>9.2f}")

        # probabilistic
        print("\n  -- probabilistic verification (served P>=X vs observed) --")
        p_cols = {7.5: "p_moderate", 64.5: "p_heavy", 124.5: "p_violent", 244.5: "p_extreme"}
        for t in [7.5, 64.5, 124.5, 244.5]:
            yt = obs >= t; p = probs[t]
            bs = brier_score_loss(yt, p)
            clim = np.mean(yt); unc = clim * (1 - clim)
            bss = 1 - bs / unc if unc > 0 else np.nan
            auc = roc_auc_score(yt, p) if 0 < np.sum(yt) < len(yt) else np.nan
            print(f"  >= {t:>6}mm: Brier={bs:.4f}  BSS={bss:+.3f}  AUC={auc:.4f}  climatology={clim:.4f}")

        # monthly breakdown
        print("\n  -- monthly RMSE (raw vs served) --")
        print(f"  {'month':>8}{'n':>8}{'raw':>9}{'served':>9}{'gain%':>9}")
        ev["_ym"] = ev["date"].str[:7]
        for ym, g in ev.groupby("_ym"):
            o = g["observed"].values; r = g["raw_rainfall"].values
            s = served[g.index]
            rr = float(np.sqrt(np.mean((r - o) ** 2))); rs = float(np.sqrt(np.mean((s - o) ** 2)))
            print(f"  {ym:>8}{len(g):>8}{rr:>9.2f}{rs:>9.2f}{100*(1-rs/rr) if rr else 0:>9.1f}")

        # worst-case
        print("\n  -- worst-case audit --")
        top = np.argsort(-np.abs(served - obs))[:10]
        print("  top-10 largest errors (date | district | raw | served | obs):")
        for i in top:
            r_ = ev.iloc[i]
            print(f"  {r_['date']} {r_['name']:<18} raw={raw[i]:7.1f} served={served[i]:7.1f} obs={obs[i]:7.1f}")
        contra = int(np.sum((served >= 10) & (probs[7.5] < 0.4)))
        big = int(np.sum((served >= obs + 10) & (obs < 10)))
        miss = int(np.sum((served < obs - 10) & (obs >= 10)))
        print(f"  contradictions (served>=10 but P7.5<0.4) : {contra}  ({100*contra/n:.2f}%)")
        print(f"  false blowups (served>=obs+10, obs<10)    : {big}   ({100*big/n:.2f}%)")
        print(f"  missed-wet (served<=obs-10, obs>=10)      : {miss}  ({100*miss/n:.2f}%)")
        dry = obs < 2.0
        print(f"  near-dry days (obs<2mm, n={int(dry.sum())}): served mean={served[dry].mean():.2f} "
              f"vs obs mean={obs[dry].mean():.2f} | served>=10mm on {int(np.sum((served>=10)&dry))} "
              f"({100*np.mean((served>=10)&dry):.2f}%) such days")

        # save CSV
        out = ev[["date", "district_id", "name", "state", "zone", "observed"]].copy()
        out["raw"] = raw; out["served"] = served
        out["p_moderate"] = results[lt]["probs"][7.5]
        outfile = f"past_year_2025_T{lt}.csv"
        out.to_csv(outfile, index=False)
        print(f"\n  saved {outfile}")

    print("\nDone.")


if __name__ == "__main__":
    main()