from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class ProvenanceBase(BaseModel):
    """Base schema for scientific provenance and dataset lifecycle audit log."""

    dataset_id: uuid.UUID = Field(..., description="Parent dataset ID")
    action: str = Field(..., max_length=100, description="Action (INGESTION, QC_RUN, ANOMALY_CALCULATION, DEPRECATION)")
    source: Optional[str] = Field(None, max_length=255, description="Input data file or upstream pipeline trigger")
    actor: Optional[str] = Field(None, max_length=150, description="User, service agent, or pipeline worker")
    timestamp: datetime = Field(default_factory=get_utc_now, description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Audit log details, parameters, error traces")



class ProvenanceCreate(ProvenanceBase):
    """Schema for creating a provenance record."""

    pass


class ProvenanceRead(ProvenanceBase):
    """Schema for reading a provenance record."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
