import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validation_run_lifecycle_and_metric_computation() -> None:
    """Test manual recording and dynamic calculation of model verification metrics (MAE, RMSE, Bias, Correlation)."""
    # 1. Create model dataset, observation dataset, and variable
    model_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"model_ds_{uuid.uuid4().hex[:8]}",
            "title": "HYCOM Model Forecast",
            "dataset_type": "MODEL_FORECAST",
        },
    )
    assert model_res.status_code == 201
    model_dataset_id = model_res.json()["id"]

    obs_ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"obs_ds_{uuid.uuid4().hex[:8]}",
            "title": "ARGO In-Situ Observations",
            "dataset_type": "IN_SITU_NETWORK",
        },
    )
    assert obs_ds_res.status_code == 201
    obs_dataset_id = obs_ds_res.json()["id"]

    var_res = client.post(
        "/api/v1/variables",
        json={
            "dataset_id": model_dataset_id,
            "name": "temperature",
            "standard_name": "sea_water_potential_temperature",
            "units": "degC",
        },
    )
    assert var_res.status_code == 201
    variable_id = var_res.json()["id"]

    # 2. Test On-The-Fly Computation and Persistence of Validation Metrics
    # Paired points: (model_prediction, observed_truth)
    # Model: [28.5, 27.2, 25.0, 22.1, 19.8]
    # Observed: [28.2, 27.0, 24.9, 22.0, 19.9]
    # Diffs: [0.3, 0.2, 0.1, 0.1, -0.1]
    # Mean Bias = (0.3+0.2+0.1+0.1-0.1)/5 = 0.6/5 = 0.12
    # MAE = (0.3+0.2+0.1+0.1+0.1)/5 = 0.8/5 = 0.16
    compute_payload = {
        "model_dataset_id": model_dataset_id,
        "observation_dataset_id": obs_dataset_id,
        "variable_id": variable_id,
        "paired_data": [
            [28.5, 28.2],
            [27.2, 27.0],
            [25.0, 24.9],
            [22.1, 22.0],
            [19.8, 19.9],
        ],
        "depth_level_min": 0.0,
        "depth_level_max": 200.0,
        "spatial_scope_geom": {
            "type": "Polygon",
            "coordinates": [
                [
                    [65.0, 5.0],
                    [80.0, 5.0],
                    [80.0, 20.0],
                    [65.0, 20.0],
                    [65.0, 5.0],
                ]
            ],
        },
    }

    comp_res = client.post("/api/v1/validation-runs/compute", json=compute_payload)
    assert comp_res.status_code == 201
    run_data = comp_res.json()
    assert run_data["sample_count"] == 5
    assert run_data["metric_mae"] == 0.16
    assert run_data["metric_bias"] == 0.12
    assert run_data["metric_rmse"] is not None
    assert run_data["metric_correlation"] is not None
    assert run_data["metric_correlation"] > 0.99  # Strong positive correlation
    assert run_data["spatial_scope_geom"] is not None
    assert run_data["spatial_scope_geom"]["type"] == "Polygon"
    run_id = run_data["id"]

    # 3. Query validation run by ID
    get_res = client.get(f"/api/v1/validation-runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["sample_count"] == 5

    # 4. Filter validation runs by model_dataset_id and variable_id
    list_res = client.get(
        "/api/v1/validation-runs",
        params={"model_dataset_id": model_dataset_id, "variable_id": variable_id},
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 5. Delete validation run
    del_res = client.delete(f"/api/v1/validation-runs/{run_id}")
    assert del_res.status_code == 204

    # Cleanup datasets
    client.delete(f"/api/v1/datasets/{model_dataset_id}")
    client.delete(f"/api/v1/datasets/{obs_dataset_id}")
