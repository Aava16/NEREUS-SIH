# NEREUS — System Architecture Specification

## 1. Overview
NEREUS is a scientific ocean-data visualization and analysis platform designed for exploring multi-dimensional oceanic datasets, in-situ observational networks, model validation, and predictive ocean intelligence.

---

## 2. Technology Stack

### 2.1 Frontend
- **Core:** React, TypeScript, Vite
- **3D & Spatial Visualization:** Three.js, React Three Fiber (R3F), `@react-three/drei`
- **Animation & Motion Orchestration:** Framer Motion, GSAP (targeted for camera trajectories & complex interpolation)
- **State Management:** Zustand (client/visualizer state)
- **Data Fetching & Cache:** TanStack Query (server state & slice caching)
- **Scientific 2D Charting:** Specialized scientific plotting libraries (e.g., Plotly.js / Chart.js / D3) where genuinely needed

### 2.2 Backend
- **Core Framework:** Python 3.11+, FastAPI, Pydantic v2
- **ORM & Migrations:** SQLAlchemy 2.0, Alembic
- **Scientific Computing & Array Processing:** xarray, NumPy, SciPy, pandas, netCDF4 / h5netcdf
- **Geospatial & Spatial Processing:** Shapely, GeoAlchemy2

### 2.3 Database & Storage Layer
- **Relational & Spatial Database:** PostgreSQL with PostGIS extension
  - Stores application metadata, observations, instruments, locations, dataset catalog, processing jobs, and spatial bounding envelopes.
- **Scientific Data Storage:** NetCDF4 / Zarr on filesystem or object storage
  - Large multidimensional scientific arrays (temperature, salinity, currents, depth, lat, lon, time) reside in scientific formats and are accessed via `xarray`.
  - **Constraint:** Dense multidimensional arrays are **never** stored directly in PostgreSQL tables.

---

## 3. Core Modules

| Module | Purpose & Scope |
| :--- | :--- |
| **EXPLORE** | 3D interactive ocean visualizer: temperature, salinity, ocean currents (U/V/W vectors), depth levels, time scrubbing, 2D/3D planar slices, and volumetric isosurfaces. |
| **OBSERVE** | In-situ observational data integration: ARGO floats, underwater gliders, CTD casts, and moored buoys. |
| **ANALYZE** | Scientific analysis engine: vertical profile comparisons, T-S (Temperature-Salinity) diagrams, temporal trendlines, spatial anomalies, and regional ocean statistics. |
| **DATA** | Dataset ingestion, provider source tracking, spatial/temporal metadata registration, data health, and quality control (QC) information. |
| **VALIDATE** | Numerical model verification against observed in-situ data: MAE, RMSE, bias, Pearson correlation, and collocated profile verification. |
| **INTELLIGENCE** | Scientific anomaly detection, derived marine insights, upwelling/eddy feature identification, and future predictive model integration. |

---

## 4. End-to-End Data Flow

```text
Raw Scientific Data (NetCDF / CSV / In-situ feeds)
  │
  ▼
[Ingestion Pipeline]
  │
  ▼
[Validation & Quality Control (QC flags, bounds)]
  │
  ▼
[Normalization & Coordinate Standardisation (CF Conventions)]
  │
  ├──► [Scientific Storage] (NetCDF4 / Zarr chunked arrays)
  │          ▲
  │          │ (xarray spatial/temporal slicing)
  │          │
  └──► [PostgreSQL / PostGIS] (Metadata, Trajectories, Stations, Jobs)
             ▲
             │ (SQLAlchemy / GeoAlchemy2)
             │
       [FastAPI Backend Services]
             │
             │ (REST / JSON / Typed Array Payloads)
             ▼
     [Frontend Application]
    (Zustand + TanStack Query)
             │
       ┌─────┴────────────────┐
       ▼                      ▼
[3D Ocean Explorer]     [Scientific 2D Analytics]
(Three.js / R3F)        (Profiles, Metrics, Validation)
```

### Strict Architectural Boundaries:
- The **frontend never directly accesses PostgreSQL or raw scientific files**.
- All data access must pass through the **FastAPI backend layer**, which validates, slices, decimates, and formats data payloads specifically for visualization consumption.

---

## 5. Design Philosophy & Visual Aesthetic

- **Scientific & Sophisticated:** Clean, precise, high-density scientific interface built for oceanographers, researchers, and decision-makers.
- **Calm & Spacious:** Generous white space and typography outside the 3D explorer to prevent cognitive fatigue.
- **Atmospheric Contrast:** 
  - **Light Scientific UI:** Breathable, clean light aesthetic for data tables, validation reports, profile cards, and metadata panels.
  - **Cinematic Ocean Environment:** Deep, rich, focused ocean environment inside the 3D WebGL / R3F Canvas.
- **Meaningful Motion:** Animations must serve a functional purpose — communicating state transitions, camera depth adjustments, temporal playback, and spatial coordinate changes.
- **Avoid:** Generic admin dashboard templates, excessive gradient cards, cyberpunk/neon themes, completely pitch-black non-3D layouts, and gratuitous micro-interactions.
