import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== 1. HEALTH & ROOT ENDPOINTS ===")
for path in ["/health", "/health/db", "/api/v1/health", "/api/v1/health/db", "/docs", "/openapi.json"]:
    resp = client.get(path)
    print(f"GET {path:20} -> status={resp.status_code}")
    assert resp.status_code == 200, f"Failed on {path}"

print("\n=== 2. DATASETS & VARIABLES ===")
resp = client.get("/api/v1/datasets")
assert resp.status_code == 200
datasets = resp.json()
print(f"Total datasets found: {len(datasets)}")
demo_ds = next(
    (d for d in datasets if "copernicus" in d.get("name", "").lower() or "copernicus" in d.get("dataset_name", "").lower()),
    None
)
if not demo_ds:
    print("Copernicus dataset not found by name, using first available dataset.")
    demo_ds = datasets[0]

ds_id = demo_ds["id"]
print(f"Selected demo dataset: id={ds_id}, name={demo_ds.get('name')}")

resp_vars = client.get(f"/api/v1/datasets/{ds_id}/variables")
print(f"Variables status: {resp_vars.status_code}, count: {len(resp_vars.json())}")

print("\n=== 3. SCIENTIFIC DATA DELIVERY ENDPOINTS ===")
# Grid map
resp_grid = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/grid?depth_index=0&time_index=0")
print(f"GET thetao grid -> status={resp_grid.status_code}, shape={resp_grid.json().get('shape')}")
assert resp_grid.status_code == 200

# Profile
resp_prof = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/profile?latitude=15.0&longitude=70.0&time_index=0")
print(f"GET thetao profile -> status={resp_prof.status_code}, depths count={len(resp_prof.json().get('depths', []))}")
assert resp_prof.status_code == 200

# Time Series
resp_ts = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/timeseries?latitude=15.0&longitude=70.0&depth_index=0")
print(f"GET thetao timeseries -> status={resp_ts.status_code}, times count={len(resp_ts.json().get('times', []))}")
assert resp_ts.status_code == 200

# Currents
resp_curr = client.get(f"/api/v1/datasets/{ds_id}/currents/vectors?u_var=uo&v_var=vo&depth_index=0&time_index=0")
print(f"GET currents vectors -> status={resp_curr.status_code}, points={len(resp_curr.json().get('vectors', []))}")
assert resp_curr.status_code == 200

# Transect
resp_tran = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/transect?lat1=10.0&lon1=66.0&lat2=16.0&lon2=74.0&num_points=20")
print(f"GET thetao transect -> status={resp_tran.status_code}, points count={len(resp_tran.json().get('points', []))}")
assert resp_tran.status_code == 200

# Statistics
resp_stat = client.get(f"/api/v1/analysis/datasets/{ds_id}/statistics?variable_name=thetao")
thetao_stats = resp_stat.json().get("variables", {}).get("thetao", {})
print(f"GET statistics -> status={resp_stat.status_code}, thetao mean={thetao_stats.get('mean'):.3f}, valid_count={thetao_stats.get('valid_count')}")
assert resp_stat.status_code == 200

# Provenance
resp_prov = client.get(f"/api/v1/provenance?dataset_id={ds_id}")
print(f"GET provenance -> status={resp_prov.status_code}, records={len(resp_prov.json())}")
assert resp_prov.status_code == 200

print("\n=== 4. ERROR-STATE & SAFETY LIMIT CHECKS ===")
# Nonexistent dataset
resp_404 = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000000/variables/thetao/grid")
print(f"GET nonexistent dataset -> status={resp_404.status_code} (expected 404)")
assert resp_404.status_code == 404

# Nonexistent variable
resp_v404 = client.get(f"/api/v1/datasets/{ds_id}/variables/nonexistent_variable_xyz/grid")
print(f"GET nonexistent variable -> status={resp_v404.status_code} (expected 404)")
assert resp_v404.status_code == 404

print("\n=======================================================")
print(">>> ALL LIVE SMOKE & SAFETY TESTS PASSED WITH 100% SUCCESS <<<")
print("=======================================================")
