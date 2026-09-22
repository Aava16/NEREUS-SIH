# NEREUS-SIH — Production Deployment & Cloud Hosting Guide

This document specifies the exact configuration, environment variables, startup commands, and SPA routing setup required to host NEREUS-SIH publicly for the Smart India Hackathon (SIH) demonstration.

---

## 1. Environment Variables Specification

### A. Frontend Environment Variables (Vercel / Netlify / Static Host)

| Variable | Required | Production Example | Local Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | **YES** | `https://nereus-api.onrender.com` | `http://localhost:8000` | Target URL of the deployed FastAPI backend. Injected at Vite build time. |

### B. Backend Environment Variables (Render / Railway / Cloud Host)

| Variable | Required | Production Example | Local Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **YES** | `postgresql://postgres:secret@db.supabase.co:5432/postgres` | `postgresql://postgres:postgres@localhost:5432/nereus_db` | PostgreSQL connection string with PostGIS enabled. |
| `CORS_ORIGINS` | **YES** | `["https://nereus-sih.vercel.app", "http://localhost:5173"]` | `["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]` | Allowed origins for cross-origin requests. Accepts JSON arrays or comma-separated URLs. |
| `DEBUG` | NO | `false` | `false` | Disable debug-level verbose logging in production. |
| `APP_NAME` | NO | `NEREUS API` | `NEREUS API` | Service title in OpenAPI/Swagger documentation. |
| `API_V1_PREFIX` | NO | `/api/v1` | `/api/v1` | Prefix for version 1 API endpoints. |
| `DATA_ROOT` | NO | `data` | `data` | Base directory for scientific NetCDF-4/Zarr storage. |

---

## 2. Frontend Deployment (Vercel)

### Configuration Settings in Vercel Dashboard
- **Framework Preset**: `Vite`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (or `tsc -b && vite build`)
- **Output Directory**: `dist`
- **Install Command**: `npm install`
- **Environment Variables**:
  - `VITE_API_BASE_URL`: `https://<your-deployed-backend-url>`

### SPA Routing Fallback
NEREUS-SIH includes [frontend/vercel.json](../frontend/vercel.json) with client-side rewrite rules:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```
*And [frontend/public/_redirects](../frontend/public/_redirects) for Netlify / Render Static compatibility.*

---

## 3. Backend Deployment (Render / Railway / AWS / Docker)

### Startup Commands

#### Option A: Running from Repository Root
```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT --workers 2
```

#### Option B: Running from `backend/` Directory
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

### Pre-Deploy / Release Command
Run this single command before server start to apply database migrations and register the Copernicus scientific dataset:
```bash
alembic upgrade head && python scripts/generate_copernicus_demo_asset.py && python scripts/ingest_demo_dataset.py
```

---

## 4. Database Requirements (PostgreSQL + PostGIS)

1. Provision a PostgreSQL 14+ instance on Supabase, Neon, Render, Railway, or AWS RDS.
2. Enable PostGIS extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
   *(Note: Alembic migration `87eb89dfbcdd` runs this statement automatically during `alembic upgrade head`).*
3. Set `DATABASE_URL` in backend environment variables.

---

## 5. Local Development Behavior

Local development remains 100% untouched and zero-config:
- **Backend**: `python -m uvicorn app.main:app --reload` (connects to local PostgreSQL and allows localhost:5173 / localhost:3000).
- **Frontend**: `npm run dev` (defaults to `http://localhost:8000` when `VITE_API_BASE_URL` is omitted).
- **Data assets**: Automatically resolves local arrays from `data/processed/copernicus_multiobs_arabian_sea_2024.nc`.
