import sys
import os
import traceback

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import httpx

print("=== CHECKING REMOTE RENDER ENDPOINTS ===")
try:
    r_health = httpx.get("https://nereus-sih.onrender.com/health", timeout=10.0)
    print(f"Render GET /health: {r_health.status_code} -> {r_health.text}")
    
    r_db = httpx.get("https://nereus-sih.onrender.com/health/db", timeout=10.0)
    print(f"Render GET /health/db: {r_db.status_code} -> {r_db.text}")
    
    r_datasets = httpx.get("https://nereus-sih.onrender.com/api/v1/datasets", timeout=10.0)
    print(f"Render GET /api/v1/datasets: {r_datasets.status_code} -> {r_datasets.text}")
except Exception as exc:
    print(f"Render HTTP request failed: {exc}")

print("\n=== CHECKING LOCAL FASTAPI / DATABASE TRACE ===")
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.services.dataset import DatasetService

try:
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v1/datasets")
    print(f"Local TestClient GET /api/v1/datasets: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as exc:
    print("TestClient Exception:")
    traceback.print_exc()

print("\n=== DIRECT SERVICE/REPOSITORY EXECUTION ===")
db = SessionLocal()
try:
    svc = DatasetService()
    results = svc.list_datasets(db)
    print(f"DatasetService.list_datasets returned {len(results)} items")
    for r in results:
        print("Item:", r.model_dump())
except Exception as exc:
    print("Service Exception:")
    traceback.print_exc()
finally:
    db.close()
