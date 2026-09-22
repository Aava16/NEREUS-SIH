import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_array_asset_lifecycle() -> None:
    """Test scientific multidimensional array asset registration and querying."""
    # 1. Create parent dataset
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"asset_ds_{uuid.uuid4().hex[:8]}",
            "title": "Copernicus Marine Global Ocean Physics Analysis",
            "dataset_type": "REANALYSIS",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 2. Register array asset
    asset_payload = {
        "dataset_id": dataset_id,
        "storage_format": "NETCDF4",
        "uri": "s3://nereus-ocean-data/cmems/glorys12v1_daily_2026.nc",
        "variable_info": {
            "thetao": {"long_name": "Sea water potential temperature", "units": "degrees_C"},
            "so": {"long_name": "Sea water salinity", "units": "1e-3"},
        },
        "dimensions": {"time": 365, "depth": 50, "latitude": 2041, "longitude": 4320},
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }

    create_res = client.post("/api/v1/array-assets", json=asset_payload)
    assert create_res.status_code == 201
    asset_data = create_res.json()
    assert asset_data["storage_format"] == "NETCDF4"
    assert asset_data["uri"] == asset_payload["uri"]
    asset_id = asset_data["id"]

    # 3. Query asset by ID
    get_res = client.get(f"/api/v1/array-assets/{asset_id}")
    assert get_res.status_code == 200
    assert get_res.json()["dimensions"]["time"] == 365

    # 4. List assets by dataset_id
    list_res = client.get("/api/v1/array-assets", params={"dataset_id": dataset_id})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 5. Delete asset
    del_res = client.delete(f"/api/v1/array-assets/{asset_id}")
    assert del_res.status_code == 204

    # Cleanup dataset
    client.delete(f"/api/v1/datasets/{dataset_id}")
