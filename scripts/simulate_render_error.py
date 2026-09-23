import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.router import api_router, v1_router
from app.db.session import get_db

settings = get_settings()
url = settings.database_url
postgres_url = url.replace("/nereus_sih", "/postgres") if "/nereus_sih" in url else url

postgres_engine = create_engine(postgres_url)
PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine, expire_on_commit=False)

def override_get_db():
    db = PostgresSessionLocal()
    try:
        yield db
    finally:
        db.close()

test_app = FastAPI()
test_app.include_router(api_router)
test_app.include_router(v1_router)
test_app.dependency_overrides[get_db] = override_get_db

client = TestClient(test_app, raise_server_exceptions=False)
resp = client.get("/api/v1/datasets")
print(f"Test against 'postgres' db -> status: {resp.status_code}")
print(f"Response: {resp.text}")
