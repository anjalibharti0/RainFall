"""
Train ML models on real IMD/GFS data.
V2: Iterative train-evaluate-improve cycle with metrics tracking.

Usage:
    python train_real.py --start 2024-06-01 --end 2024-09-30
    python train_real.py --download --start 2024-06-01 --end 2024-09-30
    python train_real.py --force
    python train_real.py --iterate 3  # run 3 training cycles
"""

import argparse
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(__file__))


def train_cycle(df, registry, cycle_num, total_cycles):
    """Run one training cycle and return metrics."""
    print(f"\n{'='*70}")
    print(f"TRAINING CYCLE {cycle_num}/{total_cycles}")
    print(f"{'='*70}")

    t0 = time.time()
    was_retrained, version = registry.retrain_if_needed(df, force=True)
    elapsed = time.time() - t0

    meta = version.load_metadata()
    metrics = meta.get("metrics", {})
    metrics["train_time_sec"] = round(elapsed, 1)
    metrics["cycle"] = cycle_num

    print(f"\n  Cycle {cycle_num} completed in {elapsed:.1f}s")
    print(f"  Regime accuracy: {metrics.get('regime_accuracy', 'N/A')}")
    print(f"  Raw RMSE: {metrics.get('raw_rmse', 'N/A')}")
    print(f"  Corrected RMSE: {metrics.get('corrected_rmse', 'N/A')}")
    print(f"  RMSE improvement: {metrics.get('rmse_improvement_pct', 'N/A')}%")

    return metrics, version


def main():
    parser = argparse.ArgumentParser(description="Train models on real data")
    parser.add_argument("--start", default="2024-06-01", help="Training start date")
    parser.add_argument("--end", default="2024-09-30", help="Training end date")
    parser.add_argument("--download", action="store_true", help="Download data first")
    parser.add_argument("--force", action="store_true", help="Force retrain")
    parser.add_argument("--districts", type=int, default=800, help="Number of districts")
    parser.add_argument("--synthetic-fallback", action="store_true", help="Use synthetic if real data insufficient")
    parser.add_argument("--iterate", type=int, default=1, help="Number of training cycles (each with fresh version)")
    args = parser.parse_args()

    print("=" * 70)
    print("REGIME-AWARE RAINFALL POST-PROCESSING - MODEL TRAINING V2")
    print("=" * 70)

    if args.download:
        print("\n--- Downloading IMD data (yearly archive) ---")
        from download_imd import download_yearly_range
        start_year = int(args.start[:4])
        end_year = int(args.end[:4])
        download_yearly_range(start_year, end_year, "imd_data")

        print("\n--- Downloading GFS data ---")
        from download_gfs import download_gfs
        download_gfs(args.start, args.end, "nwp_data")

    print(f"\n--- Building training dataset ({args.start} to {args.end}) ---")
    from ml.data_loader import RealDataLoader
    from ml.all_districts import DISTRICTS

    loader = RealDataLoader(imd_dir="imd_data", gfs_dir="nwp_data")
    districts = DISTRICTS[:args.districts] if args.districts < len(DISTRICTS) else DISTRICTS

    df = loader.build_training_dataset(args.start, args.end, districts=districts)

    if len(df) < 50:
        print(f"\nInsufficient real data ({len(df)} rows).")
        if args.synthetic_fallback:
            print("Falling back to synthetic training...")
            from ml.synthetic_data import generate_training_data
            df = generate_training_data(n_samples=10000, seed=42)
        else:
            print("Run with --synthetic-fallback or download more data.")
            sys.exit(1)

    from ml.model_registry import ModelRegistry
    registry = ModelRegistry()

    all_metrics = []
    best_version = None
    best_rmse = float("inf")

    for cycle in range(1, args.iterate + 1):
        metrics, version = train_cycle(df, registry, cycle, args.iterate)
        all_metrics.append(metrics)

        corrected_rmse = metrics.get("corrected_rmse", metrics.get("raw_rmse", float("inf")))
        if corrected_rmse < best_rmse:
            best_rmse = corrected_rmse
            best_version = version

    if best_version:
        registry.set_latest(best_version.version_name)

    history_path = os.path.join(os.path.dirname(__file__), "trained_models", "training_history.json")
    with open(history_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")
    print(f"  Cycles run: {args.iterate}")
    print(f"  Best version: {best_version.version_name if best_version else 'N/A'}")
    print(f"  Best corrected RMSE: {best_rmse}")
    print(f"  History saved to: trained_models/training_history.json")

    if len(all_metrics) > 1:
        print(f"\n  Improvement across cycles:")
        for i, m in enumerate(all_metrics):
            print(f"    Cycle {i+1}: RMSE={m.get('corrected_rmse', 'N/A')}, "
                  f"Regime acc={m.get('regime_accuracy', 'N/A')}, "
                  f"Time={m.get('train_time_sec', 'N/A')}s")


if __name__ == "__main__":
    main()
