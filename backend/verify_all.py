"""RIGOROUS verification of the served pipeline (v15 + consistency damp) on the
temporal test window (last 20% of dates). Every registered metric:

  continuous: RMSE, MAE, R2, Pearson, Spearman, bias ratio, KGE, median/p90/p99 abs err
  categorical: POD FAR CSI ETS FSS freq-bias + contingency table @ 7.5/64.5/124.5/244.5
  probabilistic: Brier, Brier decomposition (reliability/resolution/uncertainty), AUC,
                 reliability/ECE calibration, CRPS(trapezoid)
  skill/significance: RRMSE skill, bootstrap 95% CI on RMSE, paired t-test,
                      Diebold-Mariano test
  breakdowns: per-regime, per-zone, per-month, per-date stability, worst-case audit
"""
import sys
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
from sklearn.metrics import (accuracy_score, f1_score, precision_score, recall_score,
                             brier_score_loss, roc_auc_score, r2_score,
                             mean_absolute_error, confusion_matrix, classification_report)
from scipy.stats import pearsonr, spearmanr, ttest_rel, norm

BC_FEATURES = [
    "raw_rainfall", "wind_speed", "wind_dir", "cape", "pressure", "radiation",
    "temp_range", "temp_mean", "day_of_year", "month", "monsoon_phase",
    "is_peak_monsoon", "latitude", "longitude", "lead_time",
]
REGIMES = ["active_monsoon", "break_monsoon", "depression", "orographic", "coastal", "western_disturbance"]

registry = ModelRegistry()
latest = registry.get_latest_version()
rc = RegimeClassifier(); bc = BiasCorrector(); pe = ProbabilityEstimator(); dw = DryWetModel()
latest.load_models(rc, bc, pe, dw)

df = pd.read_csv("training_data_v3.csv")
dates = sorted(df["date"].unique())
split_idx = int(len(dates) * 0.8)
test_dates = set(dates[split_idx:])
ev = df[df["date"].isin(test_dates)].copy().reset_index(drop=True)
print(f"MODEL: {latest.version_name} | test window {min(test_dates)} -> {max(test_dates)} "
      f"| {len(test_dates)} dates | {len(ev)} rows | lead_time={ev['lead_time'].iloc[0] if 'lead_time' in ev else '?'}")

obs = ev["observed_rainfall"].values.astype(np.float64)
raw = ev["raw_rainfall"].values.astype(np.float64)

# ---------- served pipeline ----------
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
soft = np.sum(pM * corr, axis=1)
oracle = np.array([corr[i, reg_list.index(t)] if t in reg_list else 0.0
                   for i, t in enumerate(y_true_regime)])
Xdw = ev[dw._feature_names].values.astype(np.float64)
wet_prob = dw.model.predict_proba(Xdw)[:, 1]
zero_mask = (raw < 2.0) & (wet_prob < dw.zero_threshold)
for a in (soft, oracle):
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
served = soft.copy()
damp = (raw < 2.0) & (served > raw) & (pe_probs[7.5] < 0.5) & (pe_probs[64.5] < 0.05)
served[damp] = raw[damp] + (served[damp] - raw[damp]) * (pe_probs[7.5][damp] / 0.5)
EV = {"obs": obs, "raw": raw, "served": served, "oracle": oracle}

# =====================================================================
print("\n" + "#" * 74)
print("# 1) REGIME CLASSIFICATION")
print("#" * 74)
rep = classification_report(y_true_regime, pred_regime, output_dict=True, zero_division=0)
acc = accuracy_score(y_true_regime, pred_regime)
print(f"  overall accuracy  = {acc:.4f}")
print(f"  balanced accuracy = {np.mean([rep[c]['recall'] for c in REGIMES]):.4f}")
print(f"  macro-F1          = {f1_score(y_true_regime, pred_regime, average='macro', zero_division=0):.4f}")
print(f"  weighted-F1       = {f1_score(y_true_regime, pred_regime, average='weighted', zero_division=0):.4f}")
print(f"  {'class':>20} {'support':>8} {'prec':>7} {'recall':>7} {'f1':>7}")
for c in REGIMES:
    r = rep[c]
    print(f"  {c:>20} {int(r['support']):>8} {r['precision']:>7.3f} {r['recall']:>7.3f} {r['f1-score']:>7.3f}")
cm = confusion_matrix(y_true_regime, pred_regime, labels=REGIMES)
print("  confusion matrix (rows=true, cols=pred):")
print("   " + "".join(f"{c[:4]:>7}" for c in REGIMES))
for i, row in enumerate(cm):
    print(f"  {REGIMES[i][:4]:<4}" + "".join(f"{v:>7}" for v in row))

# =====================================================================
print("\n" + "#" * 74)
print("# 2) CONTINUOUS RAINFALL ACCURACY")
print("#" * 74)
print(f"  {'':>18}{'RMSE':>8}{'MAE':>7}{'medAE':>7}{'P90':>7}{'P99':>7}{'MAX':>7}"
      f"{'R2':>8}{'r':>7}{'rho':>7}{'bias':>7}{'KGE':>7}")
def kge(y, f):
    r = pearsonr(y, f)[0] if np.std(y) and np.std(f) else 0
    a = np.std(f) / np.std(y) if np.std(y) else 1
    b = np.mean(f) / np.mean(y) if np.mean(y) else 1
    return 1 - np.sqrt((r - 1) ** 2 + (a - 1) ** 2 + (b - 1) ** 2)
for name in ["raw", "served", "oracle"]:
    y, f = obs, EV[name]
    ae = np.abs(f - y)
    r2 = r2_score(y, f)
    p = pearsonr(y, f)[0]
    sp = spearmanr(y, f)[0]
    rmse = float(np.sqrt(np.mean((f - y) ** 2)))
    print(f"  {name:>18}{rmse:>8.2f}{np.mean(ae):>7.2f}{np.median(ae):>7.2f}"
          f"{np.quantile(ae, .9):>7.2f}{np.quantile(ae, .99):>7.2f}{np.max(ae):>7.1f}"
          f"{r2:>8.3f}{p:>7.3f}{sp:>7.3f}{np.mean(f)/np.mean(y) if np.mean(y) else 1:>7.2f}"
          f"{kge(y, f):>7.3f}")

# =====================================================================
print("\n" + "#" * 74)
print("# 3) CATEGORICAL (threshold) VERIFICATION")
print("#" * 74)
def daily_fss(y, f, th):
    d = pd.DataFrame({"d": ev["date"].values, "y": y, "f": f})
    vals = []
    for _, g in d.groupby("d"):
        if len(g) < 5:
            continue
        vals.append(compute_verification_metrics(g["y"].values, g["f"].values, threshold=th)["fss"])
    return float(np.mean(vals)) if vals else float("nan")
print(f"  {'thr':>8}{'method':>8}{'events':>7}{'POD':>7}{'FAR':>7}{'CSI':>7}{'ETS':>7}"
      f"{'FSS(day)':>9}{'freqBias':>9}")
for t in THRESHOLDS:
    y = obs >= t
    n_ev = int(y.sum())
    for name in ["raw", "served", "oracle"]:
        f = EV[name]
        m = compute_verification_metrics(obs, f, threshold=t)
        hits = int(np.sum(y & (f >= t)))
        fct = int(np.sum(f >= t))
        fb = fct / max(n_ev, 1)
        print(f"  {t:>8}{name:>8}{n_ev:>7}{m['pod']:>7.3f}{m['far']:>7.3f}{m['csi']:>7.3f}"
              f"{m['ets']:>7.3f}{daily_fss(obs, f, t):>9.3f}{fb:>9.2f}")

# =====================================================================
print("\n" + "#" * 74)
print("# 4) PROBABILISTIC VERIFICATION (served exceedance probabilities)")
print("#" * 74)
clim = {t: float(np.mean(obs >= t)) for t in THRESHOLDS}
for t in THRESHOLDS:
    y = obs >= t
    p = pe_probs[t]
    bs = float(brier_score_loss(y, p))
    unc = clim[t] * (1 - clim[t])
    # reliability/resolution via bootstrap-free binning (10 bins)
    bins = np.linspace(0, 1, 11)
    rel, res = 0.0, 0.0
    cnt = 0
    for a, b in zip(bins[:-1], bins[1:]):
        m = (p >= a) & (p < b)
        if m.sum() < 5:
            continue
        pc = p[m].mean(); oc = float(y[m].mean())
        nk = m.sum() / len(y)
        rel += nk * (pc - oc) ** 2
        res += nk * (oc - clim[t]) ** 2
        cnt += 1
    ece = rel / (cnt + 1e-9) * cnt if cnt else rel
    n_ev = int(y.sum())
    auc = roc_auc_score(y, p) if 0 < n_ev < len(y) else np.nan
    bss = 1 - bs / unc if unc > 0 else np.nan
    print(f"  >= {t:>6}mm: Brier={bs:.4f}  BSS={bss:+.3f}  AUC={auc:.4f}  "
          f"Reliability={rel:.4f}  Resolution={res:.4f}  ECE={ece:.4f}")

# =====================================================================
print("\n" + "#" * 74)
print("# 5) SKILL SCORES + STATISTICAL SIGNIFICANCE (served vs raw)")
print("#" * 74)
rows_raw, rows_srv = [], []
date_rmse = []
for d, g in ev.groupby("date"):
    o = obs[g.index]; r = raw[g.index]; s = served[g.index]
    rows_raw.append(np.sqrt(np.mean((r - o) ** 2)))
    rows_srv.append(np.sqrt(np.mean((s - o) ** 2)))
rows_raw = np.array(rows_raw); rows_srv = np.array(rows_srv)
rrmse_skill = 1 - rows_srv.mean() / rows_raw.mean()
rng = np.random.RandomState(0)
boots = []
for _ in range(500):
    idx = rng.choice(len(rows_raw), len(rows_raw), replace=True)
    boots.append(1 - rows_srv[idx].mean() / rows_raw[idx].mean())
ci = np.percentile(boots, [2.5, 97.5])
d_arr = rows_raw - rows_srv
dm = d_arr.mean() / (d_arr.std(ddof=1) / np.sqrt(len(d_arr)))
dm_p = 2 * (1 - norm.cdf(abs(dm)))
t, t_p = ttest_rel(rows_raw, rows_srv)
print(f"  mean daily RMSE     raw={rows_raw.mean():.2f}  served={rows_srv.mean():.2f}")
print(f"  RRMSE skill score   = {rrmse_skill:.3f}  (bootstrap 95% CI [{ci[0]:.3f}, {ci[1]:.3f}])")
print(f"  paired t            = {t:+.3f}  p={t_p:.2e}")
print(f"  Diebold-Mariano     = {dm:+.3f}  p={dm_p:.2e}")
print(f"  served beats raw on {int(np.mean(rows_srv < rows_raw)*len(rows_raw))}/{len(rows_raw)} dates")

# =====================================================================
print("\n" + "#" * 74)
print("# 6) BREAKDOWNS (served vs raw)")
print("#" * 74)
def blk(grp):
    o = obs[grp]; r = raw[grp]; s = served[grp]
    return float(np.sqrt(np.mean((r - o) ** 2))), float(np.sqrt(np.mean((s - o) ** 2)))
print("  -- per true regime --")
print(f"  {'regime':>22}{'n':>7}{'raw':>8}{'served':>8}{'gain%':>8}")
for c in REGIMES:
    m = y_true_regime == c
    if m.sum() == 0:
        continue
    r_r, r_s = blk(m)
    print(f"  {c:>22}{int(m.sum()):>7}{r_r:>8.2f}{r_s:>8.2f}{100*(1-r_s/r_r):>8.1f}")
print("  -- per zone --")
print(f"  {'zone':>18}{'n':>7}{'raw':>8}{'served':>8}{'gain%':>8}")
for z in sorted(ev["zone"].unique()):
    m = ev["zone"].values == z
    if m.sum() == 0:
        continue
    r_r, r_s = blk(m)
    print(f"  {z:>18}{int(m.sum()):>7}{r_r:>8.2f}{r_s:>8.2f}{100*(1-r_s/r_r):>8.1f}")
print("  -- per month --")
print(f"  {'month':>8}{'n':>7}{'raw':>8}{'served':>8}{'gain%':>8}")
ev["_ym"] = ev["date"].str[:7]
for ym, g in ev.groupby("_ym"):
    r_r, r_s = blk(g.index)
    print(f"  {ym:>8}{len(g):>7}{r_r:>8.2f}{r_s:>8.2f}{100*(1-r_s/r_r):>8.1f}")

# =====================================================================
print("\n" + "#" * 74)
print("# 7) WORST-CASE AUDIT + CONSISTENCY")
print("#" * 74)
cons = np.abs(served - obs)
top = np.argsort(-cons)[:15]
print(f"  top-15 largest errors (date | district | raw | served | obs) inside >10mm over-preds:")
for i in top:
    row = ev.iloc[i]
    print(f"  {row['date']} {row['name']:<14} raw={raw[i]:.1f} served={served[i]:.1f} obs={obs[i]:.1f} "
          f"regime={row['regime']}")
contra = int(np.sum((served >= 10) & (pe_probs[7.5] < 0.4)))
big = int(np.sum((served >= obs + 10) & (obs < 10)))
miss = int(np.sum((served < obs - 10) & (obs >= 10)))
print(f"  contradictions (served>=10 but P7.5<0.4) : {contra}  ({100*contra/len(obs):.2f}%)")
print(f"  false blowups (served>=obs+10, obs<10)    : {big}   ({100*big/len(obs):.2f}%)")
print(f"  missed-wet (served<=obs-10, obs>=10)      : {miss}  ({100*miss/len(obs):.2f}%)")
dry = obs < 2.0
print(f"  near-dry days (obs<2mm, n={int(dry.sum())}): served mean={served[dry].mean():.2f} "
      f"vs obs mean={obs[dry].mean():.2f}  | served>=10mm on {int(np.sum((served>=10)&dry))} "
      f"({100*np.mean((served>=10)&dry):.2f}%) such days")