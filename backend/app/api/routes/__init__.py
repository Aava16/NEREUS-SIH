"""API route modules for NEREUS."""

from app.api.routes.analysis import router as analysis_router
from app.api.routes.array_assets import router as array_assets_router
from app.api.routes.data_delivery import router as data_delivery_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.health import router as health_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.observations import router as observations_router
from app.api.routes.platforms import router as platforms_router
from app.api.routes.processing_jobs import router as processing_jobs_router
from app.api.routes.provenance import router as provenance_router
from app.api.routes.scientific_processing import router as scientific_processing_router
from app.api.routes.validation_runs import router as validation_runs_router
from app.api.routes.variables import router as variables_router

__all__ = [
    "analysis_router",
    "array_assets_router",
    "data_delivery_router",
    "datasets_router",
    "health_router",
    "ingestion_router",
    "observations_router",
    "platforms_router",
    "processing_jobs_router",
    "provenance_router",
    "scientific_processing_router",
    "validation_runs_router",
    "variables_router",
]



