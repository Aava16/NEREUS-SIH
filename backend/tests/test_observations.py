import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_observation_lifecycle_and_spatial_queries() -> None:
    """Test observation creation, bulk insertion, depth filtering, and spatial bounding box queries."""
    # 1. Create prerequisite Dataset, Platform, and Variable
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"obs_ds_{uuid.uuid4().hex[:8]}",
            "title": "Argo GDAC Real-Time In-Situ Observations",
            "dataset_type": "IN_SITU_NETWORK",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    plat_res = client.post(
        "/api/v1/platforms",
        json={
            "name": f"ARGO_{uuid.uuid4().hex[:6]}",
            "platform_type": "ARGO_FLOAT",
            "operator": "INCOIS",
        },
    )
    assert plat_res.status_code == 201
    platform_id = plat_res.json()["id"]

    var_res = client.post(
        "/api/v1/variables",
        json={
            "dataset_id": dataset_id,
            "name": "salinity",
            "standard_name": "sea_water_practical_salinity",
            "units": "PSU",
        },
    )
    assert var_res.status_code == 201
    variable_id = var_res.json()["id"]

    # 2. Ingest single observation
    single_obs_payload = {
        "dataset_id": dataset_id,
        "variable_id": variable_id,
        "platform_id": platform_id,
        "observed_at": "2026-03-15T12:00:00Z",
        "depth_m": 10.5,
        "value": 35.42,
        "quality_flag": 1,
        "geometry": {"type": "Point", "coordinates": [75.5, 15.0]},
        "metadata_json": {"cycle_number": 12, "pressure_dbar": 10.6},
    }

    obs_res = client.post("/api/v1/observations", json=single_obs_payload)
    assert obs_res.status_code == 201
    obs_data = obs_res.json()
    assert obs_data["value"] == 35.42
    assert obs_data["geometry"]["coordinates"] == [75.5, 15.0]
    obs_id = obs_data["id"]

    # 3. Bulk ingest observations across depth profile
    bulk_payload = {
        "observations": [
            {
                "dataset_id": dataset_id,
                "variable_id": variable_id,
                "platform_id": platform_id,
                "observed_at": "2026-03-15T12:05:00Z",
                "depth_m": 50.0,
                "value": 35.10,
                "quality_flag": 1,
                "geometry": {"type": "Point", "coordinates": [75.5, 15.0]},
                "metadata_json": {"cycle_number": 12},
            },
            {
                "dataset_id": dataset_id,
                "variable_id": variable_id,
                "platform_id": platform_id,
                "observed_at": "2026-03-15T12:10:00Z",
                "depth_m": 100.0,
                "value": 34.85,
                "quality_flag": 1,
                "geometry": {"type": "Point", "coordinates": [75.5, 15.0]},
                "metadata_json": {"cycle_number": 12},
            },
            {
                "dataset_id": dataset_id,
                "variable_id": variable_id,
                "platform_id": platform_id,
                "observed_at": "2026-03-15T12:20:00Z",
                "depth_m": 500.0,
                "value": 34.50,
                "quality_flag": 1,
                "geometry": {"type": "Point", "coordinates": [75.5, 15.0]},
                "metadata_json": {"cycle_number": 12},
            },
        ]
    }

    bulk_res = client.post("/api/v1/observations/bulk", json=bulk_payload)
    assert bulk_res.status_code == 201
    bulk_data = bulk_res.json()
    assert len(bulk_data) == 3

    # 4. Filter by depth range (shallow depths 0 - 60m)
    depth_res = client.get(
        "/api/v1/observations",
        params={
            "dataset_id": dataset_id,
            "depth_min": 0.0,
            "depth_max": 60.0,
        },
    )
    assert depth_res.status_code == 200
    shallow_points = depth_res.json()
    assert len(shallow_points) == 2  # 10.5m and 50.0m

    # 5. Filter by spatial bounding box enclosing Arabian Sea
    bbox_res = client.get(
        "/api/v1/observations",
        params={
            "dataset_id": dataset_id,
            "bbox_min_lon": 70.0,
            "bbox_min_lat": 10.0,
            "bbox_max_lon": 80.0,
            "bbox_max_lat": 20.0,
        },
    )
    assert bbox_res.status_code == 200
    assert len(bbox_res.json()) == 4

    # 6. Delete single observation
    del_res = client.delete(f"/api/v1/observations/{obs_id}")
    assert del_res.status_code == 204

    # Cleanup dataset and platform
    client.delete(f"/api/v1/datasets/{dataset_id}")
    client.delete(f"/api/v1/platforms/{platform_id}")
