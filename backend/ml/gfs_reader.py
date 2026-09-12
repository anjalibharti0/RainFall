"""
Read GFS 0.25° GRIB2 forecast files.
Requires: cfgrib, eccodes (pip install cfgrib eccodes)
"""
import os
import numpy as np

NWD_BOUNDS = {"lat_min": 20, "lat_max": 37.5, "lon_min": 65, "lon_max": 80}


def read_gfs(filepath, parameter="tp"):
    """Read a GFS GRIB2 file and return the precipitation grid.
    
    filepath: path to .grb2 file
    parameter: 'tp' (total precipitation) or 'prate' (precipitation rate)
    
    Returns: dict with lats, lons, data arrays
    """
    try:
        import xarray as xr
        ds = xr.open_dataset(filepath, engine="cfgrib", 
                             backend_kwargs={"filter_by_keys": {"typeOfLevel": "surface"}})
        
        # Get precipitation variable
        var_name = None
        for name in ["tp", "prate", "cp", "lsp"]:
            if name in ds.data_vars:
                var_name = name
                break
        
        if var_name is None:
            var_name = list(ds.data_vars.keys())[0]
        
        data = ds[var_name].values
        lats = ds.latitude.values
        lons = ds.longitude.values
        
        # Ensure 2D
        if data.ndim == 3:
            data = data[0]
        
        return {
            "data": data,
            "lats": lats,
            "lons": lons,
            "parameter": var_name,
            "units": ds[var_name].attrs.get("units", "unknown"),
        }
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def get_nwd_subset(filepath):
    """Read GFS file and extract NWD region (lat 20-37.5, lon 65-80)."""
    result = read_gfs(filepath)
    if result is None:
        return None
    
    data = result["data"]
    lats = result["lats"]
    lons = result["lons"]
    
    # Handle 1D lat/lon arrays
    if lats.ndim == 1 and lons.ndim == 1:
        lon_grid, lat_grid = np.meshgrid(lons, lats)
    else:
        lat_grid, lon_grid = lats, lons
    
    # Create mask for NWD region
    mask = (
        (lat_grid >= NWD_BOUNDS["lat_min"]) & 
        (lat_grid <= NWD_BOUNDS["lat_max"]) &
        (lon_grid >= NWD_BOUNDS["lon_min"]) & 
        (lon_grid <= NWD_BOUNDS["lon_max"])
    )
    
    # Extract subset
    if lats.ndim == 1:
        lat_indices = np.where((lats >= NWD_BOUNDS["lat_min"]) & (lats <= NWD_BOUNDS["lat_max"]))[0]
        lon_indices = np.where((lons >= NWD_BOUNDS["lon_min"]) & (lons <= NWD_BOUNDS["lon_max"]))[0]
        subset = data[np.ix_(lat_indices, lon_indices)]
        subset_lats = lats[lat_indices]
        subset_lons = lons[lon_indices]
    else:
        subset = data[mask]
        subset_lats = lat_grid[mask]
        subset_lons = lon_grid[mask]
    
    return {
        "data": subset,
        "lats": subset_lats,
        "lons": subset_lons,
        "parameter": result["parameter"],
        "units": result["units"],
    }


def list_gfs_files(data_dir="nwp_data"):
    """List all available GFS files."""
    files = []
    for year_dir in sorted(os.listdir(data_dir)):
        year_path = os.path.join(data_dir, year_dir)
        if not os.path.isdir(year_path):
            continue
        for f in sorted(os.listdir(year_path)):
            if f.endswith(".grb2"):
                files.append(os.path.join(year_dir, f))
    return files


def load_gfs_date(date_str, lead_time=24, data_dir="nwp_data"):
    """Load GFS forecast for a specific date and lead time.
    
    date_str: YYYYMMDD
    lead_time: hours (0, 24, 48, 72)
    """
    year = date_str[:4]
    filename = f"gfs_0p25_00z_{date_str}_00_{lead_time:03d}.grb2"
    filepath = os.path.join(data_dir, year, filename)
    
    if os.path.exists(filepath):
        return get_nwd_subset(filepath)
    return None
