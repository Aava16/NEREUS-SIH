from datetime import datetime, timezone
from pydantic import BaseModel, Field


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class HealthResponse(BaseModel):
    """Schema for basic API health status response."""

    status: str = Field(default="ok", description="Process health status")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=get_utc_now, description="Server UTC timestamp")


class DatabaseHealthResponse(BaseModel):
    """Schema for database connectivity and health response."""

    status: str = Field(default="ok", description="Database health status")
    database: str = Field(..., description="Target database name")
    connected: bool = Field(default=True, description="Database connection status")
    latency_ms: float = Field(..., description="Query execution latency in milliseconds")
    timestamp: datetime = Field(default_factory=get_utc_now, description="Server UTC timestamp")
