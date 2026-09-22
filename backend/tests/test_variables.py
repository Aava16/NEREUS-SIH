import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_variable_lifecycle() -> None:
    """Test variable registration, lookup, constraint enforcement, and deletion."""
    # 1. Create a parent dataset
    dataset_name = f"var_ds_{uuid.uuid4().hex[:8]}"
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": dataset_name,
            "title": "Variable Parent Test Dataset",
            "dataset_type": "IN_SITU_NETWORK",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 2. Register a variable under the dataset
    var_payload = {
        "dataset_id": dataset_id,
        "name": "temperature",
        "standard_name": "sea_water_potential_temperature",
        "long_name": "Sea Water Potential Temperature",
        "units": "degC",
        "data_type": "float32",
        "description": "Insitu water temperature measured in degrees Celsius.",
        "metadata_json": {"valid_min": -2.0, "valid_max": 40.0, "colormap": "thermal"},
    }

    create_res = client.post("/api/v1/variables", json=var_payload)
    assert create_res.status_code == 201
    var_data = create_res.json()
    assert var_data["name"] == "temperature"
    assert var_data["units"] == "degC"
    var_id = var_data["id"]

    # 3. Prevent duplicate variable in same dataset
    dup_res = client.post("/api/v1/variables", json=var_payload)
    assert dup_res.status_code == 409

    # 4. List variables by dataset_id
    list_res = client.get("/api/v1/variables", params={"dataset_id": dataset_id})
    assert list_res.status_code == 200
    vars_list = list_res.json()
    assert len(vars_list) == 1
    assert vars_list[0]["id"] == var_id

    # 5. Update variable
    update_res = client.patch(
        f"/api/v1/variables/{var_id}",
        json={"long_name": "Updated Sea Water Temperature"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["long_name"] == "Updated Sea Water Temperature"

    # 6. Delete variable
    del_res = client.delete(f"/api/v1/variables/{var_id}")
    assert del_res.status_code == 204

    # 7. Cleanup dataset
    client.delete(f"/api/v1/datasets/{dataset_id}")
