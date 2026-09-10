"""
IMD API Integration - Real-time data from India Meteorological Department
https://api.imd.gov.in/public/api_reference.html
"""
import httpx
import asyncio
from typing import Optional

IMD_BASE = "https://api.imd.gov.in/api/v1"

# IMD Warning Color Codes: 1=Green, 2=Yellow, 3=Orange, 4=Red
WARNING_COLORS = {
    "1": {"level": "green", "label": "Normal", "color": "#22c55e"},
    "2": {"level": "yellow", "label": "Advisory", "color": "#eab308"},
    "3": {"level": "orange", "label": "Warning", "color": "#f97316"},
    "4": {"level": "red", "label": "Extreme", "color": "#ef4444"},
}

# IMD Warning Codes
WARNING_CODES = {
    "1": "No Warning",
    "2": "Heavy Rain",
    "3": "Heavy Snow",
    "4": "Thunderstorm & Lightning",
    "5": "Hailstorm",
    "6": "Dust Storm",
    "7": "Dust Raising Winds",
    "8": "Strong Surface Winds",
    "9": "Heat Wave",
    "10": "Hot Day",
    "11": "Warm Night",
    "12": "Cold Wave",
    "13": "Cold Day",
    "14": "Ground Frost",
    "15": "Fog",
    "16": "Very Heavy Rain",
    "17": "Extremely Heavy Rain",
}

# IMD Rainfall Categories
RAINFALL_CATEGORIES = {
    "LE": {"label": "Large Excess", "threshold": 60},
    "E": {"label": "Excess", "threshold": 20},
    "N": {"label": "Normal", "threshold": -19},
    "D": {"label": "Deficient", "threshold": -59},
    "LD": {"label": "Large Deficient", "threshold": -99},
    "NR": {"label": "No Rain", "threshold": -100},
}


async def fetch_imd_warnings(district_obj_id: str) -> dict:
    """Fetch district-wise warnings from IMD API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{IMD_BASE}/districtwarning", params={"id": district_obj_id})
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
    except Exception as e:
        print(f"IMD warning fetch error for district {district_obj_id}: {e}")
        return {}


async def fetch_imd_district_rainfall(district_obj_id: str) -> dict:
    """Fetch district-wise rainfall from IMD API"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{IMD_BASE}/districtrainfall", params={"id": district_obj_id})
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
    except Exception as e:
        print(f"IMD rainfall fetch error for district {district_obj_id}: {e}")
        return {}


async def fetch_imd_state_district_forecast() -> list:
    """Fetch state-district rainfall forecast (5 days) from IMD API"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{IMD_BASE}/state_district_rainfall_forecast")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"IMD state-district forecast fetch error: {e}")
        return []


async def fetch_imd_current_weather(station_id: str = "NDL") -> dict:
    """Fetch current weather from IMD AWS station"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{IMD_BASE}/current_wx", params={"id": station_id})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"IMD current weather fetch error: {e}")
        return {}


async def fetch_imd_aws_data(state_id: Optional[str] = None, station_id: Optional[str] = None) -> list:
    """Fetch AWS/ARG real-time data from IMD"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {}
            if station_id:
                params["id"] = station_id
            elif state_id:
                params["sid"] = state_id
            resp = await client.get(f"{IMD_BASE}/aws_data", params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"IMD AWS data fetch error: {e}")
        return []


async def fetch_imd_subdivision_forecast() -> list:
    """Fetch subdivision rainfall forecast (7 days) from IMD"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{IMD_BASE}/subdivision_rainfall_forecast")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"IMD subdivision forecast fetch error: {e}")
        return []


def parse_imd_warning_color(color_code: str) -> dict:
    """Convert IMD color code (1-4) to our alert level"""
    return WARNING_COLORS.get(color_code, WARNING_COLORS["1"])


def parse_imd_warning_codes(codes_str: str) -> list:
    """Parse comma-separated warning codes"""
    if not codes_str or codes_str == "0":
        return []
    codes = codes_str.split(",")
    return [{"code": c.strip(), "description": WARNING_CODES.get(c.strip(), "Unknown")} for c in codes if c.strip() in WARNING_CODES]


def estimate_rainfall_from_color(color: str) -> dict:
    """Estimate rainfall range from IMD color code"""
    color_rainfall = {
        "#004de6": {"range": "7-11.5mm", "category": "Light", "min": 7, "max": 11.5},      # Blue
        "#00a0f0": {"range": "11.5-24.5mm", "category": "Moderate", "min": 11.5, "max": 24.5},  # Light Blue
        "#00ff00": {"range": "24.5-49.5mm", "category": "Heavy", "min": 24.5, "max": 49.5},     # Green
        "#ffff00": {"range": "49.5-64.5mm", "category": "Very Heavy", "min": 49.5, "max": 64.5}, # Yellow
        "#ff0000": {"range": "64.5-115.5mm", "category": "Extremely Heavy", "min": 64.5, "max": 115.5},  # Red
        "#ff00ff": {"range": ">115.5mm", "category": "Exceptional", "min": 115.5, "max": 250},  # Magenta
    }
    return color_rainfall.get(color, {"range": "0-7mm", "category": "Dry", "min": 0, "max": 7})


async def get_real_time_district_data(district_obj_id: str, district_name: str, state: str, lat: float, lon: float) -> dict:
    """
    Aggregate real IMD data for a single district.
    Returns unified format compatible with our frontend.
    """
    # Fetch warnings and rainfall concurrently
    warning_task = fetch_imd_warnings(district_obj_id)
    rainfall_task = fetch_imd_district_rainfall(district_obj_id)
    
    warning_data, rainfall_data = await asyncio.gather(warning_task, rainfall_task)
    
    # Parse warning
    day1_color = warning_data.get("Day1_Color", "1")
    day2_color = warning_data.get("Day2_Color", "1")
    day3_color = warning_data.get("Day3_Color", "1")
    
    warning_level = parse_imd_warning_color(day1_color)
    warning_codes = parse_imd_warning_codes(warning_data.get("Day_1", "0"))
    
    # Parse rainfall
    daily_actual = float(rainfall_data.get("Daily Actual", 0) or 0)
    daily_normal = float(rainfall_data.get("Daily Normal", 0) or 0)
    daily_departure = rainfall_data.get("Daily Departure Per", "0%")
    rainfall_category = rainfall_data.get("Daily Category", "NR")
    
    # Calculate probability based on warning level and rainfall
    p_heavy = min(0.95, daily_actual / 100 + 0.2) if daily_actual > 20 else 0.1
    p_very_heavy = min(0.8, p_heavy * 0.5)
    p_extreme = min(0.5, p_heavy * 0.2)
    
    # Determine regime from warning patterns
    regime = "active_monsoon"
    if warning_level["level"] == "red":
        regime = "depression"
    elif warning_level["level"] == "orange":
        regime = "active_monsoon"
    elif warning_level["level"] == "yellow":
        regime = "active_monsoon"
    else:
        regime = "break_monsoon"
    
    return {
        "id": district_obj_id,
        "name": district_name,
        "state": state,
        "lat": lat,
        "lon": lon,
        "raw": daily_actual,
        "corrected": daily_actual * 0.9,  # Simple bias correction
        "pHeavy": round(p_heavy, 3),
        "pVeryHeavy": round(p_very_heavy, 3),
        "pExtreme": round(p_extreme, 3),
        "regime": regime,
        "imd_warning_level": warning_level["level"],
        "imd_warning_color": warning_level["color"],
        "imd_warning_label": warning_level["label"],
        "imd_warnings": warning_codes,
        "imd_rainfall_actual": daily_actual,
        "imd_rainfall_normal": daily_normal,
        "imd_rainfall_departure": daily_departure,
        "imd_rainfall_category": rainfall_category,
        "data_source": "IMD_real_time",
    }
