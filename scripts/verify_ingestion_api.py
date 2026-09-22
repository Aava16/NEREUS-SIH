import sys
import os
import json

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.repositories.dataset import DatasetRepository
from app.repositories.provenance import ProvenanceRepository

def verify_all():
    print("=== 1. DATABASE REPOSITORY VERIFICATION ===")
    db = SessionLocal()
    try:
        repo = DatasetRepository()
        prov_repo = ProvenanceRepository()
        
        datasets = repo.list_datasets(db)
        print(f"Total datasets in database: {len(datasets)}")
        
        copernicus = next((d for d in datasets if "copernicus" in d.name.lower()), None)
        assert copernicus is not None, "Copernicus dataset not found in database!"
        
        print(f"Dataset ID:         {copernicus.id}")
        print(f"Dataset Name:       {copernicus.name}")
        print(f"Dataset Title:      {copernicus.title}")
        print(f"Dataset Type:       {copernicus.dataset_type}")
        print(f"Temporal Coverage:  {copernicus.temporal_start} to {copernicus.temporal_end}")
        print(f"Spatial Extent:     SRID={copernicus.spatial_extent.srid if copernicus.spatial_extent else 'N/A'}")
        
        print(f"\nVariables Registered ({len(copernicus.variables)}):")
        for v in copernicus.variables:
            print(f"  - {v.name} ({v.standard_name}): {v.units}, type={v.data_type}")
            
        print(f"\nArray Assets Registered ({len(copernicus.array_assets)}):")
        for a in copernicus.array_assets:
            print(f"  - Format: {a.storage_format}, URI: {a.uri}, Variables Info: {list(a.variable_info.keys()) if isinstance(a.variable_info, dict) else a.variable_info}")
            
        provs = prov_repo.list_records(db, dataset_id=copernicus.id)
        print(f"\nProvenance Records ({len(provs)}):")
        for p in provs:
            print(f"  - Action: {p.action}, Actor: {p.actor}, Source: {p.source}")
            
        ds_id = str(copernicus.id)
    finally:
        db.close()
        
    print("\n=== 2. FASTAPI API VERIFICATION ===")
    client = TestClient(app)
    
    # 1. Dataset Catalog
    r_cat = client.get("/api/v1/datasets")
    assert r_cat.status_code == 200
    print(f"GET /api/v1/datasets -> status={r_cat.status_code}, count={len(r_cat.json())}")
    
    # 2. Dataset Detail
    r_det = client.get(f"/api/v1/datasets/{ds_id}")
    assert r_det.status_code == 200
    det = r_det.json()
    print(f"GET /api/v1/datasets/{ds_id} -> status={r_det.status_code}, title='{det.get('title')}'")
    
    # 3. Variables Endpoint
    r_vars = client.get(f"/api/v1/datasets/{ds_id}/variables")
    assert r_vars.status_code == 200
    print(f"GET /api/v1/datasets/{ds_id}/variables -> status={r_vars.status_code}, count={len(r_vars.json())}")
    
    # 4. Grid Delivery
    r_grid = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/grid?depth_index=0&time_index=0")
    assert r_grid.status_code == 200
    grid_json = r_grid.json()
    print(f"GET thetao grid -> status={r_grid.status_code}, lats={len(grid_json.get('latitudes', []))}, lons={len(grid_json.get('longitudes', []))}")
    
    # 5. Depth Profile
    r_prof = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/profile?latitude=14.0&longitude=70.0&time_index=0")
    assert r_prof.status_code == 200
    prof_json = r_prof.json()
    print(f"GET thetao profile -> status={r_prof.status_code}, depths count={len(prof_json.get('depths', []))}")
    
    # 6. Time Series
    r_ts = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/timeseries?latitude=14.0&longitude=70.0&depth_index=0")
    assert r_ts.status_code == 200
    ts_json = r_ts.json()
    print(f"GET thetao timeseries -> status={r_ts.status_code}, times count={len(ts_json.get('times', []))}")
    
    # 7. Currents Vectors
    r_curr = client.get(f"/api/v1/datasets/{ds_id}/currents/vectors?u_var=uo&v_var=vo&depth_index=0&time_index=0")
    assert r_curr.status_code == 200
    curr_json = r_curr.json()
    print(f"GET currents vectors -> status={r_curr.status_code}, vectors count={len(curr_json.get('vectors', []))}")
    
    # 8. Transect Cross-Section
    r_tran = client.get(f"/api/v1/datasets/{ds_id}/variables/thetao/transect?lat1=10.0&lon1=66.0&lat2=16.0&lon2=74.0&num_points=25")
    assert r_tran.status_code == 200
    tran_json = r_tran.json()
    print(f"GET thetao transect -> status={r_tran.status_code}, points count={len(tran_json.get('points', []))}")
    
    # 9. Statistics
    r_stat = client.get(f"/api/v1/analysis/datasets/{ds_id}/statistics?variable_name=thetao")
    assert r_stat.status_code == 200
    stat_json = r_stat.json()
    var_stat = stat_json.get("variables", {}).get("thetao", {})
    print(f"GET thetao statistics -> status={r_stat.status_code}, mean={var_stat.get('mean'):.3f}, valid_count={var_stat.get('valid_count')}")
    
    # 10. Provenance
    r_prov = client.get(f"/api/v1/provenance?dataset_id={ds_id}")
    assert r_prov.status_code == 200
    print(f"GET provenance -> status={r_prov.status_code}, records={len(r_prov.json())}")
    
    print("\n>>> ALL INGESTION & SCIENTIFIC DATA APIS VERIFIED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    verify_all()
