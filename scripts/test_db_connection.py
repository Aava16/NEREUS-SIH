import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from sqlalchemy import create_engine, text

def check_connection():
    settings = get_settings()
    has_db_url = bool(settings.database_url and len(settings.database_url) > 10)
    print(f"DATABASE_URL Loaded: {'YES' if has_db_url else 'NO'}")
    
    if not has_db_url:
        print("Error: DATABASE_URL is not set or empty.")
        return False

    try:
        # Create engine with standard parameters
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            pg_ver = conn.execute(text("SELECT version();")).scalar()
            print("Cloud PostgreSQL Connection: SUCCESS")
            print(f"PostgreSQL Version: {pg_ver.split(',')[0] if pg_ver else 'Unknown'}")
            
            # Check PostGIS extension
            postgis_ok = False
            try:
                pgis_ver = conn.execute(text("SELECT PostGIS_Full_Version();")).scalar()
                print(f"PostGIS Status: AVAILABLE (Version: {pgis_ver})")
                postgis_ok = True
            except Exception:
                # Check if we can enable or query postgis
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                    conn.commit()
                    pgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
                    print(f"PostGIS Status: AVAILABLE (Version: {pgis_ver})")
                    postgis_ok = True
                except Exception as ext_err:
                    print(f"PostGIS Status: FAILED ({type(ext_err).__name__})")
                    postgis_ok = False
            
            return True and postgis_ok
    except Exception as exc:
        print(f"Cloud PostgreSQL Connection: FAILED ({type(exc).__name__})")
        return False

if __name__ == "__main__":
    success = check_connection()
    sys.exit(0 if success else 1)
