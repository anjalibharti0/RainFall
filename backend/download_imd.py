"""
Download IMD 0.25° gridded daily rainfall data (binary .grd format).
Source: IMD Pune

Run: python download_imd.py --start 2024-01-01 --end 2026-09-12
"""
import os
import sys
import time
import urllib.request
import argparse
from datetime import datetime, timedelta

# IMD binary file naming: rain_ind0.25_DD_MM_YY.grd
# Base URL for IMD rainfall data
IMD_BASE = "https://www.imdpune.gov.in/cmpg/Griddata"


def build_imd_url(date_str):
    """Build IMD URL for a given date.
    
    date_str: YYYYMMDD
    Returns: (url, filename)
    """
    dt = datetime.strptime(date_str, "%Y%m%d")
    dd = dt.strftime("%d")
    mm = dt.strftime("%m")
    yy = dt.strftime("%y")
    
    filename = f"rain_ind0.25_{dd}_{mm}_{yy}.grd"
    # IMD uses multiple URL patterns, try common ones
    urls = [
        f"{IMD_BASE}/{filename}",
        f"{IMD_BASE}/rain_ind0.25_{dd}_{mm}_{yy}.grd",
        f"https://mausam.imd.gov.in/backend/{filename}",
    ]
    return urls, filename


def download_file(urls, filepath, retries=3):
    """Try downloading from multiple URLs with retries."""
    for url in urls:
        for attempt in range(retries):
            try:
                urllib.request.urlretrieve(url, filepath)
                size_kb = os.path.getsize(filepath) / 1024
                if size_kb > 1:  # Skip empty files
                    return True, size_kb, url
                else:
                    os.remove(filepath)
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(1)
        # Try next URL
    return False, "All URLs failed", None


def download_imd_range(start_date, end_date, data_dir="imd_data"):
    """Download IMD files for a date range."""
    os.makedirs(data_dir, exist_ok=True)
    
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    total_files = 0
    downloaded = 0
    failed = 0
    skipped = 0
    failed_dates = []
    
    while current <= end:
        date_str = current.strftime("%Y%m%d")
        year = current.strftime("%Y")
        year_dir = os.path.join(data_dir, year)
        os.makedirs(year_dir, exist_ok=True)
        
        total_files += 1
        urls, filename = build_imd_url(date_str)
        filepath = os.path.join(year_dir, filename)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1:
            skipped += 1
            current += timedelta(days=1)
            continue
        
        print(f"[{downloaded+failed+skipped}/{total_files}] {filename}...", end=" ")
        success, result, used_url = download_file(urls, filepath)
        
        if success:
            downloaded += 1
            print(f"OK ({result:.0f} KB)")
        else:
            failed += 1
            failed_dates.append(date_str)
            print(f"FAILED")
        
        current += timedelta(days=1)
        time.sleep(0.5)  # Be nice to IMD servers
    
    print(f"\n=== DONE ===")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped (exists): {skipped}")
    print(f"Failed: {failed}")
    
    if failed_dates:
        print(f"\nFailed dates ({len(failed_dates)}):")
        print(", ".join(failed_dates[:20]) + ("..." if len(failed_dates) > 20 else ""))
        print(f"\nDownload manually from: https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html")
    
    print(f"Location: {os.path.abspath(data_dir)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download IMD rainfall data")
    parser.add_argument("--start", default="2024-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2026-09-12", help="End date YYYY-MM-DD")
    parser.add_argument("--dir", default="imd_data", help="Output directory")
    args = parser.parse_args()
    
    print(f"IMD Download: {args.start} to {args.end}")
    print(f"Output: {args.dir}/")
    print()
    
    download_imd_range(args.start, args.end, args.dir)
