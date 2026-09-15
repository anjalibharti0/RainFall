import pandas as pd
import numpy as np
import sys
import os

csv = sys.argv[1] if len(sys.argv) > 1 else "past_year_2025_T24.csv"
top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 40

df = pd.read_csv(csv)
df["abs_err"] = (df["served"] - df["observed"]).abs()
df["raw_err"] = (df["raw"] - df["observed"]).abs()


def dd_metrics(g):
    if len(g) == 0:
        return {}
    obs = g["observed"].values
    served = g["served"].values
    raw = g["raw"].values
    se = (g["abs_err"] ** 2).sum()
    sr = (g["raw_err"] ** 2).sum()
    obs_wet = obs >= 2.5
    served_wet = served >= 2.5
    tp = (obs_wet & served_wet).sum()
    fp = (~obs_wet & served_wet).sum()
    fn = (obs_wet & ~served_wet).sum()
    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * recall / (prec + recall) if prec + recall > 0 else 0.0
    return {
        "n": len(g),
        "wedays": int(obs_wet.sum()),
        "obs_mean": round(obs.mean(), 2),
        "served_mean": round(served.mean(), 2),
        "rmse": round(np.sqrt(se / len(g)), 2),
        "raw_rmse": round(np.sqrt(sr / len(g)), 2),
        "bias": round(served.mean() - obs.mean(), 2),
        "wetF1": round(f1, 3),
        "recall": round(recall, 3),
        "prec": round(prec, 3),
        "p90err": round(np.percentile(g["abs_err"], 90), 2),
        "maxerr": round(g["abs_err"].max(), 1),
    }


out = []
for name, g in df.groupby("name"):
    m = dd_metrics(g)
    m.update({"state": g["state"].iloc[0], "zone": g["zone"].iloc[0]})
    out.append({"name": name, **m})
res = pd.DataFrame(out).sort_values("rmse", ascending=False)

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 500)
cols = ["name", "state", "zone", "n", "wedays", "obs_mean", "served_mean",
        "raw_rmse", "rmse", "bias", "wetF1", "recall", "prec", "p90err", "maxerr"]

print(f"=== District-by-district table: {csv} ({len(res)} districts with data) ===")
print("\n-- Worst {0} by RMSE --".format(top_n))
print(res[cols].head(top_n).to_string(index=False))
print("\n-- Best {0} by RMSE (>=100 days) --".format(top_n))
subset = res[res["n"] >= 100]
print(subset[cols].sort_values("rmse").head(top_n).to_string(index=False))

print("\n-- Aggregate --")
print(res[["n", "wedays", "obs_mean", "rmse", "bias", "wetF1", "recall", "prec"]].mean().round(3).to_string())
print("median rmse:", round(res["rmse"].median(), 2), "| RMSE beat raw in",
      int((res["rmse"] < res["raw_rmse"]).sum()), "of", len(res), "districts")