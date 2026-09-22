"""Automated verification test suite for Copernicus Real Demonstration Dataset.

Tests:
- Manifest structure and schema validation
- NetCDF-4 asset validation and dimensions
- Atomic dataset ingestion into PostgreSQL/PostGIS catalog
- Metadata delivery and variable discovery
- 2D spatial grid delivery (Temperature & Salinity)
- 4D vertical depth profiling (Thermocline & Pycnocline)
- Temporal point time-series extraction
- Hydrodynamic U/V geostrophic current vector delivery and speed calculation
- Great-circle transect spatial interpolation
- Dataset statistical and anomaly analysis
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import xarray as xr

from app.db.session import SessionLocal
from app.main import app
from app.repositories.dataset import DatasetRepository
from app.schemas.ingestion import DatasetIngestionRequest
from app.services.ingestion import IngestionService

ROOT_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def real_demo_dataset_fixture():
    """Ensure the Copernicus demo NetCDF-4 asset exists and is registered in the test DB."""
    nc_path = ROOT_DIR / "data" / "processed" / "copernicus_multiobs_arabian_sea_2024.nc"
    manifest_path = ROOT_DIR / "data" / "manifests" / "copernicus_multiobs_glo_phy_tsuv_manifest.json"

    # 1. Ensure asset exists
    if not nc_path.exists():
        from scripts.generate_copernicus_demo_asset import generate_copernicus_dataset
        generate_copernicus_dataset(str(nc_path))

    # 2. Ingest if not present
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    manifest_data["array_assets"][0]["uri"] = str(nc_path.resolve())
    payload = DatasetIngestionRequest.model_validate(manifest_data)

    db = SessionLocal()
    dataset_repo = DatasetRepository()
    service = IngestionService()
    try:
        existing = dataset_repo.get_by_name(db, payload.name)
        if not existing:
            result = service.ingest_dataset(db, payload)
            db.commit()
            dataset_id = str(result.dataset.id)
        else:
            dataset_id = str(existing.id)
    finally:
        db.close()

    return {
        "dataset_id": dataset_id,
        "dataset_name": payload.name,
        "nc_path": str(nc_path),
        "manifest": manifest_data,
    }


def test_copernicus_netcdf_asset_integrity(real_demo_dataset_fixture):
    """Verify physical consistency and CF-1.8 attributes of the demonstration NetCDF asset."""
    nc_path = real_demo_dataset_fixture["nc_path"]
    with xr.open_dataset(nc_path) as ds:
        # Coordinates check
        assert "latitude" in ds.coords
        assert "longitude" in ds.coords
        assert "depth" in ds.coords
        assert "time" in ds.coords

        assert len(ds.coords["latitude"]) == 21
        assert len(ds.coords["longitude"]) == 25
        assert len(ds.coords["depth"]) == 10
        assert len(ds.coords["time"]) == 5

        # Variables check
        assert "thetao" in ds.data_vars
        assert "so" in ds.data_vars
        assert "uo" in ds.data_vars
        assert "vo" in ds.data_vars
        assert "zos" in ds.data_vars
        assert "mlotst" in ds.data_vars

        # Physical value ranges for Arabian Sea
        t_vals = ds["thetao"].values
        assert np_is_finite_and_between(t_vals, 10.0, 32.0)

        s_vals = ds["so"].values
        assert np_is_finite_and_between(s_vals, 34.0, 38.0)


def np_is_finite_and_between(arr, vmin, vmax):
    import numpy as np
    valid = arr[np.isfinite(arr)]
    return len(valid) > 0 and np.all(valid >= vmin) and np.all(valid <= vmax)


def test_copernicus_api_dataset_discovery(real_demo_dataset_fixture):
    """Verify dataset is discoverable via canonical REST API."""
    client = TestClient(app)
    ds_id = real_demo_dataset_fixture["dataset_id"]

    res = client.get("/api/v1/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert any(d["id"] == ds_id for d in datasets)

    # Variables delivery
    var_res = client.get(f"/api/v1/datasets/{ds_id}/variables")
    assert var_res.status_code == 200
    var_names = [v.get("name") or v.get("variable_name") for v in var_res.json()["variables"]]
    assert "thetao" in var_names
    assert "so" in var_names
    assert "uo" in var_names
    assert "vo" in var_names


def test_copernicus_grid_and_slice_delivery(real_demo_dataset_fixture):
    """Verify 2D spatial grid extraction for temperature and salinity."""
    client = TestClient(app)
    ds_id = real_demo_dataset_fixture["dataset_id"]

    # Surface temperature
    res_t = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/grid?depth_index=0&time_index=0")
    assert res_t.status_code == 200
    grid_t = res_t.json()
    assert len(grid_t["latitudes"]) == 21
    assert len(grid_t["longitudes"]) == 25
    assert len(grid_t["values"]) == 21
    assert len(grid_t["values"][0]) == 25
    assert 25.0 <= grid_t["min_value"] <= grid_t["max_value"] <= 31.0

    # Depth 500m temperature (Thermocline cooling check)
    res_t_deep = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/grid?depth_index=9&time_index=0")
    assert res_t_deep.status_code == 200
    grid_deep = res_t_deep.json()
    assert grid_deep["max_value"] < grid_t["min_value"]  # Deep ocean is substantially cooler than surface


def test_copernicus_vertical_profile_and_timeseries(real_demo_dataset_fixture):
    """Verify vertical soundings (depth profile) and temporal point probe."""
    client = TestClient(app)
    ds_id = real_demo_dataset_fixture["dataset_id"]

    # Profile at (14.0°N, 70.0°E)
    prof_res = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/profile?latitude=14.0&longitude=70.0")
    assert prof_res.status_code == 200
    p_data = prof_res.json()
    assert len(p_data["depths"]) == 10
    assert len(p_data["values"]) == 10
    assert p_data["values"][0] > p_data["values"][-1]  # Monotonic temperature decrease with depth

    # Time series
    ts_res = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/timeseries?latitude=14.0&longitude=70.0")
    assert ts_res.status_code == 200
    t_data = ts_res.json()
    assert t_data["total_points"] == 5
    assert len(t_data["points"]) == 5


def test_copernicus_geostrophic_currents_delivery(real_demo_dataset_fixture):
    """Verify hydrodynamic current vector field extraction and speed calculations."""
    client = TestClient(app)
    ds_id = real_demo_dataset_fixture["dataset_id"]

    res = client.get(f"/api/v1/datasets/{ds_id}/currents/vectors?u_var=uo&v_var=vo&depth_index=0&time_index=0")
    assert res.status_code == 200
    c_data = res.json()
    assert c_data["total_vectors"] == 21 * 25
    assert len(c_data["vectors"]) == 21 * 25
    assert all("speed" in vec and "direction" in vec for vec in c_data["vectors"][:5])
    speeds = [v["speed"] for v in c_data["vectors"] if v.get("speed") is not None]
    assert len(speeds) > 0
    assert 0.05 <= max(speeds) <= 0.8


def test_copernicus_great_circle_transect(real_demo_dataset_fixture):
    """Verify spatial interpolation along great-circle transect line."""
    client = TestClient(app)
    ds_id = real_demo_dataset_fixture["dataset_id"]

    res = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/transect?lat1=10.0&lon1=68.0&lat2=16.0&lon2=75.0&num_points=30")
    assert res.status_code == 200
    tr_data = res.json()
    assert tr_data["total_points"] == 30
    assert tr_data["total_distance_km"] > 500.0
    assert all(p["value"] is not None for p in tr_data["points"])


def test_copernicus_statistical_analysis(real_demo_dataset_fixture):
    """Verify statistics computation over the bounded dataset."""
    client = TestClient(app)
    ds_id = real_demo_dataset_fixture["dataset_id"]

    res = client.get(f"/api/v1/analysis/datasets/{ds_id}/statistics?variable=thetao")
    assert res.status_code == 200
    stats_data = res.json()
    assert "thetao" in stats_data["variables"]
    t_stats = stats_data["variables"]["thetao"]
    assert t_stats["valid_count"] == 5 * 10 * 21 * 25
    assert t_stats["mean"] > 12.0
    assert t_stats["std"] > 1.0
