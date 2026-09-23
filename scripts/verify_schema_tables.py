import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from sqlalchemy import create_engine, inspect, text

def verify_schema():
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    inspector = inspect(engine)
    
    tables = inspector.get_table_names(schema="public")
    print(f"Total tables found in public schema: {len(tables)}")
    
    
    expected_tables = [
        "datasets",
        "platforms",
        "variables",
        "array_assets",
        "observations",
        "provenance_records",
        "processing_jobs",
        "validation_runs",
        "alembic_version",
    ]
    
    missing_tables = [t for t in expected_tables if t not in tables]
    present_tables = [t for t in expected_tables if t in tables]
    
    print(f"Present expected tables ({len(present_tables)}/{len(expected_tables)}):")
    for t in sorted(present_tables):
        cols = inspector.get_columns(t)
        print(f"  - {t} ({len(cols)} columns)")
        
    if missing_tables:
        print(f"MISSING TABLES: {missing_tables}")
        return False
        
    # Check alembic version in DB
    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"alembic_version table reports revision: {rev}")
        
        # Test spatial query
        geom_test = conn.execute(text("SELECT ST_AsText(ST_SetSRID(ST_Point(70.0, 15.0), 4326));")).scalar()
        print(f"PostGIS Spatial Query Test: {geom_test} -> SUCCESS")
        
    return True

if __name__ == "__main__":
    ok = verify_schema()
    sys.exit(0 if ok else 1)
