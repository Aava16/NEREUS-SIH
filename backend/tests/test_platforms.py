import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_platform_lifecycle() -> None:
    """Test observation platform registration, query, update, and deletion."""
    plat_code = f"ARGO_WMO_{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "name": plat_code,
        "platform_type": "ARGO_FLOAT",
        "operator": "INCOIS / Indian Argo Project",
        "description": "Autonomous profiling CTD float operating in Arabian Sea.",
        "metadata_json": {"wmo_id": plat_code, "sensor_type": "SBE41CP", "dac": "INCOIS"},
    }

    create_res = client.post("/api/v1/platforms", json=payload)
    assert create_res.status_code == 201
    platform = create_res.json()
    assert platform["name"] == plat_code
    assert platform["platform_type"] == "ARGO_FLOAT"
    platform_id = platform["id"]

    # Prevent duplicate
    dup_res = client.post("/api/v1/platforms", json=payload)
    assert dup_res.status_code == 409

    # Query platform
    get_res = client.get(f"/api/v1/platforms/{platform_id}")
    assert get_res.status_code == 200
    assert get_res.json()["operator"] == "INCOIS / Indian Argo Project"

    # Filter platforms
    list_res = client.get("/api/v1/platforms", params={"platform_type": "ARGO_FLOAT"})
    assert list_res.status_code == 200
    assert any(p["id"] == platform_id for p in list_res.json())

    # Update
    update_res = client.patch(
        f"/api/v1/platforms/{platform_id}",
        json={"operator": "INCOIS / Argo Marine Fleet"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["operator"] == "INCOIS / Argo Marine Fleet"

    # Delete
    del_res = client.delete(f"/api/v1/platforms/{platform_id}")
    assert del_res.status_code == 204
