from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class PlatformBase(BaseModel):
    """Base attributes for an ocean observation platform or instrument."""

    name: str = Field(..., max_length=100, description="Unique instrument code or WMO ID")
    platform_type: str = Field(
        ...,
        max_length=50,
        description="Type (e.g., ARGO_FLOAT, UNDERWATER_GLIDER, CTD_STATION, MOORED_BUOY, RESEARCH_VESSEL)",
    )
    operator: Optional[str] = Field(None, max_length=150, description="Deploying institute or principal investigator")
    description: Optional[str] = Field(None, description="Platform summary or deployment specifications")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Sensors, calibration, telemetry data")


class PlatformCreate(PlatformBase):
    """Schema for creating a platform."""

    pass


class PlatformUpdate(BaseModel):
    """Schema for updating platform details."""

    name: Optional[str] = Field(None, max_length=100)
    platform_type: Optional[str] = Field(None, max_length=50)
    operator: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class PlatformRead(PlatformBase):
    """Schema for returning platform metadata."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformFilterParams(BaseModel):
    """Query parameters for filtering platforms."""

    platform_type: Optional[str] = None
    operator: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
