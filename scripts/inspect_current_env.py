import sys
import os
from urllib.parse import urlparse

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()
u = urlparse(settings.database_url)
print(f"Configured Scheme: {u.scheme}")
print(f"Configured Host:   {u.hostname}")
print(f"Configured Port:   {u.port}")
print(f"Configured DB:     {u.path.lstrip('/')}")
print(f"Configured User:   {u.username}")

engine = create_engine(settings.database_url)
with engine.connect() as conn:
    curr_db = conn.execute(text("SELECT current_database();")).scalar()
    curr_user = conn.execute(text("SELECT current_user;")).scalar()
    tables = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';")).scalars().all()
    print(f"\nLive Connection DB:   {curr_db}")
    print(f"Live Connection User: {curr_user}")
    print(f"Tables in public schema ({len(tables)}): {tables}")
    
    if "datasets" in tables:
        count = conn.execute(text("SELECT COUNT(*) FROM datasets;")).scalar()
        print(f"Row count in 'datasets': {count}")
        cols = conn.execute(text("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name='datasets';")).fetchall()
        print("Columns in 'datasets':")
        for col in cols:
            print(f"  - {col[0]}: {col[1]} ({col[2]})")
