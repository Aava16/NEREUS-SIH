from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provenance import Provenance


class ProvenanceRepository:
    """Repository handling persistence and lookup for dataset audit & provenance logs."""

    def get_by_id(self, db: Session, record_id: uuid.UUID) -> Optional[Provenance]:
        """Fetch a provenance record by UUID."""
        stmt = select(Provenance).where(Provenance.id == record_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_records(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Provenance]:
        """List provenance logs with optional dataset and action filtering."""
        stmt = select(Provenance)

        if dataset_id:
            stmt = stmt.where(Provenance.dataset_id == dataset_id)
        if action:
            stmt = stmt.where(Provenance.action == action)

        stmt = stmt.order_by(Provenance.timestamp.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, record_data: Dict[str, Any]) -> Provenance:
        """Create and persist a new provenance log entry."""
        record = Provenance(**record_data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
