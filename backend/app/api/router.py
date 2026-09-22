from fastapi import APIRouter

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

api_router = APIRouter()
api_router.include_router(health_router)

# Versioned API Router for canonical domain resources
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router)
v1_router.include_router(datasets_router)
v1_router.include_router(data_delivery_router)
v1_router.include_router(variables_router)
v1_router.include_router(platforms_router)
v1_router.include_router(observations_router)
v1_router.include_router(array_assets_router)
v1_router.include_router(provenance_router)
v1_router.include_router(processing_jobs_router)
v1_router.include_router(validation_runs_router)
v1_router.include_router(ingestion_router)
v1_router.include_router(scientific_processing_router)
v1_router.include_router(analysis_router)




