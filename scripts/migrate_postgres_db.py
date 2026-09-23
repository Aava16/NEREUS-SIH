import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from app.core.config import get_settings
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

settings = get_settings()
# Target postgres database
url = settings.database_url
if "/nereus_sih" in url:
    postgres_url = url.replace("/nereus_sih", "/postgres")
else:
    postgres_url = url

print("Ensuring PostGIS and running Alembic on 'postgres' database...")
engine = create_engine(postgres_url)
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    conn.commit()
    print("PostGIS enabled on 'postgres' database.")

alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)
alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

command.upgrade(alembic_cfg, "head")
print("Alembic upgrade head completed on 'postgres' database.")

# Now ingest Copernicus demo dataset into 'postgres' database
from app.db.session import SessionLocal, sessionmaker
from app.schemas.ingestion import DatasetIngestionRequest
from app.services.ingestion import IngestionService
from app.repositories.dataset import DatasetRepository
import json
from pathlib import Path
from generate_copernicus_demo_asset import generate_copernicus_dataset

PostgresSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
db = PostgresSessionLocal()
try:
    manifest_path = Path(backend_dir).parent / "data" / "manifests" / "copernicus_multiobs_glo_phy_tsuv_manifest.json"
    nc_path = Path(backend_dir).parent / "data" / "processed" / "copernicus_multiobs_arabian_sea_2024.nc"
    if not nc_path.exists():
        generate_copernicus_dataset(str(nc_path))
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest_data["array_assets"][0]["uri"] = str(nc_path.resolve())
    
    payload = DatasetIngestionRequest.model_validate(manifest_data)
    service = IngestionService()
    dataset_repo = DatasetRepository()
    
    existing = dataset_repo.get_by_name(db, payload.name)
    if not existing:
        print(f"Ingesting '{payload.name}' into 'postgres' database...")
        res = service.ingest_dataset(db, payload)
        db.commit()
        print(f"Ingestion successful! Dataset ID: {res.dataset.id}")
    else:
        print(f"Dataset already exists in 'postgres' database (ID: {existing.id})")
finally:
    db.close()
