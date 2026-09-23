import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_get_datasets_api_returns_copernicus_dataset():
    """Regression test ensuring GET /api/v1/datasets returns 200 and includes Copernicus dataset."""
    client = TestClient(app)
    
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    datasets = response.json()
    assert isinstance(datasets, list), "Expected list of datasets"
    assert len(datasets) >= 1, "Expected at least one dataset in catalog"
    
    copernicus = next(
        (d for d in datasets if "copernicus" in d.get("name", "").lower() or "copernicus" in d.get("title", "").lower()),
        None,
    )
    assert copernicus is not None, "Copernicus Arabian Sea 2024 dataset must be present"
    assert copernicus["title"] == "Copernicus Multi-Observation 3D Ocean Physics (Arabian Sea 2024)"
    assert copernicus["dataset_type"] == "GRIDDED_OBSERVATION"
    assert copernicus["spatial_extent"] is not None
    assert copernicus["spatial_extent"]["type"] == "Polygon"
    assert "metadata_json" in copernicus
    
    # Test dataset detail endpoint
    ds_id = copernicus["id"]
    detail_resp = client.get(f"/api/v1/datasets/{ds_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == ds_id
    assert detail["variables_count"] >= 1
    assert detail["array_assets_count"] >= 1
