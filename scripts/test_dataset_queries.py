import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== TESTING DATASET API QUERY FILTERS ===")
queries = [
    "/api/v1/datasets",
    "/api/v1/datasets?dataset_type=GRIDDED_OBSERVATION",
    "/api/v1/datasets?source=Copernicus",
    "/api/v1/datasets?bbox_min_lon=60.0&bbox_min_lat=5.0&bbox_max_lon=80.0&bbox_max_lat=20.0",
    "/api/v1/datasets?limit=10&offset=0",
    "/api/v1/datasets/002f5b9a-0c37-49ed-9659-952183a566a2",
    "/api/v1/datasets/002f5b9a-0c37-49ed-9659-952183a566a2/variables",
]

for q in queries:
    r = client.get(q)
    print(f"GET {q:85} -> {r.status_code}")
    assert r.status_code == 200, f"Failed on {q}: {r.text}"

print("\nALL DATASET API QUERIES PASSED WITH HTTP 200 OK!")
