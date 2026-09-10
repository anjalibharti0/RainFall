# REGIME-AWARE AI POST-PROCESSING OF MONSOON RAINFALL FORECASTS

**Problem Statement | Architecture & Implementation Plan**

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Problem Analysis](#2-problem-analysis)
3. [System Architecture](#3-system-architecture)
4. [Data Pipeline Design](#4-data-pipeline-design)
5. [ML Module Architecture](#5-ml-module-architecture)
6. [API Layer Design](#6-api-layer-design)
7. [Frontend Dashboard Design](#7-frontend-dashboard-design)
8. [Verification Framework](#8-verification-framework)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Research References](#10-research-references)

---

## 1. EXECUTIVE SUMMARY

### Problem

Rainfall forecast errors over India vary with weather regimes (active monsoon, break monsoon, depression, orographic, coastal, western disturbances). A single bias-correction method fails across all situations.

### Solution

An AI/ML-based post-processing system that:
1. **Classifies** the prevailing weather regime
2. **Applies** regime-specific bias correction to raw NWP rainfall forecasts
3. **Generates** heavy rainfall probability products
4. **Produces** district-level rainfall forecast tables/maps
5. **Verifies** skill using standard meteorological metrics

### Expected Outcomes

| Output | Description |
|--------|-------------|
| Weather Regime Classifier | Classification of active, break, depression, coastal/orographic regimes |
| Bias-Corrected Rainfall | Improved rainfall forecast vs raw NWP output |
| Heavy Rainfall Probability | Probability of rainfall exceeding operational thresholds |
| District-Level Product | User-friendly rainfall forecast table/map |
| Verification Report | Skill comparison using RMSE, ETS, CSI, POD, FAR, FSS |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Backend | Python (scikit-learn, TensorFlow/PyTorch, xarray, pandas) |
| API Layer | FastAPI / Flask |
| Frontend | React.js + Tailwind CSS |
| Visualization | Plotly, Leaflet.js, Chart.js |
| Data Storage | PostgreSQL + MinIO (object storage for NetCDF) |
| Deployment | Docker + Docker Compose |

---

## 2. PROBLEM ANALYSIS

### 2.1 Weather Regimes Over India

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDIAN MONSOON REGIMES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. ACTIVE MONSOON                                              │
│     • Large-scale organized convection                          │
│     • Well-distributed rainfall over central India              │
│     • Strong monsoon trough                                     │
│     • Duration: 3-7 days                                        │
│                                                                 │
│  2. BREAK MONSOON                                               │
│     • Suppressed rainfall over central India                    │
│     • Rainfall shifts to foothills/northeast                    │
│     • Weak monsoon trough                                       │
│     • Duration: 3-5 days                                        │
│                                                                 │
│  3. MONSOON LOWS / DEPRESSIONS                                  │
│     • Cyclonic circulations over Bay of Bengal                  │
│     • Heavy rainfall over west coast & central India            │
│     • Organized systems with clear track                        │
│     • Duration: 2-5 days                                        │
│                                                                 │
│  4. OROGRAPHIC RAINFALL                                         │
│     • Terrain-enhanced rainfall                                 │
│     • Western Ghats, NE India, Himalayan foothills              │
│     • Localized, intense rainfall                               │
│     • Duration: Event-based                                     │
│                                                                 │
│  5. COASTAL RAINFALL                                            │
│     • Sea-breeze convergence zones                              │
│     • Coastal urban flooding                                    │
│     • Mumbai, Chennai, Kochi corridors                          │
│     • Duration: Hours to 1-2 days                               │
│                                                                 │
│  6. WESTERN DISTURBANCES                                        │
│     • Extratropical systems from Mediterranean                  │
│     • Winter rainfall over north India                          │
│     • Pre-monsoon convective events                             │
│     • Duration: 2-4 days                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Why Single Bias Correction Fails

| Regime | Bias Characteristic | Why Generic Fails |
|--------|--------------------|--------------------|
| Active Monsoon | Systematic wet bias in NWP | Overactive convection schemes |
| Break Monsoon | Dry bias in central India | Trough position errors |
| Depression | Underestimates heavy rainfall | Resolution limitations |
| Orographic | Extreme wet bias over mountains | Poor terrain representation |
| Coastal | Phase errors in diurnal cycle | Land-sea mask issues |
| Western Disturbances | Track & intensity errors | Sparse observation network |

### 2.3 Indian Districts & Grid Coverage

```
┌─────────────────────────────────────────────────────────────────┐
│                    COVERAGE MAP                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NWP Grid Resolution: ~25km (GFS) / ~9km (ECMWF)              │
│  IMD Observed Data: 0.25° × 0.25° grid (APHRODITE/IMD gridded) │
│  District Boundaries: 780+ districts across India               │
│                                                                 │
│  Key Rainfall Zones:                                            │
│  ┌──────────┬─────────────────────────────────────────┐        │
│  │ Zone     │ Districts                               │        │
│  ├──────────┼─────────────────────────────────────────┤        │
│  │ West     │ Maharashtra, Goa, Karnataka coast       │        │
│  │ Coast    │ Kerala coast                            │        │
│  │ Central  │ Madhya Pradesh, Chhattisgarh, Vidarbha  │        │
│  │ North    │ UP, Bihar, Jharkhand, Punjab            │        │
│  │ Northeast│ Assam, Meghalaya, Arunachal Pradesh     │        │
│  │ South    │ Tamil Nadu, Andhra Pradesh, Telangana   │        │
│  └──────────┴─────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. SYSTEM ARCHITECTURE

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA SOURCES                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ IMD GFS  │  │ ECMWF    │  │ IMD Obs  │  │ Station  │          │   │
│  │  │ Forecasts│  │ Forecasts│  │ Rainfall │  │ Data     │          │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │   │
│  │       └──────────────┴──────────────┴──────────────┘               │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA INGESTION LAYER                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ NetCDF Parser│  │ Grid Interp  │  │ Data Quality │             │   │
│  │  │              │  │ (Regridding) │  │ Control      │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Temporal     │  │ Spatial      │  │ Feature      │             │   │
│  │  │ Alignment    │  │ Averaging    │  │ Engineering  │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ML PROCESSING LAYER                               │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              MODULE 1: REGIME CLASSIFIER                     │   │   │
│  │  │  • Input: NWP fields (wind, OLR, moisture, pressure)       │   │   │
│  │  │  • Model: CNN / Random Forest / LSTM                        │   │   │
│  │  │  • Output: Regime label (6 classes)                         │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              MODULE 2: BIAS CORRECTOR                        │   │   │
│  │  │  • Input: Raw NWP rainfall + regime label                  │   │   │
│  │  │  • Model: Regime-specific ML corrector                      │   │   │
│  │  │  • Output: Bias-corrected rainfall forecast                 │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              MODULE 3: PROBABILITY ESTIMATOR                 │   │   │
│  │  │  • Input: Bias-corrected forecast + ensemble spread         │   │   │
│  │  │  • Model: Quantile regression / Gaussian process            │   │   │
│  │  │  • Output: P(rainfall > threshold) for each district       │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PRODUCT GENERATION LAYER                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ District     │  │ Probability  │  │ Verification │             │   │
│  │  │ Aggregation  │  │ Maps         │  │ Reports      │             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │                                           │
│                                ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    API + FRONTEND LAYER                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ FastAPI      │  │ React.js     │  │ Leaflet Maps │             │   │
│  │  │ REST API     │  │ Dashboard    │  │ Visualization│             │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW DIAGRAM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  T+0 (Now)                                                     │
│    │                                                            │
│    ├──► Ingest NWP forecast (GFS/ECMWF)                       │
│    │    • Temperature, Wind, Humidity, Pressure, OLR           │
│    │    • Rainfall (total, convective, large-scale)            │
│    │                                                            │
│    ├──► Ingest observed rainfall (IMD gridded)                 │
│    │    • Real-time rain gauge data                             │
│    │    • Satellite-merged rainfall                             │
│    │                                                            │
│    ├──► Feature Engineering                                    │
│    │    • Wind shear (200-850 hPa)                             │
│    │    • Moisture flux convergence                             │
│    │    • OLR anomalies                                         │
│    │    • Vorticity (850 hPa)                                  │
│    │    • CAPE/CIN indices                                      │
│    │    • Terrain slope/orientation                             │
│    │    • Distance to coast                                     │
│    │                                                            │
│    ▼                                                            │
│  T+1 (Processing)                                              │
│    │                                                            │
│    ├──► REGIME CLASSIFICATION                                   │
│    │    • Input: Features at T+0                               │
│    │    • Output: Regime label + confidence                    │
│    │    • Regimes: Active/Break/Depression/Orographic/Coastal/ │
│    │              Western Disturbance                           │
│    │                                                            │
│    ├──► BIAS CORRECTION                                        │
│    │    • Input: Raw NWP rainfall + regime label              │
│    │    • Model: Regime-specific corrector                     │
│    │    • Output: Bias-corrected rainfall field                │
│    │                                                            │
│    ├──► PROBABILITY ESTIMATION                                  │
│    │    • Input: Corrected forecast + ensemble spread          │
│    │    • Output: P(R > 7.5cm), P(R > 12.5cm), P(R > 25cm)  │
│    │                                                            │
│    ▼                                                            │
│  T+2 (Output)                                                  │
│    │                                                            │
│    ├──► District-level aggregation                              │
│    │    • Map grid points to district boundaries               │
│    │    • Compute district-mean rainfall                       │
│    │                                                            │
│    ├──► Product generation                                      │
│    │    • District forecast table                               │
│    │    • Probability maps                                      │
│    │    • Verification metrics                                  │
│    │                                                            │
│    └──► API response → Frontend display                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. DATA PIPELINE DESIGN

### 4.1 Data Sources

| Source | Data Type | Resolution | Format | Access |
|--------|-----------|------------|--------|--------|
| **IMD GFS** | NWP Forecasts | ~25km, 6-hourly | GRIB2/NetCDF | IMD Data Portal |
| **ECMWF IFS** | NWP Forecasts | ~9km, 6-hourly | GRIB2/NetCDF | ECMWF MARS |
| **IMD Gridded Rain** | Observed Rainfall | 0.25° × 0.25°, daily | NetCDF | IMD Open Data |
| **APHRODITE** | Observed Rainfall | 0.25° × 0.25°, daily | NetCDF | APHRODITE Portal |
| **IMD Station** | Station Observations | Point data | CSV | IMD Open Data |
| **IMD Districts** | Shapefiles | Vector | Shapefile | census.gov.in |

### 4.2 Feature Engineering

```python
# Feature Categories for Regime Classification

FEATURES = {
    "large_scale_dynamics": [
        "u_wind_200hPa",        # Upper-level zonal wind
        "v_wind_850hPa",        # Low-level meridional wind
        "wind_shear_200_850",   # Vertical wind shear
        "vorticity_850hPa",     # Low-level vorticity
        "divergence_200hPa",    # Upper-level divergence
        "omega_500hPa",         # Vertical velocity
    ],
    "moisture": [
        "q_700hPa",            # Mid-level specific humidity
        "ivt",                  # Integrated vapor transport
        "tpw",                  # Total precipitable water
        "moisture_flux_conv",   # Moisture flux convergence
    ],
    "thermodynamics": [
        "cape",                 # Convective available potential energy
        "cin",                  # Convective inhibition
        "li",                   # Lifted index
        "k_index",              # K-index stability
        "total_totals",         # Total totals index
    ],
    "radiation": [
        "olr",                  # Outgoing longwave radiation
        "olr_anomaly",          # OLR anomaly from climatology
    ],
    "surface": [
        "sst",                  # Sea surface temperature
        "land_mask",            # Land-sea fraction
        "terrain_height",       # Elevation
        "terrain_slope",        # Slope magnitude
        "terrain_orientation",  # Aspect
        "distance_to_coast",    # Distance to nearest coast
    ],
    "temporal": [
        "diurnal_cycle_phase",  # Peak rainfall hour
        "diurnal_cycle_amplitude",
        "persistence_index",    # Regime persistence
    ]
}
```

### 4.3 Data Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PROCESSING PIPELINE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STEP 1: DATA INGESTION                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Download GRIB2/NetCDF from IMD/ECMWF                │   │
│  │  • Parse using cfgrib / xarray                          │   │
│  │  • Extract variables of interest                        │   │
│  │  • Store as intermediate NetCDF files                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 2: GRID HARMONIZATION                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Regrid all data to common 0.25° × 0.25° grid        │   │
│  │  • Use xarray interp / xesmf for regridding            │   │
│  │  • Handle land-sea mask interpolation                   │   │
│  │  • Ensure consistent coordinate system (WGS84)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 3: TEMPORAL ALIGNMENT                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Align forecast and observation time steps            │   │
│  │  • Handle lead time offsets (T+24, T+48, T+72)         │   │
│  │  • Aggregate to daily/6-hourly as needed               │   │
│  │  • Create matched forecast-observation pairs            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 4: FEATURE ENGINEERING                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Compute derived features (wind shear, CAPE, etc.)   │   │
│  │  • Calculate anomalies from climatology                 │   │
│  │  • Spatial averaging for regional features              │   │
│  │  • Compute terrain metrics from DEM                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 5: LABEL GENERATION (for training)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Define regime labels based on:                       │   │
│  │    - IMD operational criteria                           │   │
│  │    - Spatial rainfall distribution patterns             │   │
│  │    - Large-scale circulation indices                    │   │
│  │  • Create labeled training dataset                      │   │
│  │  • Handle class imbalance (SMOTE/class weights)         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  STEP 6: TRAIN/VALIDATION/TEST SPLIT                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Training: 2010-2019 (monsoon seasons)               │   │
│  │  • Validation: 2020-2021                                │   │
│  │  • Testing: 2022-2024                                   │   │
│  │  • Leave-one-year-out cross-validation                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Regime Labeling Criteria

```python
# Regime classification based on IMD criteria + spatial patterns

REGIME_CRITERIA = {
    "active_monsoon": {
        "all_india_rainfall": "> 120% of long-period average",
        "central_india_rainfall": "> 100% of LPA",
        "monsoon_trough": "well-defined over Gangetic plains",
        "olr": "< -15 W/m² anomaly over central India",
        "wind_shear": "> 15 m/s (200-850 hPa)"
    },
    "break_monsoon": {
        "all_india_rainfall": "< 80% of LPA",
        "central_india_rainfall": "< 60% of LPA",
        "monsoon_trough": "weak or absent",
        "rainfall_shift": "to foothills/northeast",
        "olr": "> +5 W/m² anomaly over central India"
    },
    "depression": {
        "vorticity_850hPa": "> 2 × 10⁻⁵ s⁻¹",
        "wind_speed": "> 17 m/s at surface",
        "track": "Bay of Bengal → landfall",
        "rainfall": "heavy over west coast/central India"
    },
    "orographic": {
        "rainfall_pattern": "terrain-following",
        "location": "Western Ghats, NE India, Himalayas",
        "wind_direction": "perpendicular to terrain",
        "duration": "persistent (> 6 hours)"
    },
    "coastal": {
        "rainfall_pattern": "coastal-parallel band",
        "location": "within 100km of coast",
        "mechanism": "sea-breeze convergence / off-shore trough",
        "diurnal": "afternoon-evening peak"
    },
    "western_disturbance": {
        "location": "northwest India",
        "wind": "westerly flow at 500hPa",
        "temperature": "cold air advection aloft",
        "season": "pre-monsoon / post-monsoon"
    }
}
```

---

## 5. ML MODULE ARCHITECTURE

### 5.1 Module 1: Regime Classifier

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGIME CLASSIFIER ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT: Multi-variable fields (H × W × C)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Shape: (batch, 30, 30, num_features)                   │   │
│  │  Features: 20+ meteorological variables                 │   │
│  │  Grid: 30 × 30 points (central India focus)            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              MODEL OPTIONS                               │   │
│  │                                                          │   │
│  │  Option A: CNN (Convolutional Neural Network)           │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  Conv2D(32, 3×3) → ReLU → MaxPool              │   │   │
│  │  │  Conv2D(64, 3×3) → ReLU → MaxPool              │   │   │
│  │  │  Conv2D(128, 3×3) → ReLU → GlobalAvgPool       │   │   │
│  │  │  Dense(256) → Dropout(0.3) → Dense(6, softmax) │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  Option B: Random Forest (Baseline)                    │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  Flatten spatial features                       │   │   │
│  │  │  Regional means/std for each variable           │   │   │
│  │  │  RF classifier with 500 trees                   │   │   │
│  │  │  Feature importance for interpretability        │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  Option C: LSTM (Temporal sequences)                    │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  Time series of features (past 5 days)          │   │   │
│  │  │  LSTM(128) → LSTM(64) → Dense(6, softmax)      │   │   │
│  │  │  Captures temporal evolution of regimes         │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  OUTPUT: Regime probabilities + confidence                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  regime = "active_monsoon"                              │   │
│  │  confidence = 0.87                                       │   │
│  │  all_probs = [0.87, 0.05, 0.03, 0.02, 0.02, 0.01]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Module 2: Bias Corrector

```
┌─────────────────────────────────────────────────────────────────┐
│                    BIAS CORRECTOR ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT:                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Raw NWP rainfall field (H × W)                       │   │
│  │  • Regime label (one-hot encoded)                        │   │
│  │  • Meteorological context features                       │   │
│  │  • Lead time (T+24, T+48, T+72, ...)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              REGIME-SPECIFIC CORRECTORS                   │   │
│  │                                                          │   │
│  │  For each regime r ∈ {active, break, depression, ...}:  │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  Corrector_r:                                    │   │   │
│  │  │    Input: raw_rain + context + lead_time         │   │   │
│  │  │    Model: Gradient Boosting / Neural Network    │   │   │
│  │  │    Output: corrected_rain                        │   │   │
│  │  │                                                  │   │   │
│  │  │  Trained separately on regime-specific data      │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CORRECTION METHODS                          │   │
│  │                                                          │   │
│  │  Method 1: Quantile Mapping (Baseline)                  │   │
│  │  • Map forecast CDF to observed CDF                     │   │
│  │  • Regime-specific CDFs                                 │   │
│  │                                                          │   │
│  │  Method 2: ML Regression (Primary)                      │   │
│  │  • XGBoost/LightGBM with regime features               │   │
│  │  • Predict correction factor per grid point             │   │
│  │                                                          │   │
│  │  Method 3: Neural Network (Advanced)                    │   │
│  │  • U-Net style architecture for spatial correction     │   │
│  │  • Encoder-decoder with skip connections                │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  OUTPUT: Bias-corrected rainfall field (H × W)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  corrected_rainfall = f(raw_nwp, regime, context)      │   │
│  │  Constraint: corrected_rain ≥ 0 (non-negative)         │   │
│  │  Preserves: spatial patterns, temporal evolution        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Module 3: Probability Estimator

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROBABILITY ESTIMATOR ARCHITECTURE             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT:                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Bias-corrected rainfall forecast                     │   │
│  │  • Forecast uncertainty (ensemble spread / model spread)│   │
│  │  • Regime label + confidence                            │   │
│  │  • Historical error statistics                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              THRESHOLDS (IMD Operational)                │   │
│  │                                                          │   │
│  │  • Moderate Rainfall:    R ≥ 7.5 mm/day                │   │
│  │  • Heavy Rainfall:       R ≥ 64.5 mm/day               │   │
│  │  • Very Heavy Rainfall:  R ≥ 124.5 mm/day              │   │
│  │  • Extremely Heavy:      R ≥ 244.5 mm/day              │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ESTIMATION METHODS                          │   │
│  │                                                          │   │
│  │  Method 1: Ensemble-based                               │   │
│  │  • P(R > T) = count(R_ens > T) / N_ens                │   │
│  │                                                          │   │
│  │  Method 2: Quantile Regression                          │   │
│  │  • Learn conditional quantiles of rainfall              │   │
│  │  • Interpolate to get exceedance probability            │   │
│  │                                                          │   │
│  │  Method 3: Bayesian Model Averaging                     │   │
│  │  • Combine multiple probability estimates               │   │
│  │  • Weight by model skill                                │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  OUTPUT: District-level exceedance probabilities                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  district: "Mumbai"                                     │   │
│  │  P(R > 7.5mm):   0.92  (Very likely)                   │   │
│  │  P(R > 64.5mm):  0.78  (Likely)                        │   │
│  │  P(R > 124.5mm): 0.34  (Possible)                      │   │
│  │  P(R > 244.5mm): 0.08  (Unlikely)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Model Training Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL TRAINING STRATEGY                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRAINING DATA SPLIT:                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Training:   June 2010 - September 2019 (10 seasons)    │   │
│  │  Validation: June 2020 - September 2021 (2 seasons)     │   │
│  │  Testing:    June 2022 - September 2024 (3 seasons)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  CROSS-VALIDATION:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Leave-one-year-out (LOO-YO)                          │   │
│  │  • Spatial cross-validation (hold out regions)          │   │
│  │  • Temporal cross-validation (hold out time periods)    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  CLASS BALANCE:                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Regime Distribution (approximate):                     │   │
│  │  • Active Monsoon:     25%                              │   │
│  │  • Break Monsoon:      20%                              │   │
│  │  • Depression:         15%                              │   │
│  │  • Orographic:         20%                              │   │
│  │  • Coastal:            15%                              │   │
│  │  • Western Disturbance: 5%                              │   │
│  │                                                          │   │
│  │  Mitigation: SMOTE, class weights, focal loss           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  HYPERPARAMETER TUNING:                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Optuna / Ray Tune for automated tuning              │   │
│  │  • Bayesian optimization                                │   │
│  │  • Early stopping on validation loss                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. API LAYER DESIGN

### 6.1 FastAPI Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                    API ENDPOINTS                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  POST /api/v1/forecast/process                          │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Trigger full post-processing pipeline                │   │
│  │  • Input: date, lead_time, model_source                │   │
│  │  • Output: job_id for async processing                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/regime/classify/{date}                     │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Get regime classification for a given date          │   │
│  │  • Output: regime label, confidence, spatial map       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/forecast/district/{district_id}            │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Get district-level rainfall forecast                │   │
│  │  • Output: rainfall amount, regime, probabilities      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/probability/map/{date}                     │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Get heavy rainfall probability map                  │   │
│  │  • Output: GeoJSON with district-wise probabilities    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/verification/report/{date}                 │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Get verification metrics for a forecast             │   │
│  │  • Output: RMSE, ETS, CSI, POD, FAR, FSS              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/forecast/table/{date}                      │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Get tabular forecast for all districts              │   │
│  │  • Output: JSON table with district forecasts          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GET /api/v1/historical/{district_id}                   │   │
│  │  ─────────────────────────────────────────────────────  │   │
│  │  • Get historical forecast vs observed comparison      │   │
│  │  • Output: time series, skill scores                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Database Schema

```sql
-- Core tables for the rainfall post-processing system

-- Districts table
CREATE TABLE districts (
    district_id SERIAL PRIMARY KEY,
    district_name VARCHAR(100),
    state_name VARCHAR(100),
    geom GEOMETRY(MULTIPOLYGON, 4326),
    centroid_lat FLOAT,
    centroid_lon FLOAT,
    zone VARCHAR(50)  -- west_coast, central, north, etc.
);

-- Regime classifications
CREATE TABLE regime_classifications (
    id SERIAL PRIMARY KEY,
    forecast_date DATE,
    regime_label VARCHAR(50),
    confidence FLOAT,
    model_version VARCHAR(20),
    features JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bias-corrected forecasts
CREATE TABLE corrected_forecasts (
    id SERIAL PRIMARY KEY,
    forecast_date DATE,
    lead_time INT,  -- hours
    district_id INT REFERENCES districts(district_id),
    raw_rainfall FLOAT,
    corrected_rainfall FLOAT,
    regime_used VARCHAR(50),
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Heavy rainfall probabilities
CREATE TABLE rainfall_probabilities (
    id SERIAL PRIMARY KEY,
    forecast_date DATE,
    lead_time INT,
    district_id INT REFERENCES districts(district_id),
    p_moderate FLOAT,   -- P(R > 7.5mm)
    p_heavy FLOAT,      -- P(R > 64.5mm)
    p_very_heavy FLOAT, -- P(R > 124.5mm)
    p_extreme FLOAT,    -- P(R > 244.5mm)
    regime_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Verification metrics
CREATE TABLE verification_metrics (
    id SERIAL PRIMARY KEY,
    forecast_date DATE,
    lead_time INT,
    region VARCHAR(100),
    regime VARCHAR(50),
    rmse FLOAT,
    mae FLOAT,
    bias_ratio FLOAT,
    ets FLOAT,
    csi FLOAT,
    pod FLOAT,
    far FLOAT,
    fss FLOAT,
    threat_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Model versions and metadata
CREATE TABLE model_metadata (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    model_version VARCHAR(20),
    training_date DATE,
    training_period VARCHAR(100),
    hyperparameters JSONB,
    performance_metrics JSONB,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## 7. FRONTEND DASHBOARD DESIGN

### 7.1 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND DASHBOARD                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  HEADER: Regime-Aware Rainfall Post-Processing          │   │
│  │  [Date Picker] [Lead Time] [Model Source] [Run]        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────┬──────────────────────────────┐   │
│  │                          │                              │   │
│  │   CURRENT REGIME         │   RAINFALL MAP              │   │
│  │   ┌──────────────────┐  │   ┌──────────────────────┐  │   │
│  │   │ Active Monsoon   │  │   │   Leaflet.js map     │  │   │
│  │   │ Confidence: 87%  │  │   │   with district      │  │   │
│  │   │ Duration: 3 days │  │   │   boundaries and     │  │   │
│  │   └──────────────────┘  │   │   color-coded        │  │   │
│  │                          │   │   rainfall           │  │   │
│  │   REGIME FEATURES       │   │                      │  │   │
│  │   • Wind Shear: 18 m/s  │   │   Legend:            │  │   │
│  │   • OLR: -20 W/m²      │   │   ■ < 7.5mm          │  │   │
│  │   • CAPE: 1500 J/kg     │   │   ■ 7.5-35mm         │  │   │
│  │   • Vorticity: High    │   │   ■ 35-65mm           │  │   │
│  │                          │   │   ■ 65-125mm         │  │   │
│  │                          │   │   ■ > 125mm          │  │   │
│  │                          │   └──────────────────────┘  │   │
│  │                          │                              │   │
│  └──────────────────────────┴──────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────┬──────────────────────────────┐   │
│  │                          │                              │   │
│  │   DISTRICT TABLE         │   PROBABILITY MAP            │   │
│  │   ┌──────────────────┐  │   ┌──────────────────────┐  │   │
│  │   │ District │ Rain  │  │   │   P(Heavy Rainfall)  │  │   │
│  │   ├──────────┼───────┤  │   │   Color-coded by     │  │   │
│  │   │ Mumbai   │ 85mm  │  │   │   exceedance prob.   │  │   │
│  │   │ Pune     │ 42mm  │  │   │                      │  │   │
│  │   │ Nagpur   │ 28mm  │  │   │   Legend:            │  │   │
│  │   │ Delhi    │ 12mm  │  │   │   ■ < 25%            │  │   │
│  │   │ Kolkata  │ 65mm  │  │   │   ■ 25-50%           │  │   │
│  │   │ ...      │ ...   │  │   │   ■ 50-75%           │  │   │
│  │   └──────────────────┘  │   │   ■ > 75%            │  │   │
│  │                          │   └──────────────────────┘  │   │
│  │   [Export CSV] [Export]  │                              │   │
│  │                          │                              │   │
│  └──────────────────────────┴──────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   VERIFICATION PANEL                                     │   │
│  │   ┌─────────────────────────────────────────────────┐   │   │
│  │   │  Metric     │ Raw NWP │ Corrected │ Improvement │   │   │
│  │   ├─────────────┼─────────┼───────────┼─────────────┤   │   │
│  │   │  RMSE       │ 12.5mm  │  8.3mm    │   +33%      │   │   │
│  │   │  ETS        │ 0.35    │  0.52     │   +49%      │   │   │
│  │   │  CSI        │ 0.28    │  0.45     │   +61%      │   │   │
│  │   │  POD        │ 0.62    │  0.78     │   +26%      │   │   │
│  │   │  FAR        │ 0.45    │  0.32     │   -29%      │   │   │
│  │   │  FSS        │ 0.41    │  0.58     │   +41%      │   │   │
│  │   └─────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │   [Skill by Regime] [Skill by Lead Time] [Download]    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 React Component Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Header.jsx              # Date picker, controls
│   │   ├── Sidebar.jsx             # Navigation
│   │   └── Footer.jsx
│   ├── maps/
│   │   ├── RainfallMap.jsx         # Leaflet rainfall map
│   │   ├── ProbabilityMap.jsx      # Exceedance probability map
│   │   ├── RegimeMap.jsx           # Regime classification map
│   │   └── DistrictBoundaries.jsx  # GeoJSON district layer
│   ├── charts/
│   │   ├── VerificationChart.jsx   # Metric comparison bar chart
│   │   ├── TimeSeriesChart.jsx     # Historical trend
│   │   ├── RegimePieChart.jsx      # Regime distribution
│   │   └── LeadTimeChart.jsx       # Skill vs lead time
│   ├── tables/
│   │   ├── DistrictTable.jsx       # District forecast table
│   │   ├── VerificationTable.jsx   # Metrics table
│   │   └── RegimeHistory.jsx       # Past regime classifications
│   ├── panels/
│   │   ├── RegimePanel.jsx         # Current regime info
│   │   ├── ProbabilityPanel.jsx    # Heavy rain probabilities
│   │   └── AlertPanel.jsx          # Heavy rain warnings
│   └── common/
│       ├── LoadingSpinner.jsx
│       ├── DateRangePicker.jsx
│       └── ExportButton.jsx
├── hooks/
│   ├── useForecast.js              # API call for forecast
│   ├── useRegime.js                # Regime classification data
│   └── useVerification.js          # Verification metrics
├── services/
│   └── api.js                      # Axios API calls
├── utils/
│   ├── colorScales.js              # Rainfall color mapping
│   ├── districtMapping.js          # Grid to district mapping
│   └── formatters.js               # Number/date formatting
└── App.jsx                         # Main application
```

### 7.3 Key Frontend Features

| Feature | Description | Component |
|---------|-------------|-----------|
| **Interactive Map** | Zoomable/pannable map with district boundaries | Leaflet.js |
| **Rainfall Overlay** | Color-coded rainfall amounts on map | GeoJSON + choropleth |
| **District Selection** | Click district to see detailed forecast | onClick handler |
| **Regime Badge** | Visual indicator of current regime | RegimePanel |
| **Probability Dial** | Gauge showing exceedance probability | Gauge chart |
| **Verification Dashboard** | Compare raw vs corrected metrics | Bar charts |
| **Export Options** | Download CSV, PNG, PDF | ExportButton |
| **Responsive Design** | Works on mobile, tablet, desktop | Tailwind CSS |
| **Dark Mode** | Toggle for night-time viewing | Theme context |
| **Auto-refresh** | Update data every 6 hours | setInterval |

---

## 8. VERIFICATION FRAMEWORK

### 8.1 Metrics Definition

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERIFICATION METRICS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RMSE (Root Mean Square Error)                              │
│  ─────────────────────────────────────────────────────────────  │
│  RMSE = √[Σ(forecast - observed)² / N]                        │
│  • Measures average magnitude of forecast error                │
│  • Units: same as rainfall (mm/day)                            │
│  • Lower is better                                              │
│                                                                 │
│  2. ETS (Equitable Threat Score)                               │
│  ─────────────────────────────────────────────────────────────  │
│  ETS = (hits - hits_random) / (hits + misses + false_alarms    │
│                                - hits_random)                  │
│  • Measures forecast skill for exceedance events               │
│  • Range: -1/3 to 1 (0 = no skill)                            │
│  • Accounts for hits due to chance                             │
│                                                                 │
│  3. CSI (Critical Success Index / Threat Score)                │
│  ─────────────────────────────────────────────────────────────  │
│  CSI = hits / (hits + misses + false_alarms)                   │
│  • Measures forecast accuracy for events                       │
│  • Range: 0 to 1 (1 = perfect)                                │
│  • Ignores correct negatives                                   │
│                                                                 │
│  4. POD (Probability of Detection / Hit Rate)                  │
│  ─────────────────────────────────────────────────────────────  │
│  POD = hits / (hits + misses)                                  │
│  • Fraction of observed events correctly forecast              │
│  • Range: 0 to 1 (1 = perfect detection)                      │
│  • Also called recall or sensitivity                           │
│                                                                 │
│  5. FAR (False Alarm Ratio)                                    │
│  ─────────────────────────────────────────────────────────────  │
│  FAR = false_alarms / (hits + false_alarms)                    │
│  • Fraction of forecast events that did not occur              │
│  • Range: 0 to 1 (0 = no false alarms)                        │
│  • Lower is better                                              │
│                                                                 │
│  6. FSS (Fractions Skill Score)                                │
│  ─────────────────────────────────────────────────────────────  │
│  FSS = 1 - [MSE(obs, forecast) / MSE(obs climatology,         │
│                                        forecast climatology)]   │
│  • Neighborhood-based spatial verification                     │
│  • Accounts for spatial displacement errors                    │
│  • Range: 0 to 1 (1 = perfect)                                │
│  • Scale-aware metric                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Contingency Table

```
                    OBSERVED
                 Yes       No
            ┌─────────┬─────────┐
Forecast    │  HITS   │ FALSE   │
   Yes      │   (a)   │ ALARMS  │
            │         │   (b)   │
            ├─────────┼─────────┤
Forecast    │ MISSES  │ CORRECT │
   No       │   (c)   │NEGATIVES│
            │         │   (d)   │
            └─────────┴─────────┘

From contingency table:
  CSI  = a / (a + b + c)
  POD  = a / (a + c)
  FAR  = b / (a + b)
  ETS  = (a - ar) / (a + b + c - ar)
       where ar = (a+b)(a+c) / N
```

### 8.3 Verification Strategy

| Dimension | Approach | Purpose |
|-----------|----------|---------|
| **Temporal** | Daily, Pentadal, Monthly | Short & medium range |
| **Spatial** | Grid-level, District, Region | Multi-scale assessment |
| **Regime-wise** | Per regime class | Regime-specific skill |
| **Lead Time** | T+24, T+48, T+72, T+120 | Degradation with time |
| **Threshold** | 7.5mm, 64.5mm, 124.5mm | Heavy rain events |
| **Seasonal** | JJAS (monsoon) | Seasonal summary |
| **Comparative** | Raw vs Corrected | Improvement quantification |

### 8.4 Expected Skill Improvements

| Metric | Raw NWP | After Post-Processing | Expected Improvement |
|--------|---------|----------------------|---------------------|
| RMSE | 12-15 mm/day | 8-10 mm/day | 30-40% |
| ETS (64.5mm) | 0.25-0.35 | 0.45-0.55 | 50-80% |
| CSI (64.5mm) | 0.20-0.30 | 0.40-0.50 | 70-100% |
| POD (64.5mm) | 0.55-0.65 | 0.75-0.85 | 20-35% |
| FAR (64.5mm) | 0.40-0.50 | 0.25-0.35 | 30-40% reduction |
| FSS (64.5mm) | 0.35-0.45 | 0.55-0.65 | 40-60% |

---

## 9. IMPLEMENTATION ROADMAP

### 9.1 Phase Plan

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION ROADMAP                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: FOUNDATION (Weeks 1-4)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Week 1-2: Data Pipeline                                │   │
│  │  • Set up data ingestion from IMD/ECMWF               │   │
│  │  • Build NetCDF parser and grid regridding             │   │
│  │  • Create feature engineering module                   │   │
│  │  • Database setup (PostgreSQL + schema)                │   │
│  │                                                          │   │
│  │  Week 3-4: Regime Classification                        │   │
│  │  • Define regime labeling criteria                     │   │
│  │  • Implement baseline Random Forest classifier         │   │
│  │  • Train and validate on historical data               │   │
│  │  • Achieve >70% classification accuracy                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  PHASE 2: CORE ML (Weeks 5-8)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Week 5-6: Bias Correction                              │   │
│  │  • Implement quantile mapping (baseline)               │   │
│  │  • Build regime-specific ML correctors                 │   │
│  │  • Train XGBoost/LightGBM correctors                   │   │
│  │  • Validate bias reduction                             │   │
│  │                                                          │   │
│  │  Week 7-8: Probability Estimation                       │   │
│  │  • Implement ensemble-based probabilities              │   │
│  │  • Build quantile regression models                    │   │
│  │  • Calibrate probability estimates                     │   │
│  │  • Validate reliability diagrams                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  PHASE 3: PRODUCTS (Weeks 9-12)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Week 9-10: API Development                             │   │
│  │  • Build FastAPI endpoints                              │   │
│  │  • Implement district aggregation                      │   │
│  │  • Create GeoJSON product generation                   │   │
│  │  • API testing and documentation                       │   │
│  │                                                          │   │
│  │  Week 11-12: Frontend Dashboard                         │   │
│  │  • React.js application setup                          │   │
│  │  • Leaflet.js map integration                          │   │
│  │  • District table and charts                           │   │
│  │  • Verification dashboard                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  PHASE 4: POLISH (Weeks 13-16)                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Week 13-14: Advanced Features                         │   │
│  │  • CNN-based regime classifier (improve accuracy)      │   │
│  │  • U-Net bias corrector (spatial awareness)            │   │
│  │  • Real-time data integration                          │   │
│  │  • Alert system for heavy rainfall warnings            │   │
│  │                                                          │   │
│  │  Week 15-16: Testing & Deployment                       │   │
│  │  • End-to-end testing                                  │   │
│  │  • Performance optimization                            │   │
│  │  • Docker containerization                             │   │
│  │  • Documentation and presentation prep                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  TOTAL: 16 weeks (~4 months)                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Milestone Deliverables

| Milestone | Week | Deliverable | Success Criteria |
|-----------|------|-------------|-----------------|
| M1 | 2 | Data pipeline operational | Can ingest IMD GFS + obs data |
| M2 | 4 | Regime classifier v1 | >70% accuracy on test set |
| M3 | 6 | Bias corrector v1 | RMSE reduction >20% |
| M4 | 8 | Probability estimator v1 | Brier score <0.15 |
| M5 | 10 | API endpoints functional | All endpoints return valid JSON |
| M6 | 12 | Dashboard v1 | Interactive map + district table |
| M7 | 14 | Full system integration | End-to-end pipeline working |
| M8 | 16 | Final deployment | Docker deployment + documentation |

### 9.3 Resource Requirements

| Resource | Specification | Purpose |
|----------|--------------|---------|
| **Compute** | GPU server (NVIDIA T4/A10G) | Model training |
| **Storage** | 500GB SSD + 2TB HDD | NetCDF data storage |
| **RAM** | 32GB minimum | Large array processing |
| **Python** | 3.10+ | Core language |
| **Node.js** | 18+ | API server |
| **Docker** | Latest | Containerization |

### 9.4 Tech Stack Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    TECH STACK                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DATA LAYER                                                    │
│  ├── xarray          # NetCDF/GRIB data handling              │
│  ├── cfgrib          # GRIB2 file parsing                     │
│  ├── pandas          # Tabular data processing                │
│  ├── numpy           # Numerical computations                 │
│  └── scipy           # Interpolation, statistics              │
│                                                                 │
│  ML LAYER                                                      │
│  ├── scikit-learn    # Random Forest, metrics, preprocessing  │
│  ├── xgboost         # Gradient boosting corrector            │
│  ├── lightgbm        # Fast gradient boosting                 │
│  ├── tensorflow/     # CNN, LSTM, U-Net                       │
│  │   keras                                                │
│  └── optuna          # Hyperparameter optimization            │
│                                                                 │
│  API LAYER                                                     │
│  ├── fastapi         # REST API framework                     │
│  ├── uvicorn         # ASGI server                            │
│  ├── sqlalchemy      # ORM for PostgreSQL                     │
│  └── geoalchemy2     # PostGIS geometry support               │
│                                                                 │
│  FRONTEND LAYER                                                │
│  ├── react.js        # UI framework                           │
│  ├── tailwindcss     # Styling                                │
│  ├── leaflet.js      # Interactive maps                       │
│  ├── react-leaflet   # React Leaflet bindings                 │
│  ├── plotly.js       # Interactive charts                     │
│  └── recharts        # Simple charts                          │
│                                                                 │
│  DATABASE                                                      │
│  ├── postgresql      # Relational database                    │
│  ├── postgis         # Spatial extensions                     │
│  └── minio           # Object storage (NetCDF files)          │
│                                                                 │
│  DEPLOYMENT                                                    │
│  ├── docker          # Containerization                       │
│  ├── docker-compose  # Multi-container orchestration          │
│  └── nginx           # Reverse proxy                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. RESEARCH REFERENCES

### 10.1 Key Papers

| Area | Reference | Relevance |
|------|-----------|-----------|
| **Bias Correction** | Xia et al. (2012) "Bias correction of monthly precipitation..." | Quantile mapping methodology |
| **Regime Classification** | Ramamurthy et al. (2017) "Prediction of active and break phases..." | Indian monsoon regime detection |
| **ML for Rainfall** | Ravuri et al. (2021) "Nowcasting with deep learning..." | Deep learning for precipitation |
| **Post-Processing** | Vannitsem et al. (2021) "Statistical postprocessing of NWP..." | Comprehensive review |
| **Verification** | Roberts & Lean (2008) "Scale-selective verification..." | FSS methodology |
| **Heavy Rainfall** | Rajeevan et al. (2008) "Prediction of intense rainfall events..." | IMD operational thresholds |
| **AI for Monsoon** | Sneh & Kalsi (2023) "AI/ML for monsoon prediction..." | Indian monsoon AI applications |

### 10.2 IMD References

| Source | Description |
|--------|-------------|
| **IMD Forecast Guidelines** | Operational rainfall threshold definitions |
| **IMD LPA Data** | Long-period averages for regime classification |
| **IMD Gridded Rainfall** | 0.25° observation dataset |
| **IMD District Maps** | Shapefiles for district boundaries |
| **NWP Model Documentation** | GFS/ECMWF model specifications |

### 10.3 Software References

| Library | Version | Purpose |
|---------|---------|---------|
| xarray | 2024+ | Multi-dimensional array analysis |
| cfgrib | 0.9+ | GRIB file reading |
| scikit-learn | 1.3+ | Machine learning baseline |
| xgboost | 2.0+ | Gradient boosting |
| fastapi | 0.100+ | API framework |
| leaflet | 1.9+ | Interactive mapping |
| plotly | 5.15+ | Visualization |

---

## APPENDIX A: DIRECTORY STRUCTURE

```
regime-aware-rainfall/
├── data/
│   ├── raw/                    # Raw NetCDF/GRIB files
│   ├── processed/              # Processed features
│   ├── models/                 # Trained model artifacts
│   └── shapefiles/             # District boundaries
├── src/
│   ├── ingestion/              # Data ingestion scripts
│   │   ├── __init__.py
│   │   ├── gfs_ingest.py
│   │   ├── ecmwf_ingest.py
│   │   └── obs_ingest.py
│   ├── processing/             # Data processing
│   │   ├── __init__.py
│   │   ├── grid_regrid.py
│   │   ├── features.py
│   │   └── labels.py
│   ├── models/                 # ML models
│   │   ├── __init__.py
│   │   ├── regime_classifier.py
│   │   ├── bias_corrector.py
│   │   └── probability_estimator.py
│   ├── verification/           # Verification metrics
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   └── reports.py
│   └── api/                    # FastAPI application
│       ├── __init__.py
│       ├── main.py
│       ├── routes/
│       │   ├── forecast.py
│       │   ├── regime.py
│       │   └── verification.py
│       ├── models/
│       │   └── database.py
│       └── schemas/
│           └── responses.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   └── package.json
├── notebooks/                  # Jupyter notebooks for analysis
├── tests/                      # Unit and integration tests
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── setup.py
└── README.md
```

---

*Architecture document created for Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts*
#   R a i n F a l l  
 