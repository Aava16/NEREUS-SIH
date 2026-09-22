import logging
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.provenance import Provenance
from app.repositories.dataset import DatasetRepository
from app.repositories.provenance import ProvenanceRepository
from app.schemas.provenance import ProvenanceCreate

logger = logging.getLogger(__name__)


class ProvenanceService:
    """Service layer managing dataset lineage, auditing, and processing logs."""

    def __init__(
        self,
        repository: Optional[ProvenanceRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
    ) -> None:
        self.repository = repository or ProvenanceRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()

    def get_record(self, db: Session, record_id: uuid.UUID) -> Provenance:
        """Fetch provenance record by ID or raise 404."""
        record = self.repository.get_by_id(db, record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provenance record with ID '{record_id}' was not found.",
            )
        return record

    def list_records(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Provenance]:
        """List provenance records with optional dataset and action filters."""
        if dataset_id and not self.dataset_repo.get_by_id(db, dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent dataset with ID '{dataset_id}' was not found.",
            )
        return self.repository.list_records(
            db,
            dataset_id=dataset_id,
            action=action,
            limit=limit,
            offset=offset,
        )

    def create_record(self, db: Session, payload: ProvenanceCreate) -> Provenance:
        """Validate parent dataset and create a new provenance log entry."""
        dataset = self.dataset_repo.get_by_id(db, payload.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent dataset with ID '{payload.dataset_id}' was not found.",
            )
        return self.repository.create(db, payload.model_dump())
