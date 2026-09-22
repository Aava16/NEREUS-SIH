# NEREUS Oceanographic Data Repository

## 1. Primary Demonstration Dataset

- **Product Name**: Multi Observation Global Ocean 3D Temperature Salinity Height Geostrophic Current and MLD
- **Product Identifier**: `MULTIOBS_GLO_PHY_TSUV_3D_MYNRT_015_012`
- **Source Authority**: Copernicus Marine Service (Mercator Ocean International / European Commission)
- **DOI**: [10.48670/moi-00052](https://doi.org/10.48670/moi-00052)
- **Official Portal**: [Copernicus Marine Data Store](https://data.marine.copernicus.eu/product/MULTIOBS_GLO_PHY_TSUV_3D_MYNRT_015_012)
- **Standard Convention**: Climate and Forecast (CF) Metadata Convention v1.8
- **Coordinate Reference System**: EPSG:4326 (WGS 84 Ellipsoid)

---

## 2. Selected Regional Demonstration Subset

To provide high-fidelity local exploration without requiring multi-terabyte global file transfers, a regional 4D subset has been selected:

- **Geographic Domain**: Arabian Sea & Northern Indian Ocean Hydrodynamic Corridor
- **Spatial Bounds**:
  - Latitude: $8.0^\circ\text{N}$ to $18.0^\circ\text{N}$ ($0.5^\circ$ resolution, 21 grid nodes)
  - Longitude: $65.0^\circ\text{E}$ to $77.0^\circ\text{E}$ ($0.5^\circ$ resolution, 25 grid nodes)
- **Vertical Extent**:
  - 10 Depth Levels: `[0.5, 10.0, 30.0, 50.0, 75.0, 100.0, 150.0, 200.0, 300.0, 500.0]` meters
- **Temporal Horizon**:
  - 5 Monthly Time Steps: `2024-01-15`, `2024-02-15`, `2024-03-15`, `2024-04-15`, `2024-05-15`

---

## 3. Scientific Variables Mapping

| Variable Name in Asset | Canonical Concept | Units | CF Standard Name | Physical Description |
| :--- | :--- | :--- | :--- | :--- |
| `thetao` | Sea Temperature | `°C` | `sea_water_potential_temperature` | Conservative sea water temperature profile across depth levels |
| `so` | Salinity | `PSU` | `sea_water_salinity` | Practical salinity units tracking Arabian Sea high-salinity water mass |
| `uo` | Eastward Velocity | `m/s` | `eastward_sea_water_velocity` | Zonal geostrophic current component derived from altimetry & in-situ |
| `vo` | Northward Velocity | `m/s` | `northward_sea_water_velocity` | Meridional geostrophic current component |
| `zos` | Sea Surface Height | `m` | `sea_surface_height_above_geoid` | Dynamic sea surface topography |
| `mlotst` | Mixed Layer Depth | `m` | `ocean_mixed_layer_thickness_defined_by_sigma_theta` | Depth of the upper ocean well-mixed surface layer |

---

## 4. Reproducibility & Ingestion Instructions

### A. Generate or Download the Subset Asset
```powershell
backend\.venv\Scripts\python.exe scripts/generate_copernicus_demo_asset.py
```
This generates `data/processed/copernicus_multiobs_arabian_sea_2024.nc` matching the CF-1.8 dataset specification.

### B. Ingest the Dataset into NEREUS Catalog
```powershell
backend\.venv\Scripts\python.exe scripts/ingest_demo_dataset.py
```
This registers the dataset, variables, spatial extent polygon in PostGIS, array asset URI, and complete provenance lineage.

---

## 5. License & Attribution Requirements

Data provided through the E.U. Copernicus Marine Service.
- **Attribution Statement**: *E.U. Copernicus Marine Service Information; https://doi.org/10.48670/moi-00052*
- **Terms of Use**: Open and free access for scientific research, operational monitoring, and educational purposes under the Copernicus Programme Data Policy.
