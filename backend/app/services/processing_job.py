import logging
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob
from app.repositories.dataset import DatasetRepository
from app.repositories.processing_job import ProcessingJobRepository
from app.schemas.processing_job import (
    ProcessingJobCreate,
    ProcessingJobFilterParams,
    ProcessingJobUpdate,
)

logger = logging.getLogger(__name__)


class ProcessingJobService:
    """Service layer managing execution lifecycle and querying for processing jobs."""

    def __init__(
        self,
        repository: Optional[ProcessingJobRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
    ) -> None:
        self.repository = repository or ProcessingJobRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()

    def get_job(self, db: Session, job_id: uuid.UUID) -> ProcessingJob:
        """Fetch processing job by ID or raise 404."""
        job = self.repository.get_by_id(db, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing job with ID '{job_id}' was not found.",
            )
        return job

    def list_jobs(self, db: Session, filters: ProcessingJobFilterParams) -> List[ProcessingJob]:
        """List processing jobs matching query filters."""
        if filters.dataset_id and not self.dataset_repo.get_by_id(db, filters.dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{filters.dataset_id}' was not found.",
            )
        return self.repository.list_jobs(
            db,
            dataset_id=filters.dataset_id,
            job_type=filters.job_type,
            status=filters.status,
            limit=filters.limit,
            offset=filters.offset,
        )

    def create_job(self, db: Session, payload: ProcessingJobCreate) -> ProcessingJob:
        """Queue a new processing job with foreign key validation."""
        if payload.dataset_id and not self.dataset_repo.get_by_id(db, payload.dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{payload.dataset_id}' was not found.",
            )
        return self.repository.create(db, payload.model_dump())

    def update_job(self, db: Session, job_id: uuid.UUID, payload: ProcessingJobUpdate) -> ProcessingJob:
        """Update job execution state."""
        job = self.get_job(db, job_id)
        update_data = payload.model_dump(exclude_unset=True)
        return self.repository.update(db, job, update_data)

    def delete_job(self, db: Session, job_id: uuid.UUID) -> None:
        """Delete processing job."""
        job = self.get_job(db, job_id)
        self.repository.delete(db, job)
