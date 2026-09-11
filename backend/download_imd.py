"""
Download IMD Gridded Rainfall Data
Run: python download_imd.py
"""
import urllib.request
import os

def download_imd_rainfall(year=2024):
    os.makedirs('imd_data', exist_ok=True)
    
    # IMD Pune gridded rainfall data URLs
    urls = [
        f'https://www.imdpune.gov.in/cmpg/Griddata/ind{year}_rfp25.nc',
        f'https://www.imdpune.gov.in/cmpg/Griddata/{year}_rainfall_025.nc',
        f'https://mausam.imd.gov.in/backend/RF25_{year}.nc',
    ]
    
    filename = f'imd_data/IMD_rain_{year}.nc'
    
    for url in urls:
        print(f'Trying: {url}')
        try:
            urllib.request.urlretrieve(url, filename)
            size = os.path.getsize(filename) / (1024*1024)
            print(f'Downloaded! Size: {size:.2f} MB')
            return filename
        except Exception as e:
            print(f'Failed: {e}')
    
    print('\nAll URLs failed. Please download manually from:')
    print('https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html')
    print('Select year 2024 and click download')
    return None

if __name__ == '__main__':
    download_imd_rainfall(2024)
