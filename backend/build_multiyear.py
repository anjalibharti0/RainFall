"""Build multi-year training dataset (2022-2024) and save to CSV."""
import sys, os, time
import pandas as pd
sys.path.insert(0, ".")
sys.path.insert(0, "ml")
from ml.data_loader import RealDataLoader, DISTRICTS

out_path = os.path.join("training_data_v3.csv")

if os.path.exists(out_path):
    print(f"{out_path} already exists, loading cached...")
    df = pd.read_csv(out_path)
    print(f"Loaded {len(df)} rows: {df['date'].min()} to {df['date'].max()}")
    raise SystemExit

loader = RealDataLoader(imd_dir="imd_data", gfs_dir="nwp_data")

dfs = []
for year in [2022, 2023, 2024]:
    t0 = time.time()
    df = loader.build_training_dataset(
        f"{year}-06-01", f"{year}-09-30",
        districts=DISTRICTS,
        build_clim=(year == 2022),
    )
    elapsed = time.time() - t0
    print(f"\nYear {year}: {len(df)} rows in {elapsed:.0f}s")
    if len(df) > 0:
        print(f"  Dates: {df['date'].nunique()}, Districts: {df['district_id'].nunique()}")
        dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
print(f"\nCombined: {len(combined)} rows, {combined['date'].nunique()} dates, {combined['district_id'].nunique()} districts")
combined.to_csv(out_path, index=False)
print(f"Saved to {out_path}")
print("Date range:", combined["date"].min(), "->", combined["date"].max())
print("\nRegime distribution:\n", combined["regime"].value_counts())