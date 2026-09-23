import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    curr_db = conn.execute(text("SELECT current_database();")).scalar()
    print(f"Current Database: {curr_db}")
    
    # List all databases on this PostgreSQL instance
    dbs = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false;")).scalars().all()
    print(f"All Non-template Databases on this instance: {dbs}")
    
    # Check if 'postgres' database exists and what tables are in current db
    tables_curr = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';")).scalars().all()
    print(f"Tables in '{curr_db}' public schema: {tables_curr}")
