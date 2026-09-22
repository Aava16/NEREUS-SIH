# NEREUS-SIH — Live Demonstration & Evaluation Guide

**Audience**: Smart India Hackathon (SIH) Evaluators, Marine Scientists, GIS Engineers  
**Duration**: 5–7 Minutes  
**Core Thesis**: *NEREUS is an ocean data intelligence platform for exploring, analyzing, and delivering multidimensional oceanographic data from canonical metadata down to raw NetCDF-4 scientific arrays.*

---

## Pre-Demonstration Checklist

Before initiating the demonstration, ensure all services are active:

1. **PostgreSQL / PostGIS Database**: Running on port `5432` with `POSTGIS="3.6.2"` and Alembic at head revision `a63948da8605`.
2. **Backend API**: Running at `http://127.0.0.1:8000` (`python -m uvicorn app.main:app --reload`).
3. **Frontend Application**: Running at `http://localhost:5173` (`npm run dev`).
4. **Demonstration Dataset**: Copernicus Global 3D Ocean Physics Multiobs (`copernicus_multiobs_arabian_sea_2024.nc`) registered in catalog (`copernicus-multiobs-arabian-sea-2024`).

---

## 5–7 Minute SIH Demonstration Flow

### 1. [00:00–00:30] Landing & Architecture Vision
- **Screen**: Landing / Home Page (`/`)
- **Action**: Open the landing page. Point to the live system health indicator and real-time backend connection status.
- **Narrative**:
  > *"NEREUS is an ocean data intelligence platform built to bridge the gap between high-dimensional oceanographic observation models (NetCDF-4/Zarr) and real-time interactive scientific decision workflows. Rather than storing millions of numerical array points in a traditional relational database, NEREUS couples PostgreSQL/PostGIS for canonical cataloging, spatio-temporal indexing, and provenance tracking with high-performance out-of-core array services for slicing, depth profiling, and vector field computation."*

---

### 2. [00:30–01:15] Dataset Discovery & Metadata
- **Screen**: Dataset Catalog (`/datasets`)
- **Action**: Navigate to the Dataset Catalog. Filter/select `Copernicus Global 3D Ocean Physics Multiobs (Arabian Sea 2024)`.
- **Narrative**:
  > *"Here we discover our primary scientific asset: a real Copernicus Marine Service product (`MULTIOBS_GLO_PHY_TSUV_3D_MYNRT_015_012`) covering the Arabian Sea and Western Indian Ocean (8°N–18°N, 65°E–77°E) with 10 standard oceanographic depth levels from surface to 500 meters. Evaluators can inspect the exact bounding coordinates, temporal span, citation, and registered physical variables: Potential Temperature (`thetao`), Salinity (`so`), Zonal Velocity (`uo`), Meridional Velocity (`vo`), Sea Surface Height (`zos`), and Mixed Layer Thickness (`mlotst`)."*

---

### 3. [01:15–02:00] Spatial Exploration & Depth Slicing
- **Screen**: Scientific Workspace — Spatial Map Canvas (`/workspace` or `/datasets/{id}`)
- **Action**: 
  - Select `Potential Temperature (thetao)`.
  - Toggle through depth levels: `0.5m (Surface)` → `50m` → `150m` → `300m`.
  - Notice the thermocline temperature drop (28.5°C at surface down to ~12°C at 300m).
  - Hover over grid cells to show coordinate tooltips and continuous colorbar scalar mapping.
- **Narrative**:
  > *"When we inspect the temperature field horizontally across the Arabian Sea, our backend computes on-the-fly 2D scalar grids directly from the NetCDF asset with bounding validation. Stepping down through depth levels immediately reveals the vertical thermal stratification and mixed layer physics."*

---

### 4. [02:00–02:45] Vertical Structure & Depth Profile
- **Screen**: Vertical Depth Profile View / Probe Mode
- **Action**: Click on an offshore coordinate in the Arabian Sea (e.g., Lat: 14.5°N, Lon: 70.0°E).
- **Narrative**:
  > *"Selecting any point on the map triggers an instant vertical extraction (`/api/v1/datasets/{id}/variables/thetao/profile`). The chart visualizes the full vertical water column profile down to 500m depth, clearly demarcating the mixed layer, the rapid thermocline gradient between 50m and 150m, and the deep ocean isothermal layer."*

---

### 5. [02:45–03:30] Ocean Current Vectors & Dynamics
- **Screen**: Currents Vector Map
- **Action**:
  - Switch variable overlay to `uo` (Zonal) + `vo` (Meridional) Vector Currents.
  - Show magnitude color gradient and directional arrows indicating circulation in the Arabian Sea.
- **Narrative**:
  > *"NEREUS computes ocean current magnitude $\sqrt{U^2 + V^2}$ and directional flow using backend-authoritative hydrodynamic conventions. Here we observe the energetic coastal currents and cyclonic mesoscale eddy circulation patterns across the central Arabian Sea basin."*

---

### 6. [03:30–04:30] Scientific Analysis & Transect Cross-Sections
- **Screen**: Analytics Suite & Transect Tool
- **Action**:
  - Run **Summary Statistics** (Min, Max, Mean, Standard Deviation, Quantiles, NaN counts).
  - Open the **Transect Cross-Section** tool: Draw or set a transect line from coastal Goa (15°N, 73.5°E) to the central basin (12°N, 66°E).
  - View the 2D vertical slice rendering temperature or salinity across distance vs. depth.
- **Narrative**:
  > *"Researchers can execute real-time cross-sectional ocean transects. Our delivery service interpolates across the 3D grid along arbitrary geographic paths, producing high-resolution vertical cross-sections essential for studying coastal upwelling, frontal zones, and water mass boundaries."*

---

### 7. [04:30–05:15] End-to-End Provenance & Traceability
- **Screen**: Provenance Graph / Lineage Tab
- **Action**: Open the Dataset Provenance tab.
- **Narrative**:
  > *"Every scientific observation and analysis in NEREUS is 100% reproducible and traced through our W3C PROV-compliant provenance graph:  
  **Data Source (Copernicus Marine)** → **Registered Dataset** → **Physical Variable** → **Processing/Analysis Job** → **Output Artifact**.  
  Evaluators can verify the exact algorithms, code version, bounding filters, and timestamps applied to any delivered product."*

---

### 8. [05:15–06:00] Research Workspace Export
- **Screen**: Export Modal / Data Export
- **Action**:
  - Click **Export Data**.
  - Select format: GeoJSON (spatial), CSV (time series/profile), or NetCDF-4 metadata summary.
  - Download the resulting artifact.
- **Narrative**:
  > *"Exporting produces clean, standard-compliant scientific data packages with embedded provenance metadata, ready for integration into Python Jupyter notebooks, GIS workstations (QGIS/ArcGIS), or scientific publication pipelines."*

---

### 9. [06:00–07:00] Closing & Value Proposition
- **Screen**: Workspace Overview
- **Narrative**:
  > *"In summary, NEREUS provides a complete, hardened, and reproducible scientific data pipeline:  
  **DISCOVER → INSPECT → EXPLORE → ANALYZE → TRACE → EXPORT**.  
  Thank you, and we welcome any technical or scientific questions from the evaluation panel."*

---

## Demonstration FAQs & Evaluator Questions

| Question | Technical Answer |
| :--- | :--- |
| **How does NEREUS handle very large arrays?** | NEREUS uses out-of-core NetCDF-4/Zarr slicing via `xarray` and `numpy`. PostgreSQL/PostGIS only stores metadata, geometry envelopes, and provenance; high-dimensional chunks are streamed and bounded to prevent out-of-memory errors. |
| **Is this synthetic data?** | No. The demonstration dataset is an ingested subset from the **Copernicus Marine Service Global Ocean 3D Physics Analysis and Forecast (`MULTIOBS_GLO_PHY_TSUV_3D_MYNRT_015_012`)**, provided by the European Union Copernicus Programme. |
| **What coordinate reference system is used?** | EPSG:4326 (WGS 84 2D spatial coordinate system) for all PostGIS spatial boundaries, API payloads, and map projections. |
| **How are current directions defined?** | Oceanographic convention: direction towards which the water is moving, measured in degrees clockwise from True North ($0^\circ = \text{North}, 90^\circ = \text{East}$). |
