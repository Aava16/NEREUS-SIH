from fastapi import APIRouter

from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)

# Versioned API Router for future domain resources
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router)
