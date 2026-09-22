import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_processing_job_lifecycle() -> None:
    """Test queueing, updating status, querying, and deleting an asynchronous processing job."""
    # 1. Create a parent dataset
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"job_ds_{uuid.uuid4().hex[:8]}",
            "title": "Processing Job Target Dataset",
            "dataset_type": "MODEL_FORECAST",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 2. Queue a processing job
    job_payload = {
        "dataset_id": dataset_id,
        "job_type": "QUALITY_VALIDATION",
        "status": "QUEUED",
        "initiated_by": "automated-pipeline-trigger",
        "job_metadata": {"batch_id": "batch_2026_09", "parameters": {"qc_threshold": 3.0}},
    }

    create_res = client.post("/api/v1/processing-jobs", json=job_payload)
    assert create_res.status_code == 201
    job = create_res.json()
    assert job["job_type"] == "QUALITY_VALIDATION"
    assert job["status"] == "QUEUED"
    job_id = job["id"]

    # 3. Query job by ID
    get_res = client.get(f"/api/v1/processing-jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["initiated_by"] == "automated-pipeline-trigger"

    # 4. Filter jobs by status
    list_res = client.get(
        "/api/v1/processing-jobs",
        params={"dataset_id": dataset_id, "status": "QUEUED"},
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 5. Update job status to RUNNING, then COMPLETED
    update_res = client.patch(
        f"/api/v1/processing-jobs/{job_id}",
        json={
            "status": "COMPLETED",
            "completed_at": "2026-09-22T12:30:00Z",
            "logs_uri": "s3://nereus-logs/jobs/quality_validation_01.log",
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "COMPLETED"
    assert update_res.json()["logs_uri"] == "s3://nereus-logs/jobs/quality_validation_01.log"

    # 6. Delete job
    del_res = client.delete(f"/api/v1/processing-jobs/{job_id}")
    assert del_res.status_code == 204

    # Cleanup dataset
    client.delete(f"/api/v1/datasets/{dataset_id}")
