"""
Read IMD 0.25° gridded rainfall binary (.grd) files.
Format: little-endian float32, 135 rows x 129 cols, -999 = missing
"""
import struct
import numpy as np
import os

IMD_GRID = {
    "nrows": 135,
    "ncols": 129,
    "lat_max": 37.5,
    "lat_min": 3.75,
    "lon_min": 65.0,
    "lon_max": 97.0,
    "resolution": 0.25,
    "missing": -999.0,
}


def read_grd(filepath):
    """Read a single .grd file, return 2D numpy array (135x129)."""
    with open(filepath, "rb") as f:
        data = f.read()
    n_floats = len(data) // 4
    floats = struct.unpack(f"<{n_floats}f", data)
    arr = np.array(floats, dtype=np.float32)
    grid = arr.reshape(IMD_GRID["nrows"], IMD_GRID["ncols"])
    return grid


def grd_to_latlon(grid):
    """Convert grid to list of (lat, lon, rainfall) tuples."""
    lats = np.linspace(IMD_GRID["lat_max"], IMD_GRID["lat_min"], IMD_GRID["nrows"])
    lons = np.linspace(IMD_GRID["lon_min"], IMD_GRID["lon_max"], IMD_GRID["ncols"])
    points = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            val = float(grid[i, j])
            if val != IMD_GRID["missing"]:
                points.append({"lat": round(lat, 4), "lon": round(lon, 4), "rainfall": round(val, 2)})
    return points


def load_date(date_str, data_dir="imd_data"):
    """Load rainfall for a date string like '20241225'. Returns 135x129 grid or None."""
    year = date_str[:4]
    filename = f"rain_ind0.25_{date_str[4:6]}_{date_str[6:8]}_{date_str[2:4]}.grd"
    # IMD naming: rain_ind0.25_DD_MM_YY.grd
    # Also try: rain_ind0.25_YYYYMMDD.grd
    candidates = [
        f"rain_ind0.25_{date_str[4:6]}_{date_str[6:8]}_{date_str[2:4]}.grd",
        f"rain_ind0.25_{date_str}.grd",
        f"RF25_{date_str[4:6]}{date_str[6:8]}{date_str[:4]}.grd",
    ]
    for fname in candidates:
        path = os.path.join(data_dir, year, fname)
        if os.path.exists(path):
            return read_grd(path)
    return None


def get_nwd_grid(grid):
    """Extract Northwest India (NWD) subset: lat 20-37.5, lon 65-80."""
    lats = np.linspace(IMD_GRID["lat_max"], IMD_GRID["lat_min"], IMD_GRID["nrows"])
    lons = np.linspace(IMD_GRID["lon_min"], IMD_GRID["lon_max"], IMD_GRID["ncols"])
    lat_mask = (lats >= 20) & (lats <= 37.5)
    lon_mask = (lons >= 65) & (lons <= 80)
    return grid[np.ix_(lat_mask, lon_mask)]


def list_available_dates(data_dir="imd_data"):
    """List all available dates across year folders."""
    dates = []
    for year_dir in sorted(os.listdir(data_dir)):
        year_path = os.path.join(data_dir, year_dir)
        if not os.path.isdir(year_path):
            continue
        for f in sorted(os.listdir(year_path)):
            if f.endswith(".grd"):
                dates.append(os.path.join(year_dir, f))
    return dates
