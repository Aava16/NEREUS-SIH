# NEREUS — Ocean Data Intelligence & Scientific Analytics Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![PostgreSQL 15+](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![PostGIS 3.6+](https://img.shields.io/badge/PostGIS-3.6+-orange.svg)](https://postgis.net/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.3+-646CFF.svg)](https://vitejs.dev/)

**NEREUS** is an ocean data intelligence platform built for exploring, analyzing, and delivering multidimensional oceanographic data (NetCDF-4 / Zarr / PostGIS) through canonical catalogs, high-performance out-of-core array services, and an interactive scientific research workspace.

---

## 🏛️ System Architecture

NEREUS adopts a layered, separation-of-concerns architecture designed specifically for high-volume scientific datasets:

```
PostgreSQL / PostGIS (EPSG:4326)
  ├─ Canonical Dataset & Platform Metadata
  ├─ Variable Registry & Physical Dimensions
  ├─ Observation Records & Spatial Indices
  └─ W3C PROV-Compliant Provenance Graph
             │
             ▼
Scientific Array Layer (NetCDF-4 / Zarr via xarray & netCDF4)
  ├─ Multi-dimensional Coordinate Alignment
  ├─ Chunked Slicing & Memory-Safe Bounded Extracts
  └─ Hydrodynamic Vector & Derived Field Calculations
             │
             ▼
Analysis & Data Delivery Layer (FastAPI REST Services)
  ├─ 2D Horizontal Scalar Grids (`/grid`)
  ├─ Vertical Depth Profiles (`/profile`)
  ├─ Spatio-Temporal Point Extraction (`/timeseries`)
  ├─ Ocean Current Vector Fields (`/currents/vectors`)
  ├─ Arbitrary Cross-Section Transects (`/transect`)
  └─ Comprehensive Summary Statistics (`/statistics`)
             │
             ▼
Scientific Visualization Workspace (React 19 + TypeScript + Vite)
  ├─ High-Precision Canvas Renderer & Colormaps (Viridis, Thermal, Haline, Salinity)
  ├─ Interactive Coordinate Probe & Time/Depth Scrubbers
  ├─ Multi-Variable Comparison & Vector Field Overlays
  └─ Provenance Inspector & Scientific Artifact Exporter
```

---

## 📦 System Requirements

- **Python**: `3.11` or higher
- **Node.js**: `18.0.0` or higher (with `npm 9+`)
- **PostgreSQL**: `15` or higher with **PostGIS `3.3+`** extension enabled
- **GDAL / PROJ**: Standard geospatial libraries (included with PostGIS)

---

## 🚀 Quick Start Guide

### 1. Environment Configuration

Clone the repository and copy the environment template:

```bash
# In repository root
cp .env.example .env
cp .env.example backend/.env
```

Ensure your PostgreSQL connection string in `backend/.env` points to an active database with PostGIS:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nereus_db
```

---

### 2. Backend Setup & Database Migrations

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations to current HEAD
python -m alembic upgrade head
```

---

### 3. Ingest Scientific Demonstration Dataset

Generate the NetCDF-4 binary asset and register it in the PostGIS catalog with full provenance:

```bash
# From repository root (with backend .venv activated):
python scripts/generate_copernicus_demo_asset.py
python scripts/ingest_demo_dataset.py
```

This ingests the **Copernicus Global Ocean 3D Physics Multiobs (Arabian Sea 2024)** dataset with 6 registered variables (`thetao`, `so`, `uo`, `vo`, `zos`, `mlotst`) and 10 vertical depth levels (0.5m to 500m).

---

### 4. Run Backend API Server

```bash
# In backend directory (with .venv active)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Base: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Checks: `http://127.0.0.1:8000/health` & `http://127.0.0.1:8000/health/db`

---

### 5. Frontend Setup & Launch

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Open your browser at: **`http://localhost:5173`**

---

## 🧪 Testing & Validation Suite

### Backend Test Suite (43 Tests)
```bash
cd backend
.venv\Scripts\python.exe -m pytest tests -v
```

### Frontend Lint & Production Build
```bash
cd frontend
npm run lint
npm run build
```

---

## 🧭 SIH Demonstration Walkthrough

For a step-by-step 5–7 minute presentation guide for evaluators, refer to [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md).

1. **[00:00] Landing**: Real-time health status, telemetry, system capability overview.
2. **[00:30] Catalog**: Filter Copernicus Marine 3D physics dataset with registered dimensions.
3. **[01:15] Spatial Exploration**: Dynamic depth slicing of potential temperature (`thetao`) from 0.5m to 500m.
4. **[02:00] Depth Profile**: Interactive vertical water-column extraction and thermocline analysis.
5. **[02:45] Ocean Currents**: Vector field rendering ($U, V$) showing speed and direction.
6. **[03:30] Transect Cross-Section**: Arbitrary 2D vertical slicing across coastal-to-offshore transects.
7. **[04:30] Provenance**: Full lineage graph from Copernicus source product to analysis artifacts.
8. **[05:15] Export**: Multi-format scientific data delivery (GeoJSON / CSV / JSON).

---

## 📄 Scientific Attribution & Data Source

The primary demonstration dataset is derived from:
- **Provider**: European Union Copernicus Marine Service (CMEMS)
- **Product**: `MULTIOBS_GLO_PHY_TSUV_3D_MYNRT_015_012`
- **Geographic Domain**: Arabian Sea / Western Indian Ocean ($8^\circ\text{N}-18^\circ\text{N}, 65^\circ\text{E}-77^\circ\text{E}$)
- **Depth Range**: 0.5 m to 500.0 m (10 oceanographic standard levels)
- **Licence**: Creative Commons Attribution 4.0 International (CC BY 4.0)

---

## 🔒 Security & Privacy

- All secrets and credentials are fully externalized via `.env`.
- Database credentials and internal filepaths are never exposed in client API responses.
- Memory safety bounds enforce maximum grid resolution limits ($2048 \times 2048$) to prevent denial-of-service or out-of-memory crashes during array slicing.
