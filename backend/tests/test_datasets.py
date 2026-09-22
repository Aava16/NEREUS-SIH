import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_get_dataset() -> None:
    """Test creating a dataset with GeoJSON polygon extent and retrieving details."""
    unique_name = f"test_hycom_{uuid.uuid4().hex[:8]}"
    payload = {
        "name": unique_name,
        "title": "HYCOM Indian Ocean Reanalysis Model",
        "description": "High-resolution numerical model forecast for the Indian Ocean basin.",
        "source": "INCOIS / HYCOM Consortium",
        "source_uri": "https://hycom.org/data/indian_ocean",
        "dataset_type": "MODEL_FORECAST",
        "temporal_start": "2026-01-01T00:00:00Z",
        "temporal_end": "2026-12-31T23:59:59Z",
        "spatial_extent": {
            "type": "Polygon",
            "coordinates": [
                [
                    [50.0, -10.0],
                    [100.0, -10.0],
                    [100.0, 30.0],
                    [50.0, 30.0],
                    [50.0, -10.0],
                ]
            ],
        },
        "metadata_json": {"grid_resolution": "0.08 deg", "vertical_levels": 40},
    }

    create_res = client.post("/api/v1/datasets", json=payload)
    assert create_res.status_code == 201
    dataset = create_res.json()
    assert dataset["name"] == unique_name
    assert dataset["title"] == payload["title"]
    assert dataset["spatial_extent"] is not None
    assert dataset["spatial_extent"]["type"] == "Polygon"
    dataset_id = dataset["id"]

    # Test Duplicate Conflict
    dup_res = client.post("/api/v1/datasets", json=payload)
    assert dup_res.status_code == 409

    # Test Get by ID
    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == dataset_id
    assert "variables_count" in detail
    assert "array_assets_count" in detail

    # Test Spatial Filtering with Bounding Box
    filter_res = client.get(
        "/api/v1/datasets",
        params={
            "bbox_min_lon": 60.0,
            "bbox_min_lat": 0.0,
            "bbox_max_lon": 90.0,
            "bbox_max_lat": 20.0,
        },
    )
    assert filter_res.status_code == 200
    results = filter_res.json()
    assert any(d["id"] == dataset_id for d in results)

    # Test Update
    update_res = client.patch(
        f"/api/v1/datasets/{dataset_id}",
        json={"title": "HYCOM Indian Ocean Updated Title"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "HYCOM Indian Ocean Updated Title"

    # Test Delete
    del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_res.status_code == 204

    # Verify not found after delete
    get_after_del = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_after_del.status_code == 404
