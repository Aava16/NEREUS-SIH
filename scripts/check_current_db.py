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
    dbname = conn.execute(text("SELECT current_database();")).scalar()
    user = conn.execute(text("SELECT current_user;")).scalar()
    tables = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';")).scalars().all()
    print(f"Local config connected Database: {dbname}")
    print(f"Connected User: {user}")
    print(f"Tables in public schema ({len(tables)}): {tables}")
