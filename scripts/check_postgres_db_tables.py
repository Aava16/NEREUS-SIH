import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()
# Replace database name at the end of database_url to 'postgres'
url = settings.database_url
if "/nereus_sih" in url:
    postgres_url = url.replace("/nereus_sih", "/postgres")
else:
    postgres_url = url

engine = create_engine(postgres_url)
try:
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public';")).scalars().all()
        print(f"Tables in 'postgres' database ({len(tables)}): {tables}")
except Exception as e:
    print(f"Error connecting to 'postgres' database: {e}")
