from pathlib import Path
import uuid
from fastapi.testclient import TestClient
import numpy as np
import pytest
import xarray as xr

from app.main import app

client = TestClient(app)


@pytest.fixture
def synthetic_netcdf_asset(tmp_path: Path):
    """Fixture creating a temporary synthetic NetCDF4 file and registering it as a Dataset and ArrayAsset."""
    nc_path = tmp_path / "synthetic_ocean_grid.nc"

    lons = np.linspace(60.0, 80.0, 21)
    lats = np.linspace(0.0, 20.0, 21)
    depths = np.array([0.0, 10.0, 50.0, 100.0, 500.0])
    times = np.array(["2026-06-01T00:00:00", "2026-06-02T00:00:00"], dtype="datetime64[ns]")

    temp_data = 28.0 - 0.04 * depths[None, :, None, None] + np.zeros((2, 5, 21, 21))
    u_data = np.ones((2, 5, 21, 21), dtype=np.float32) * 0.5
    v_data = np.ones((2, 5, 21, 21), dtype=np.float32) * 0.8

    ds = xr.Dataset(
        data_vars={
            "temperature": (
                ("time", "depth", "lat", "lon"),
                temp_data.astype(np.float32),
                {"units": "degC", "standard_name": "sea_water_potential_temperature", "valid_min": -2.0, "valid_max": 40.0},
            ),
            "u_current": (("time", "depth", "lat", "lon"), u_data, {"units": "m/s"}),
            "v_current": (("time", "depth", "lat", "lon"), v_data, {"units": "m/s"}),
        },
        coords={"time": times, "depth": depths, "lat": lats, "lon": lons},
        attrs={"title": "NEREUS Synthetic Test Ocean Grid", "institution": "NEREUS Development"},
    )
    ds.to_netcdf(nc_path)

    # Register Dataset in DB
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"synth_ds_{uuid.uuid4().hex[:8]}",
            "title": "Synthetic Ocean Test Dataset",
            "dataset_type": "MODEL_FORECAST",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # Register Array Asset pointing to local file
    asset_res = client.post(
        "/api/v1/array-assets",
        json={
            "dataset_id": dataset_id,
            "storage_format": "NETCDF4",
            "uri": str(nc_path.resolve()),
            "variable_info": {"temperature": "temperature", "u_current": "u_current", "v_current": "v_current"},
            "dimensions": {"time": 2, "depth": 5, "lat": 21, "lon": 21},
        },
    )
    assert asset_res.status_code == 201
    asset_id = asset_res.json()["id"]

    yield {"dataset_id": dataset_id, "asset_id": asset_id, "filepath": str(nc_path)}

    # Cleanup dataset & assets
    client.delete(f"/api/v1/datasets/{dataset_id}")


def test_scientific_asset_inspection(synthetic_netcdf_asset: dict) -> None:
    """Test opening and inspecting multidimensional NetCDF4 asset metadata with xarray."""
    asset_id = synthetic_netcdf_asset["asset_id"]

    res = client.get(f"/api/v1/processing/assets/{asset_id}/inspect")
    assert res.status_code == 200
    data = res.json()

    # 1. Dimensions
    assert "time" in data["dimensions"]
    assert "depth" in data["dimensions"]
    assert "lat" in data["dimensions"]
    assert "lon" in data["dimensions"]
    assert data["dimensions"]["lon"]["min_value"] == 60.0
    assert data["dimensions"]["lon"]["max_value"] == 80.0

    # 2. Variables
    assert "temperature" in data["variables"]
    assert data["variables"]["temperature"]["units"] == "degC"
    assert data["variables"]["temperature"]["shape"] == [2, 5, 21, 21]

    # 3. Spatial & Temporal Extents
    assert data["spatial_extent"]["min_lon"] == 60.0
    assert data["spatial_extent"]["max_lat"] == 20.0
    assert data["depth_coverage"]["min_m"] == 0.0
    assert data["depth_coverage"]["max_m"] == 500.0
    assert data["is_valid_ocean_grid"] is True


def test_bounded_grid_slicing_and_provenance(synthetic_netcdf_asset: dict) -> None:
    """Test bounded 2D array grid extraction with spatial bbox, decimation, and provenance."""
    asset_id = synthetic_netcdf_asset["asset_id"]
    dataset_id = synthetic_netcdf_asset["dataset_id"]

    slice_payload = {
        "variable_name": "temperature",
        "time_index": 0,
        "depth_index": 1,  # depth = 10m, temp = 28.0 - 0.04*10 = 27.6
        "bbox_min_lon": 65.0,
        "bbox_min_lat": 5.0,
        "bbox_max_lon": 75.0,
        "bbox_max_lat": 15.0,
        "decimation_step": 2,
    }

    res = client.post(f"/api/v1/processing/assets/{asset_id}/slice", json=slice_payload)
    assert res.status_code == 200
    slice_data = res.json()

    assert slice_data["variable_name"] == "temperature"
    assert slice_data["units"] == "degC"
    assert slice_data["depth_m"] == 10.0
    assert len(slice_data["data_grid"]) > 0
    assert slice_data["statistics"]["sample_count"] > 0
    assert round(slice_data["statistics"]["mean_value"], 1) == 27.6
    assert "provenance_id" in slice_data

    # Verify Provenance Record
    prov_res = client.get(
        "/api/v1/provenance",
        params={"dataset_id": dataset_id, "action": "SCIENTIFIC_SLICING"},
    )
    assert prov_res.status_code == 200
    prov_records = prov_res.json()
    assert len(prov_records) == 1
    assert prov_records[0]["details"]["variable_name"] == "temperature"


def test_derived_field_current_speed_magnitude(synthetic_netcdf_asset: dict) -> None:
    """Test on-the-fly calculation of current velocity magnitude sqrt(u^2 + v^2)."""
    asset_id = synthetic_netcdf_asset["asset_id"]
    dataset_id = synthetic_netcdf_asset["dataset_id"]

    # u = 0.5, v = 0.8 -> speed = sqrt(0.5^2 + 0.8^2) = sqrt(0.25 + 0.64) = sqrt(0.89) ≈ 0.9434
    derive_payload = {
        "derived_type": "CURRENT_SPEED_MAGNITUDE",
        "variable_u": "u_current",
        "variable_v": "v_current",
        "time_index": 0,
        "depth_index": 0,
        "decimation_step": 1,
    }

    res = client.post(f"/api/v1/processing/assets/{asset_id}/derive", json=derive_payload)
    assert res.status_code == 200
    derived_data = res.json()

    assert derived_data["derived_type"] == "CURRENT_SPEED_MAGNITUDE"
    assert derived_data["units"] == "m/s"
    assert round(derived_data["statistics"]["mean_value"], 3) == 0.943

    # Verify Provenance Record
    prov_res = client.get(
        "/api/v1/provenance",
        params={"dataset_id": dataset_id, "action": "SCIENTIFIC_DERIVATION"},
    )
    assert prov_res.status_code == 200
    assert len(prov_res.json()) == 1


def test_missing_asset_and_missing_variable_error_handling() -> None:
    """Test error handling when asset or variable is missing."""
    non_existent_id = uuid.uuid4()

    # 1. Non-existent asset ID in DB
    inspect_res = client.get(f"/api/v1/processing/assets/{non_existent_id}/inspect")
    assert inspect_res.status_code == 404

    # 2. Asset registered with non-existent file on disk
    ds_res = client.post(
        "/api/v1/datasets",
        json={"name": f"bad_uri_ds_{uuid.uuid4().hex[:6]}", "title": "Missing File DS", "dataset_type": "MODEL_FORECAST"},
    )
    dataset_id = ds_res.json()["id"]

    bad_asset_res = client.post(
        "/api/v1/array-assets",
        json={
            "dataset_id": dataset_id,
            "storage_format": "NETCDF4",
            "uri": "/tmp/non_existent_file_nereus_12345.nc",
        },
    )
    bad_asset_id = bad_asset_res.json()["id"]

    missing_file_res = client.get(f"/api/v1/processing/assets/{bad_asset_id}/inspect")
    assert missing_file_res.status_code == 404

    # Cleanup
    client.delete(f"/api/v1/datasets/{dataset_id}")
