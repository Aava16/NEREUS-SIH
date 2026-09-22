import logging
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.health import HealthRepository
from app.schemas.health import DatabaseHealthResponse, HealthResponse

logger = logging.getLogger(__name__)


class HealthService:
    """Service layer coordinating application and database health checks."""

    def __init__(self, repository: HealthRepository | None = None) -> None:
        self.repository = repository or HealthRepository()
        self.settings = get_settings()

    def get_api_health(self) -> HealthResponse:
        """Return basic process health status."""
        return HealthResponse(
            status="ok",
            app=self.settings.app_name,
            version=self.settings.app_version,
        )

    def get_database_health(self, db: Session) -> DatabaseHealthResponse:
        """Validate live database connectivity via repository probe."""
        try:
            db_probe = self.repository.ping_database(db)
            return DatabaseHealthResponse(
                status="ok",
                database=db_probe["database_name"],
                connected=db_probe["is_alive"],
                latency_ms=db_probe["latency_ms"],
            )
        except SQLAlchemyError as exc:
            logger.error("Database health check probe failed: %s", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service is unavailable",
            ) from None
        except Exception as exc:
            logger.error("Unexpected error during database health check: %s", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database health verification failed",
            ) from None
