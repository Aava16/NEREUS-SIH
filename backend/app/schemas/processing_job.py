from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class ProcessingJobBase(BaseModel):
    """Base attributes for an asynchronous scientific processing or ingestion job."""

    dataset_id: Optional[uuid.UUID] = Field(None, description="Target or parent dataset ID")
    job_type: str = Field(
        ...,
        max_length=50,
        description="Type: DATASET_INGESTION, QUALITY_VALIDATION, COORDINATE_NORMALIZATION, DERIVED_ANOMALY_COMPUTE, SPATIAL_INDEXING",
    )
    status: str = Field(
        default="QUEUED",
        max_length=50,
        description="Status: QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED",
    )
    initiated_by: Optional[str] = Field(None, max_length=128, description="User, pipeline, or cron worker ID")
    error_message: Optional[str] = Field(None, description="Diagnostic error trace if failed")
    logs_uri: Optional[str] = Field(None, max_length=512, description="Log file URI")
    job_metadata: Dict[str, Any] = Field(default_factory=dict, description="Job parameters, execution statistics")


class ProcessingJobCreate(ProcessingJobBase):
    """Schema for queueing a new processing job."""

    pass


class ProcessingJobUpdate(BaseModel):
    """Schema for updating processing job status, error, and timestamps."""

    status: Optional[str] = Field(None, max_length=50)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    logs_uri: Optional[str] = Field(None, max_length=512)
    job_metadata: Optional[Dict[str, Any]] = None


class ProcessingJobRead(ProcessingJobBase):
    """Schema for returning processing job status."""

    id: uuid.UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingJobFilterParams(BaseModel):
    """Query parameters for filtering processing jobs."""

    dataset_id: Optional[uuid.UUID] = None
    job_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
