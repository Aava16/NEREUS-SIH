from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.processing_job import (
    ProcessingJobCreate,
    ProcessingJobFilterParams,
    ProcessingJobRead,
    ProcessingJobUpdate,
)
from app.services.processing_job import ProcessingJobService

router = APIRouter(prefix="/processing-jobs", tags=["Processing Jobs"])
job_service = ProcessingJobService()


@router.get(
    "",
    response_model=List[ProcessingJobRead],
    summary="List Processing Jobs",
    description="Retrieve processing, ingestion, and validation job executions.",
)
def list_jobs(
    filters: ProcessingJobFilterParams = Depends(),
    db: Session = Depends(get_db),
) -> List[ProcessingJobRead]:
    """List processing jobs matching filter parameters."""
    return job_service.list_jobs(db, filters)  # type: ignore[return-value]


@router.post(
    "",
    response_model=ProcessingJobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Queue Processing Job",
    description="Queue an asynchronous scientific ingestion, validation, or anomaly compute task.",
)
def create_job(
    payload: ProcessingJobCreate,
    db: Session = Depends(get_db),
) -> ProcessingJobRead:
    """Queue a processing job."""
    return job_service.create_job(db, payload)  # type: ignore[return-value]


@router.get(
    "/{job_id}",
    response_model=ProcessingJobRead,
    summary="Get Processing Job Status",
    description="Retrieve status and diagnostic logs for a specific job.",
)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ProcessingJobRead:
    """Fetch processing job by ID."""
    return job_service.get_job(db, job_id)  # type: ignore[return-value]


@router.patch(
    "/{job_id}",
    response_model=ProcessingJobRead,
    summary="Update Processing Job Status",
    description="Update processing job status, error traces, and timestamps.",
)
def update_job(
    job_id: uuid.UUID,
    payload: ProcessingJobUpdate,
    db: Session = Depends(get_db),
) -> ProcessingJobRead:
    """Update processing job."""
    return job_service.update_job(db, job_id, payload)  # type: ignore[return-value]


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Processing Job",
    description="Delete a processing job record.",
)
def delete_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a processing job by ID."""
    job_service.delete_job(db, job_id)
