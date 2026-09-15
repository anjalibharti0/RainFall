"""Backtest v15 (served pipeline) across the temporal test window (last 20% of dates).

Replicates the LIVE path exactly:
  regime classifier predict_proba -> soft (probability-weighted) bias correction
  -> dry/wet hurdle zeroing -> probability-consistency damp
  -> probability estimator scaled by P(wet)

Compares: Raw NWP vs Hard (argmax regime) vs Soft (served) vs Oracle (true regime)
Aggregates continuous + heavy-rain contingency + probabilistic metrics,
plus per-regime and monthly roll-forward breakdowns.
"""
import sys, os
import numpy as np
import pandas as pd
sys.path.insert(0, ".")
sys.path.insert(0, "ml")

from ml.model_registry import ModelRegistry
from ml.regime_classifier import RegimeClassifier
from ml.bias_corrector import BiasCorrector
from ml.probability_estimator import ProbabilityEstimator, THRESHOLDS
from ml.dry_wet_model import DryWetModel
import ml.probability_estimator as pemod
from ml.synthetic_data import compute_verification_metrics
from sklearn.metrics import brier_score_loss, roc_auc_score, r2_score
from scipy.stats import pearsonr

BC_FEATURES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure", "radiation",
    "temp_range", "temp_mean", "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude", "lead_time",
]

registry = ModelRegistry()
latest = registry.get_latest_version()
print(f"Backtesting {latest.version_name} (latest)")

rc = RegimeClassifier(); bc = BiasCorrector(); pe = ProbabilityEstimator(); dw = DryWetModel()
latest.load_models(rc, bc, pe, dw)

df = pd.read_csv("training_data_v3.csv")
dates = sorted(df["date"].unique())
split_idx = int(len(dates) * 0.8)
test_dates = set(dates[split_idx:])
ev = df[df["date"].isin(test_dates)].copy().reset_index(drop=True)
print(f"Test window: {min(test_dates)} -> {max(test_dates)} | {len(test_dates)} dates | {len(ev)} rows")

obs = ev["observed_rainfall"].values.astype(np.float64)
raw = ev["raw_rainfall"].values.astype(np.float64)

Xrc = ev[rc._feature_names].values.astype(np.float64)
y_true_regime = ev["regime"].values
probs_all = rc.model.predict_proba(Xrc)
classes = rc.le.inverse_transform(rc.model.classes_.astype(int)).tolist()
idx_of = {c: j for j, c in enumerate(classes)}
pred_regime = rc.le.inverse_transform(rc.model.predict(Xrc).astype(int))

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

hard = np.array([corr[i, reg_list.index(p)] for i, p in enumerate(pred_regime)])
soft = np.sum(pM * corr, axis=1)
oracle = np.array([corr[i, reg_list.index(t)] if t in reg_list else 0.0
                   for i, t in enumerate(y_true_regime)])

Xdw = ev[dw._feature_names].values.astype(np.float64)
wet_prob = dw.model.predict_proba(Xdw)[:, 1]
zero_mask = (raw < 2.0) & (wet_prob < dw.zero_threshold)
for a in (hard, soft, oracle):
    a[zero_mask] = 0.0

Xpe = ev[pemod.FEATURE_NAMES].values.astype(np.float64)
p_scale = np.minimum(1.0, wet_prob)
pe_probs = {}
for t in THRESHOLDS:
    if t in pe.models:
        p = pe.models[t].predict_proba(Xpe)[:, 1]
    else:
        p = 1 / (1 + np.exp(0.06 * (t - raw)))
    pe_probs[t] = np.clip(p, 0, 1) * p_scale

# Served path: probability-consistency damp (same as main.py _predict_district)
served = soft.copy()
damp_mask = (raw < 2.0) & (soft > raw) & (pe_probs[7.5] < 0.5) & (pe_probs[64.5] < 0.05)
served[damp_mask] = raw[damp_mask] + (soft[damp_mask] - raw[damp_mask]) * (pe_probs[7.5][damp_mask] / 0.5)

def cont(y, f):
    rmse = float(np.sqrt(np.mean((f - y) ** 2)))
    mae = float(np.mean(np.abs(f - y)))
    r2 = float(r2_score(y, f))
    rho = float(pearsonr(y, f)[0]) if np.std(y) > 0 and np.std(f) > 0 else 0.0
    bias = float(np.mean(f) / np.mean(y)) if np.mean(y) > 0 else 1.0
    return rmse, mae, r2, rho, bias

print("\n" + "=" * 68)
print("1) REGIME CLASSIFICATION on held-out features")
print("=" * 68)
from sklearn.metrics import accuracy_score, f1_score
print(f"  accuracy overall : {accuracy_score(y_true_regime, pred_regime):.4f}")
print(f"  macro-F1         : {f1_score(y_true_regime, pred_regime, average='macro', zero_division=0):.4f}")
for c in ["depression", "active_monsoon", "break_monsoon", "coastal", "orographic", "western_disturbance"]:
    m = y_true_regime == c
    if m.sum() == 0:
        continue
    rec = float(np.mean(pred_regime[m] == c))
    print(f"  {c:>22}: n={int(m.sum()):5d}  recall={rec:.3f}")

print("\n" + "=" * 68)
print("2) RAINFALL ACCURACY (all held-out days pooled)")
print("=" * 68)
print(f"  {'':>12}{'RMSE':>8}{'MAE':>8}{'R2':>7}{'corr':>7}{'bias':>7}")
for name, f in [("Raw NWP", raw), ("Hard argmax", hard), ("SOFT (served)", served), ("Oracle", oracle)]:
    r = cont(obs, f)
    print(f"  {name:>12}{r[0]:>8.2f}{r[1]:>8.2f}{r[2]:>7.3f}{r[3]:>7.3f}{r[4]:>7.2f}")
contra = int(np.sum((served >= 10) & (pe_probs[7.5] < 0.4)))
big = float(np.mean((served >= obs + 10) & (obs < 10)))
print(f"  consistency: contradictions (>=10mm but p7.5<0.4) = {contra}; false blowups (>=obs+10 when obs<10) = {100*big:.2f}%")

print("\n" + "=" * 68)
print("3) HEAVY RAIN (deterministic + probabilistic)")
print("=" * 68)
for t in THRESHOLDS:
    y = obs >= t
    n_ev = int(y.sum())
    raw_m = compute_verification_metrics(obs, raw, threshold=t)
    soft_m = compute_verification_metrics(obs, served, threshold=t)
    orc_m = compute_verification_metrics(obs, oracle, threshold=t)
    brier = float(brier_score_loss(y, pe_probs[t]))
    auc = float(roc_auc_score(y, pe_probs[t])) if n_ev > 0 and n_ev < len(y) else float("nan")
    print(f"  >= {t:>6}mm  events={n_ev:>4}")
    print(f"      {'':>16}{'CSI':>7}{'ETS':>7}{'POD':>7}{'FAR':>7}{'FSS':>7}")
    for name, m in [("Raw", raw_m), ("Served", soft_m), ("Oracle", orc_m)]:
        print(f"      {name:>16}{m['csi']:>7.3f}{m['ets']:>7.3f}{m['pod']:>7.3f}{m['far']:>7.3f}{m['fss']:>7.3f}")
    print(f"      {'prob(Served)':>16}  Brier={brier:.4f}  AUC={auc:.4f}")

print("\n" + "=" * 68)
print("4) TRUE-REGIME BREAKDOWN (pooled RMSE raw vs served)")
print("=" * 68)
print(f"  {'regime':>22}{'n':>7}{'raw':>8}{'served':>8}{'gain%':>8}")
for c in ["active_monsoon", "break_monsoon", "depression", "coastal", "orographic", "western_disturbance"]:
    m = y_true_regime == c
    if m.sum() == 0:
        continue
    r_r = float(np.sqrt(np.mean((raw[m] - obs[m]) ** 2)))
    r_s = float(np.sqrt(np.mean((served[m] - obs[m]) ** 2)))
    print(f"  {c:>22}{int(m.sum()):>7}{r_r:>8.2f}{r_s:>8.2f}{100*(1-r_s/r_r):>8.1f}")

print("\n" + "=" * 68)
print("5) MONTHLY ROLL-FORWARD CONSISTENCY (per test-window month)")
print("=" * 68)
ev["_ym"] = ev["date"].str[:7]
print(f"  {'month':>8}{'n':>7}{'raw':>8}{'served':>8}{'gain%':>8}")
per_month_raw, per_month_srv = [], []
for ym, g in ev.groupby("_ym"):
    r_r = float(np.sqrt(np.mean((raw[g.index] - obs[g.index]) ** 2)))
    r_s = float(np.sqrt(np.mean((served[g.index] - obs[g.index]) ** 2)))
    per_month_raw.append(r_r); per_month_srv.append(r_s)
    print(f"  {ym:>8}{len(g):>7}{r_r:>8.2f}{r_s:>8.2f}{100*(1-r_s/r_r):>8.1f}")
imp = [100*(1-s/r) for r, s in zip(per_month_raw, per_month_srv)]
print(f"  months with improvement: {sum(1 for x in imp if x > 0)}/{len(imp)}")

print("\n" + "=" * 68)
print("6) DAY-BY-DAY STABILITY (per-date district-mean RMSE)")
print("=" * 68)
d_better = d_total = 0
for d, g in ev.groupby("date"):
    r_r = float(np.sqrt(np.mean((raw[g.index] - obs[g.index]) ** 2)))
    r_s = float(np.sqrt(np.mean((served[g.index] - obs[g.index]) ** 2)))
    d_total += 1
    if r_s < r_r:
        d_better += 1
print(f"  served beats raw on {d_better}/{d_total} dates ({100*d_better/d_total:.1f}%)")

print(f"\nNOTE: 'Hard' uses predicted-regime argmax; 'Oracle' uses true regimes "
      f"(unachievable live, shown for reference). Served = Soft + consistency damp.")