from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.observation import (
    ObservationBulkCreate,
    ObservationCreate,
    ObservationFilterParams,
    ObservationRead,
)
from app.services.observation import ObservationService

router = APIRouter(prefix="/observations", tags=["Observations"])
observation_service = ObservationService()


@router.get(
    "",
    response_model=List[ObservationRead],
    summary="Query In-Situ Observations",
    description="Retrieve observation points with spatial bounding box, vertical depth range, and temporal filtering.",
)
def list_observations(
    filters: ObservationFilterParams = Depends(),
    db: Session = Depends(get_db),
) -> List[ObservationRead]:
    """Query discrete observation points."""
    return observation_service.list_observations(db, filters)  # type: ignore[return-value]


@router.post(
    "",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Single Observation",
    description="Ingest a single discrete ocean in-situ measurement with GeoJSON coordinate point.",
)
def create_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
) -> ObservationRead:
    """Create a single observation point."""
    return observation_service.create_observation(db, payload)  # type: ignore[return-value]


@router.post(
    "/bulk",
    response_model=List[ObservationRead],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Ingest Observations",
    description="Ingest up to 1000 in-situ observation points atomically in a single transaction.",
)
def bulk_create_observations(
    payload: ObservationBulkCreate,
    db: Session = Depends(get_db),
) -> List[ObservationRead]:
    """Bulk ingest observation records."""
    return observation_service.bulk_create_observations(db, payload)  # type: ignore[return-value]


@router.get(
    "/{observation_id}",
    response_model=ObservationRead,
    summary="Get Observation Details",
    description="Fetch a specific in-situ measurement point by ID.",
)
def get_observation(
    observation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ObservationRead:
    """Fetch observation point by ID."""
    return observation_service.get_observation(db, observation_id)  # type: ignore[return-value]


@router.delete(
    "/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Observation",
    description="Delete an observation point by ID.",
)
def delete_observation(
    observation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an observation point by ID."""
    observation_service.delete_observation(db, observation_id)
