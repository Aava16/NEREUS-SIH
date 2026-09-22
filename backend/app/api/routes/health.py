from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import DatabaseHealthResponse, HealthResponse
from app.services.health import HealthService

router = APIRouter(tags=["Health"])
health_service = HealthService()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Process Health Check",
    description="Returns status indicating that the FastAPI service process is operational.",
)
def check_api_health() -> HealthResponse:
    """Return process health status."""
    return health_service.get_api_health()


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Check",
    description="Executes a live query to verify PostgreSQL and PostGIS database connectivity.",
)
def check_database_health(db: Session = Depends(get_db)) -> DatabaseHealthResponse:
    """Validate database connectivity and measure query latency."""
    return health_service.get_database_health(db)
