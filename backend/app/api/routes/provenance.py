from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.provenance import ProvenanceCreate, ProvenanceRead
from app.services.provenance import ProvenanceService

router = APIRouter(prefix="/provenance", tags=["Provenance & Audit"])
provenance_service = ProvenanceService()


@router.get(
    "",
    response_model=List[ProvenanceRead],
    summary="List Provenance Records",
    description="Retrieve scientific provenance and data operation audit records.",
)
def list_records(
    dataset_id: Optional[uuid.UUID] = Query(None, description="Filter by parent dataset ID"),
    action: Optional[str] = Query(None, description="Filter by action type (e.g., INGESTION, QC_RUN)"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[ProvenanceRead]:
    """List provenance audit records."""
    return provenance_service.list_records(  # type: ignore[return-value]
        db,
        dataset_id=dataset_id,
        action=action,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ProvenanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record Provenance Event",
    description="Append a scientific lineage or audit log event for a dataset.",
)
def create_record(
    payload: ProvenanceCreate,
    db: Session = Depends(get_db),
) -> ProvenanceRead:
    """Record a provenance event."""
    return provenance_service.create_record(db, payload)  # type: ignore[return-value]


@router.get(
    "/{record_id}",
    response_model=ProvenanceRead,
    summary="Get Provenance Record Details",
    description="Retrieve details and execution parameters for a provenance audit record.",
)
def get_record(
    record_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ProvenanceRead:
    """Fetch provenance record by ID."""
    return provenance_service.get_record(db, record_id)  # type: ignore[return-value]
