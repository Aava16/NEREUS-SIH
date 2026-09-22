"""Tests for Phase 8: Scientific Data Delivery & Visualization Foundation.

Validates frontend dataset metadata descriptions, variable discovery,
2D spatial grid map delivery, vertical depth profiles, point time-series,
ocean current vectors, and safe array slicing with synthetic fixtures.
"""

from datetime import datetime, timezone
import os
import tempfile
import uuid
import numpy as np
import pytest
from fastapi.testclient import TestClient
import netCDF4 as nc

from app.main import app
from app.models.dataset import Dataset
from app.models.array_asset import ArrayAsset
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture
def synthetic_delivery_netcdf():
    """Create a temporary synthetic NetCDF4 file with temperature, currents, and salinity."""
    fd, path = tempfile.mkstemp(suffix=".nc")
    os.close(fd)

    ds = nc.Dataset(path, "w", format="NETCDF4")

    # Dimensions
    ds.createDimension("time", 5)
    ds.createDimension("depth", 4)
    ds.createDimension("lat", 10)
    ds.createDimension("lon", 12)

    # Coordinate variables
    time_var = ds.createVariable("time", "f8", ("time",))
    time_var.units = "hours since 2026-02-01 00:00:00"
    time_var.standard_name = "time"
    time_var[:] = [0.0, 6.0, 12.0, 18.0, 24.0]

    depth_var = ds.createVariable("depth", "f4", ("depth",))
    depth_var.units = "m"
    depth_var.standard_name = "depth"
    depth_var[:] = [0.0, 10.0, 50.0, 100.0]

    lat_var = ds.createVariable("lat", "f4", ("lat",))
    lat_var.units = "degrees_north"
    lat_var.standard_name = "latitude"
    lat_var[:] = np.linspace(10.0, 19.0, 10)

    lon_var = ds.createVariable("lon", "f4", ("lon",))
    lon_var.units = "degrees_east"
    lon_var.standard_name = "longitude"
    lon_var[:] = np.linspace(70.0, 81.0, 12)

    # Sea Surface Temperature
    sst_var = ds.createVariable("sst", "f4", ("time", "depth", "lat", "lon"), fill_value=-999.0)
    sst_var.units = "degC"
    sst_var.standard_name = "sea_surface_temperature"
    sst_var.long_name = "Sea Surface Temperature"
    sst_data = 26.0 + np.random.uniform(-1.5, 1.5, size=(5, 4, 10, 12)).astype(np.float32)
    sst_data[0, 0, 0, 0] = np.nan
    sst_var[:] = sst_data

    # Ocean current velocity fields
    u_var = ds.createVariable("u", "f4", ("time", "depth", "lat", "lon"))
    u_var.units = "m/s"
    u_var.standard_name = "eastward_sea_water_velocity"
    u_var[:] = np.full((5, 4, 10, 12), 0.3, dtype=np.float32)

    v_var = ds.createVariable("v", "f4", ("time", "depth", "lat", "lon"))
    v_var.units = "m/s"
    v_var.standard_name = "northward_sea_water_velocity"
    v_var[:] = np.full((5, 4, 10, 12), 0.4, dtype=np.float32)

    w_var = ds.createVariable("w", "f4", ("time", "depth", "lat", "lon"))
    w_var.units = "m/s"
    w_var.standard_name = "upward_sea_water_velocity"
    w_var[:] = np.full((5, 4, 10, 12), 0.05, dtype=np.float32)

    # Salinity
    sal_var = ds.createVariable("salinity", "f4", ("time", "depth", "lat", "lon"))
    sal_var.units = "PSU"
    sal_var.standard_name = "sea_water_salinity"
    sal_var[:] = np.full((5, 4, 10, 12), 35.0, dtype=np.float32)

    ds.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def registered_delivery_dataset(synthetic_delivery_netcdf):
    """Register a canonical dataset and array asset pointing to the synthetic file."""
    db = next(get_db())

    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        name=f"delivery-test-ds-{dataset_id.hex[:6]}",
        title="Delivery Test Dataset",
        description="Dataset for scientific data delivery and visualization verification",
        source="INCOIS_SIMULATION",
        source_uri=synthetic_delivery_netcdf,
        dataset_type="GRIDDED_MODEL",
        temporal_start=datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        temporal_end=datetime(2026, 2, 2, 0, 0, 0, tzinfo=timezone.utc),
        metadata_json={"institution": "INCOIS", "project": "NEREUS"},
    )
    db.add(dataset)
    db.flush()

    asset_id = uuid.uuid4()
    asset = ArrayAsset(
        id=asset_id,
        dataset_id=dataset_id,
        storage_format="NETCDF4",
        uri=synthetic_delivery_netcdf,
        dimensions={"time": 5, "depth": 4, "lat": 10, "lon": 12},
        variable_info={"sst": "degC", "u": "m/s", "v": "m/s", "w": "m/s", "salinity": "PSU"},
    )
    db.add(asset)
    db.commit()

    yield dataset_id, asset_id

    # Teardown
    db.delete(asset)
    db.delete(dataset)
    db.commit()


def test_get_dataset_metadata_delivery(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/metadata returns complete frontend description."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(f"/api/v1/datasets/{dataset_id}/metadata")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["title"] == "Delivery Test Dataset"
    assert data["dataset_type"] == "GRIDDED_MODEL"
    assert "sst" in data["variables"]
    assert "u" in data["variables"]
    assert data["dimensions"]["time"] == 5
    assert data["dimensions"]["depth"] == 4
    assert data["spatial_extent"]["latitude_min"] == 10.0
    assert data["spatial_extent"]["latitude_max"] == 19.0
    assert data["depth_extent"]["depth_levels_count"] == 4
    assert data["depth_extent"]["levels"] == [0.0, 10.0, 50.0, 100.0]
    assert data["temporal_extent"]["total_timesteps"] == 5


def test_discover_variables(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/variables discovers all variables with metadata."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(f"/api/v1/datasets/{dataset_id}/variables")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["total_variables"] >= 4
    var_names = [v["variable_name"] for v in data["variables"]]
    assert "sst" in var_names
    assert "u" in var_names
    assert "v" in var_names
    assert "salinity" in var_names

    sst_item = next(v for v in data["variables"] if v["variable_name"] == "sst")
    assert sst_item["units"] == "degC"
    assert sst_item["standard_name"] == "sea_surface_temperature"
    assert sst_item["shape"] == [5, 4, 10, 12]
    assert sst_item["dimensions"] == ["time", "depth", "lat", "lon"]


def test_get_variable_grid_map_delivery(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/variables/{variable}/grid returns 2D matrix for map visualization."""
    dataset_id, asset_id = registered_delivery_dataset

    # 1. Standard grid slice
    resp = client.get(f"/api/v1/datasets/{dataset_id}/variables/sst/grid?time_index=0&depth_index=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["variable_name"] == "sst"
    assert data["units"] == "degC"
    assert len(data["latitudes"]) == 10
    assert len(data["longitudes"]) == 12
    assert len(data["values"]) == 10
    assert len(data["values"][0]) == 12
    assert data["values"][0][0] is None  # NaN cell converted to None

    # 2. Bounded grid slice with spatial decimation
    sub_resp = client.get(
        f"/api/v1/datasets/{dataset_id}/variables/sst/grid?min_lat=12.0&max_lat=18.0&min_lon=72.0&max_lon=80.0&decimation=2"
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["downsample"]["downsampled"] is True
    assert sub_data["downsample"]["decimation_factor"] == 2
    assert len(sub_data["latitudes"]) <= 5


def test_get_variable_profile(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/variables/{variable}/profile returns vertical water column."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(
        f"/api/v1/datasets/{dataset_id}/variables/sst/profile?latitude=14.5&longitude=75.5&time_index=0"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["variable_name"] == "sst"
    assert data["requested_latitude"] == 14.5
    assert data["requested_longitude"] == 75.5
    assert 10.0 <= data["actual_latitude"] <= 19.0
    assert 70.0 <= data["actual_longitude"] <= 81.0
    assert len(data["depths"]) == 4
    assert len(data["values"]) == 4
    assert data["depths"] == [0.0, 10.0, 50.0, 100.0]


def test_get_variable_timeseries(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/variables/{variable}/timeseries returns sequence points."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(
        f"/api/v1/datasets/{dataset_id}/variables/sst/timeseries?latitude=15.0&longitude=75.0&depth=0.0"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["variable_name"] == "sst"
    assert len(data["points"]) == 5
    assert data["points"][0]["timestamp"] is not None
    assert "value" in data["points"][0]


def test_get_current_vectors_delivery(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/currents/vectors returns vector field for arrow/particle renderers."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(
        f"/api/v1/datasets/{dataset_id}/currents/vectors?u_var=u&v_var=v&w_var=w&time_index=0&depth_index=0"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["velocity_dimensions"] == "3D (total: u, v, w)"
    assert data["total_vectors"] == 10 * 12
    vec = data["vectors"][0]
    assert vec["u"] == 0.3
    assert vec["v"] == 0.4
    assert vec["w"] == 0.05
    assert pytest.approx(vec["speed"], rel=1e-2) == 0.5025
    assert pytest.approx(vec["direction"], rel=1e-2) == 36.87


def test_get_variable_slice(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/variables/{variable}/slice returns bounded multidimensional array."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(
        f"/api/v1/datasets/{dataset_id}/variables/salinity/slice?time_index=0&depth_index=0"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["variable_name"] == "salinity"
    assert data["shape"] == [10, 12]
    assert "lat" in data["dimension_coordinates"]
    assert "lon" in data["dimension_coordinates"]


def test_data_delivery_safety_limits_and_errors(registered_delivery_dataset):
    """Test error handling for non-existent variables, non-depth profile queries, and missing resources."""
    dataset_id, asset_id = registered_delivery_dataset

    # Non-existent variable
    resp_var = client.get(f"/api/v1/datasets/{dataset_id}/variables/unknown_var/grid")
    assert resp_var.status_code == 404

    # Non-existent dataset
    fake_id = uuid.uuid4()
    resp_ds = client.get(f"/api/v1/datasets/{fake_id}/metadata")
    assert resp_ds.status_code == 404

    # Out-of-bounds time index
    resp_time = client.get(f"/api/v1/datasets/{dataset_id}/variables/sst/grid?time_index=999")
    assert resp_time.status_code == 400


def test_get_variable_transect(registered_delivery_dataset):
    """Test /api/v1/datasets/{dataset_id}/variables/{variable}/transect extracts 1D cross-section."""
    dataset_id, asset_id = registered_delivery_dataset

    resp = client.get(
        f"/api/v1/datasets/{dataset_id}/variables/sst/transect?lat1=10.0&lon1=70.0&lat2=19.0&lon2=81.0&num_points=10&time_index=0&depth_index=0"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["variable_name"] == "sst"
    assert data["total_points"] == 10
    assert data["total_distance_km"] > 0
    assert len(data["points"]) == 10
    assert data["points"][0]["latitude"] == 10.0
    assert data["points"][0]["distance_km"] == 0.0
    assert data["points"][0]["value"] is None  # index (0, 0) is nan in fixture
    assert data["points"][1]["value"] is not None


