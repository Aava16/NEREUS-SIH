from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = BACKEND_DIR.parent
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _initialize_database_and_demo_dataset() -> None:
    """Non-destructive startup initialization ensuring schema migrations and demo dataset."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        logger.info("Verifying/applying database migrations to head...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database schema is up-to-date.")
    except Exception as exc:
        logger.warning("Alembic auto-migration notice: %s", exc)

    try:
        import json
        from app.db.session import SessionLocal
        from app.repositories.dataset import DatasetRepository
        from app.schemas.ingestion import DatasetIngestionRequest
        from app.services.ingestion import IngestionService

        db = SessionLocal()
        try:
            repo = DatasetRepository()
            existing = repo.get_by_name(db, "copernicus-multiobs-arabian-sea-2024")
            if not existing:
                logger.info("Demo dataset not found in database; initializing automatic ingestion...")
                manifest_path = WORKSPACE_DIR / "data" / "manifests" / "copernicus_multiobs_glo_phy_tsuv_manifest.json"
                nc_path = WORKSPACE_DIR / "data" / "processed" / "copernicus_multiobs_arabian_sea_2024.nc"

                if not nc_path.exists():
                    try:
                        from generate_copernicus_demo_asset import generate_copernicus_dataset
                        generate_copernicus_dataset(str(nc_path))
                    except Exception as gen_exc:
                        logger.warning("Could not auto-generate NetCDF asset: %s", gen_exc)

                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    manifest_data["array_assets"][0]["uri"] = str(nc_path.resolve())
                    payload = DatasetIngestionRequest.model_validate(manifest_data)
                    service = IngestionService()
                    service.ingest_dataset(db, payload)
                    db.commit()
                    logger.info("Copernicus demo dataset successfully registered in database.")
            else:
                logger.info("Copernicus demo dataset verified in catalog.")
        finally:
            db.close()
    except Exception as ingest_exc:
        logger.warning("Demo dataset initialization notice: %s", ingest_exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for non-destructive startup & graceful shutdown."""
    setup_logging(debug=settings.debug)
    logger.info("Initializing %s v%s...", settings.app_name, settings.app_version)
    logger.info("Configuration loaded from backend environment.")
    _initialize_database_and_demo_dataset()
    yield
    logger.info("Shutting down %s...", settings.app_name)


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(api_router)
    app.include_router(v1_router)

    return app


app = create_application()
