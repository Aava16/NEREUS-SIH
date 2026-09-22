import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provenance_lifecycle() -> None:
    """Test scientific provenance audit logging and lookup."""
    # 1. Create parent dataset
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"prov_ds_{uuid.uuid4().hex[:8]}",
            "title": "Indian Ocean Climatology Baseline",
            "dataset_type": "CLIMATOLOGY",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 2. Record provenance event
    prov_payload = {
        "dataset_id": dataset_id,
        "action": "INGESTION",
        "source": "ftp://incois.gov.in/pub/data/argo_2026.nc",
        "actor": "pipeline-worker-01",
        "details": {
            "records_processed": 14250,
            "qc_passed_percentage": 98.6,
            "pipeline_version": "v1.4.0",
        },
    }

    create_res = client.post("/api/v1/provenance", json=prov_payload)
    assert create_res.status_code == 201
    prov_data = create_res.json()
    assert prov_data["action"] == "INGESTION"
    assert prov_data["details"]["records_processed"] == 14250
    record_id = prov_data["id"]

    # 3. Query record by ID
    get_res = client.get(f"/api/v1/provenance/{record_id}")
    assert get_res.status_code == 200
    assert get_res.json()["actor"] == "pipeline-worker-01"

    # 4. List records by dataset and action
    list_res = client.get(
        "/api/v1/provenance",
        params={"dataset_id": dataset_id, "action": "INGESTION"},
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Cleanup dataset
    client.delete(f"/api/v1/datasets/{dataset_id}")
