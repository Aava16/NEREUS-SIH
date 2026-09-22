from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob


class ProcessingJobRepository:
    """Repository handling persistence and lookup for asynchronous processing and ingestion jobs."""

    def get_by_id(self, db: Session, job_id: uuid.UUID) -> Optional[ProcessingJob]:
        """Fetch processing job by UUID."""
        stmt = select(ProcessingJob).where(ProcessingJob.id == job_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_jobs(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ProcessingJob]:
        """List processing jobs with optional dataset, type, and status filtering."""
        stmt = select(ProcessingJob)

        if dataset_id:
            stmt = stmt.where(ProcessingJob.dataset_id == dataset_id)
        if job_type:
            stmt = stmt.where(ProcessingJob.job_type == job_type)
        if status:
            stmt = stmt.where(ProcessingJob.status == status)

        stmt = stmt.order_by(ProcessingJob.created_at.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, job_data: Dict[str, Any]) -> ProcessingJob:
        """Create and persist a new processing job."""
        job = ProcessingJob(**job_data)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def update(self, db: Session, job: ProcessingJob, update_data: Dict[str, Any]) -> ProcessingJob:
        """Update existing processing job attributes."""
        for field, value in update_data.items():
            setattr(job, field, value)
        db.commit()
        db.refresh(job)
        return job

    def delete(self, db: Session, job: ProcessingJob) -> None:
        """Delete a processing job record."""
        db.delete(job)
        db.commit()
