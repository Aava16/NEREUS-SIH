"""Pydantic data schemas package."""

from app.schemas.health import DatabaseHealthResponse, HealthResponse

__all__ = ["HealthResponse", "DatabaseHealthResponse"]
