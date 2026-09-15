"""Merge ERA5 gap files into gap_combined.json."""
import os
import json
import glob

DATA_DIR = "nwp_data/2024"
OUTPUT = os.path.join(DATA_DIR, "gap_combined.json")

# Load existing gap_combined.json if it exists
existing = []
if os.path.exists(OUTPUT):
    existing = json.load(open(OUTPUT, "r"))
    print(f"Existing gap_combined.json: {len(existing)} locations")

# Find all ERA5 gap files
era5_files = sorted(glob.glob(os.path.join(DATA_DIR, "era5_gap_*.json")))
print(f"Found {len(era5_files)} ERA5 gap files")

new_locations = []
for f in era5_files:
    data = json.load(open(f, "r"))
    if isinstance(data, list):
        new_locations.extend(data)
    else:
        new_locations.append(data)

print(f"New ERA5 locations: {len(new_locations)}")

# Merge: keep existing + add new (skip duplicates by lat/lon)
existing_keys = set()
for loc in existing:
    key = (round(loc.get("latitude", 0), 2), round(loc.get("longitude", 0), 2))
    existing_keys.add(key)

deduped_new = []
for loc in new_locations:
    key = (round(loc.get("latitude", 0), 2), round(loc.get("longitude", 0), 2))
    if key not in existing_keys:
        deduped_new.append(loc)
        existing_keys.add(key)

merged = existing + deduped_new
print(f"Merged: {len(merged)} total locations ({len(deduped_new)} new added)")

with open(OUTPUT, "w") as f:
    json.dump(merged, f)
print(f"Saved to {OUTPUT}")
