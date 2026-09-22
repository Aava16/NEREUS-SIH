"""Tests for Phase 7: Scientific Data Analysis Foundation.

Validates statistical reductions, spatial extent extraction, temporal resolution,
2D/3D ocean current velocity magnitudes and directional flow, derived variables,
dataset summaries, and robust error handling using synthetic array fixtures.
"""

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
def synthetic_ocean_netcdf():
    """Create a temporary synthetic NetCDF4 file with temperature, currents, and salinity."""
    fd, path = tempfile.mkstemp(suffix=".nc")
    os.close(fd)

    ds = nc.Dataset(path, "w", format="NETCDF4")

    # Dimensions
    ds.createDimension("time", 4)
    ds.createDimension("depth", 3)
    ds.createDimension("lat", 6)
    ds.createDimension("lon", 8)

    # Coordinate variables
    time_var = ds.createVariable("time", "f8", ("time",))
    time_var.units = "hours since 2026-01-01 00:00:00"
    time_var.standard_name = "time"
    time_var[:] = [0.0, 6.0, 12.0, 18.0]

    depth_var = ds.createVariable("depth", "f4", ("depth",))
    depth_var.units = "m"
    depth_var.standard_name = "depth"
    depth_var[:] = [0.0, 10.0, 50.0]

    lat_var = ds.createVariable("lat", "f4", ("lat",))
    lat_var.units = "degrees_north"
    lat_var.standard_name = "latitude"
    lat_var[:] = np.linspace(10.0, 15.0, 6)

    lon_var = ds.createVariable("lon", "f4", ("lon",))
    lon_var.units = "degrees_east"
    lon_var.standard_name = "longitude"
    lon_var[:] = np.linspace(70.0, 77.0, 8)

    # Data variables: Temperature (with a few NaNs)
    sst_var = ds.createVariable("sst", "f4", ("time", "depth", "lat", "lon"), fill_value=-999.0)
    sst_var.units = "degC"
    sst_var.standard_name = "sea_surface_temperature"
    sst_data = 25.0 + np.random.uniform(-2.0, 2.0, size=(4, 3, 6, 8)).astype(np.float32)
    sst_data[0, 0, 0, 0] = np.nan  # NaN value
    sst_data[1, 1, 2, 2] = np.nan  # NaN value
    sst_var[:] = sst_data

    # Velocity fields: U (eastward), V (northward), W (upward)
    u_var = ds.createVariable("u", "f4", ("time", "depth", "lat", "lon"))
    u_var.units = "m/s"
    u_var.standard_name = "eastward_sea_water_velocity"
    u_data = np.full((4, 3, 6, 8), 0.3, dtype=np.float32)  # 0.3 m/s east
    u_var[:] = u_data

    v_var = ds.createVariable("v", "f4", ("time", "depth", "lat", "lon"))
    v_var.units = "m/s"
    v_var.standard_name = "northward_sea_water_velocity"
    v_data = np.full((4, 3, 6, 8), 0.4, dtype=np.float32)  # 0.4 m/s north -> speed = sqrt(0.3^2 + 0.4^2) = 0.5 m/s
    v_var[:] = v_data

    w_var = ds.createVariable("w", "f4", ("time", "depth", "lat", "lon"))
    w_var.units = "m/s"
    w_var.standard_name = "upward_sea_water_velocity"
    w_data = np.full((4, 3, 6, 8), 0.0, dtype=np.float32)
    w_var[:] = w_data

    # Temperature in Kelvin for derived conversions
    temp_k_var = ds.createVariable("temperature", "f4", ("time", "depth", "lat", "lon"))
    temp_k_var.units = "K"
    temp_k_var.standard_name = "sea_water_temperature"
    temp_k_var[:] = np.full((4, 3, 6, 8), 300.15, dtype=np.float32)  # 300.15 K = 27.0 °C

    ds.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def registered_dataset_and_asset(synthetic_ocean_netcdf):
    """Register a canonical dataset and array asset pointing to the synthetic fixture."""
    from datetime import datetime, timezone
    db = next(get_db())

    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        name=f"analysis-test-dataset-{dataset_id.hex[:6]}",
        title="Analysis Test Dataset",
        description="Dataset for scientific analysis foundation testing",
        source="INCOIS_SIMULATION",
        source_uri=synthetic_ocean_netcdf,
        dataset_type="GRIDDED_MODEL",
        temporal_start=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        temporal_end=datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
        metadata_json={"institution": "INCOIS"},
    )
    db.add(dataset)
    db.flush()

    asset_id = uuid.uuid4()
    asset = ArrayAsset(
        id=asset_id,
        dataset_id=dataset_id,
        storage_format="NETCDF4",
        uri=synthetic_ocean_netcdf,
        dimensions={"time": 4, "depth": 3, "lat": 6, "lon": 8},
        variable_info={"sst": "degC", "u": "m/s", "v": "m/s", "w": "m/s"},
    )
    db.add(asset)
    db.commit()

    yield dataset_id, asset_id

    # Teardown
    db.delete(asset)
    db.delete(dataset)
    db.commit()


def test_dataset_statistics_endpoint_and_nan_handling(registered_dataset_and_asset):
    """Test /api/v1/analysis/datasets/{dataset_id}/statistics handles NaNs and calculates all percentiles."""
    dataset_id, asset_id = registered_dataset_and_asset

    # 1. Statistics for all variables
    resp = client.get(f"/api/v1/analysis/datasets/{dataset_id}/statistics")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert str(data["dataset_id"]) == str(dataset_id)
    assert "sst" in data["variables"]
    assert "u" in data["variables"]
    assert "v" in data["variables"]

    sst_stats = data["variables"]["sst"]
    assert sst_stats["missing_count"] == 2  # exactly 2 NaNs inserted
    assert sst_stats["valid_count"] == (4 * 3 * 6 * 8) - 2
    assert sst_stats["min"] is not None
    assert sst_stats["max"] is not None
    assert sst_stats["mean"] is not None
    assert sst_stats["median"] is not None
    assert sst_stats["std"] is not None
    assert sst_stats["p25"] is not None
    assert sst_stats["p50"] is not None
    assert sst_stats["p75"] is not None
    assert sst_stats["p90"] is not None
    assert sst_stats["p95"] is not None

    # 2. Statistics for specific single variable
    single_resp = client.get(f"/api/v1/analysis/datasets/{dataset_id}/statistics?variable=u")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert list(single_data["variables"].keys()) == ["u"]
    u_stats = single_data["variables"]["u"]
    assert u_stats["mean"] == 0.3
    assert u_stats["min"] == 0.3
    assert u_stats["max"] == 0.3
    assert u_stats["missing_count"] == 0


def test_dataset_spatial_analysis(registered_dataset_and_asset):
    """Test /api/v1/analysis/datasets/{dataset_id}/spatial returns correct bounding box and depths."""
    dataset_id, asset_id = registered_dataset_and_asset

    resp = client.get(f"/api/v1/analysis/datasets/{dataset_id}/spatial")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    spatial = data["spatial_extent"]
    assert spatial["latitude_min"] == 10.0
    assert spatial["latitude_max"] == 15.0
    assert spatial["latitude_points"] == 6
    assert spatial["longitude_min"] == 70.0
    assert spatial["longitude_max"] == 77.0
    assert spatial["longitude_points"] == 8

    depth = data["depth_range"]
    assert depth["depth_min"] == 0.0
    assert depth["depth_max"] == 50.0
    assert depth["depth_levels_count"] == 3
    assert depth["levels"] == [0.0, 10.0, 50.0]


def test_dataset_temporal_analysis(registered_dataset_and_asset):
    """Test /api/v1/analysis/datasets/{dataset_id}/temporal returns time range and intervals."""
    dataset_id, asset_id = registered_dataset_and_asset

    resp = client.get(f"/api/v1/analysis/datasets/{dataset_id}/temporal")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    temp = data["temporal_range"]
    assert temp["total_timesteps"] == 4
    assert temp["start_time"] is not None
    assert temp["end_time"] is not None
    assert temp["is_regular_interval"] is True
    assert len(data["timesteps_sample"]) >= 4


def test_dataset_ocean_currents_analysis(registered_dataset_and_asset):
    """Test /api/v1/analysis/datasets/{dataset_id}/currents computes speed magnitude and flow direction."""
    dataset_id, asset_id = registered_dataset_and_asset

    # Test 2D current analysis (u=0.3, v=0.4 -> speed = 0.5 m/s, atan2(0.3, 0.4) = 36.87 degrees)
    resp = client.get(f"/api/v1/analysis/datasets/{dataset_id}/currents?u_var=u&v_var=v")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["velocity_dimensions"] == "2D (horizontal: u, v)"
    assert data["variables_used"] == {"u": "u", "v": "v"}

    speed_stats = data["speed_statistics"]
    assert pytest.approx(speed_stats["mean"], rel=1e-3) == 0.5
    assert pytest.approx(speed_stats["min"], rel=1e-3) == 0.5
    assert pytest.approx(speed_stats["max"], rel=1e-3) == 0.5

    dir_stats = data["direction_statistics"]
    assert dir_stats["vector_mean_direction_degrees"] is not None
    assert pytest.approx(dir_stats["vector_mean_direction_degrees"], rel=1e-2) == 36.87
    assert pytest.approx(dir_stats["vector_mean_speed_m_s"], rel=1e-2) == 0.5

    # Test 3D current analysis with w component
    resp_3d = client.get(f"/api/v1/analysis/datasets/{dataset_id}/currents?u_var=u&v_var=v&w_var=w")
    assert resp_3d.status_code == 200
    data_3d = resp_3d.json()
    assert data_3d["velocity_dimensions"] == "3D (total: u, v, w)"
    assert "w" in data_3d["variables_used"]
    assert "w" in data_3d["component_statistics"]


def test_dataset_analysis_summary(registered_dataset_and_asset):
    """Test /api/v1/analysis/datasets/{dataset_id}/summary returns aggregated metadata & distribution."""
    dataset_id, asset_id = registered_dataset_and_asset

    resp = client.get(f"/api/v1/analysis/datasets/{dataset_id}/summary")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert str(data["dataset_id"]) == str(dataset_id)
    assert data["data_type"] == "GRIDDED_MODEL"
    assert data["spatial_extent"]["latitude_min"] == 10.0
    assert data["spatial_extent"]["longitude_max"] == 77.0
    assert data["depth_range"]["depth_levels_count"] == 3
    assert data["temporal_range"]["total_timesteps"] == 4
    assert "sst" in data["available_variables"]
    assert "sst" in data["variables_summary"]


def test_analysis_error_handling_and_validation(registered_dataset_and_asset):
    """Test error handling for non-existent datasets, missing variables, and invalid parameters."""
    dataset_id, asset_id = registered_dataset_and_asset

    # Non-existent dataset ID
    fake_id = uuid.uuid4()
    resp = client.get(f"/api/v1/analysis/datasets/{fake_id}/statistics")
    assert resp.status_code == 404

    # Non-existent variable in existing dataset
    resp_var = client.get(f"/api/v1/analysis/datasets/{dataset_id}/statistics?variable=non_existent_var")
    assert resp_var.status_code == 404
    assert "not found in dataset" in resp_var.json()["detail"]

    # Non-existent current variable
    resp_curr = client.get(f"/api/v1/analysis/datasets/{dataset_id}/currents?u_var=bad_u&v_var=bad_v")
    assert resp_curr.status_code == 400
    assert "not found" in resp_curr.json()["detail"]


def test_derived_analyzer_calculations(synthetic_ocean_netcdf):
    """Test DerivedAnalyzer for kinetic energy and Celsius conversion."""
    import xarray as xr
    from app.services.analysis.derived import DerivedAnalyzer

    with xr.open_dataset(synthetic_ocean_netcdf) as ds:
        # Kinetic energy: 0.5 * (u^2 + v^2) = 0.5 * (0.3^2 + 0.4^2) = 0.5 * 0.25 = 0.125
        ke, units, std_name = DerivedAnalyzer.compute("KINETIC_ENERGY", ds)
        assert pytest.approx(float(ke[0, 0, 0, 0]), rel=1e-3) == 0.125
        assert units == "m2 s-2"
        assert std_name == "specific_kinetic_energy_of_sea_water"

        # Celsius from Kelvin: 300.15 - 273.15 = 27.0
        celsius, c_units, c_std_name = DerivedAnalyzer.compute("CELSIUS_FROM_KELVIN", ds)
        assert pytest.approx(float(celsius[0, 0, 0, 0]), rel=1e-3) == 27.0
        assert c_units == "degC"

