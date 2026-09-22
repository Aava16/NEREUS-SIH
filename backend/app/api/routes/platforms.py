from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.platform import (
    PlatformCreate,
    PlatformFilterParams,
    PlatformRead,
    PlatformUpdate,
)
from app.services.platform import PlatformService

router = APIRouter(prefix="/platforms", tags=["Platforms"])
platform_service = PlatformService()


@router.get(
    "",
    response_model=List[PlatformRead],
    summary="List Observation Platforms",
    description="Retrieve observation instruments and platforms (ARGO floats, gliders, moored buoys, CTD stations).",
)
def list_platforms(
    filters: PlatformFilterParams = Depends(),
    db: Session = Depends(get_db),
) -> List[PlatformRead]:
    """List observation platforms matching filter criteria."""
    return platform_service.list_platforms(db, filters)  # type: ignore[return-value]


@router.post(
    "",
    response_model=PlatformRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Observation Platform",
    description="Register an in-situ ocean observation platform or deployment instrument.",
)
def create_platform(
    payload: PlatformCreate,
    db: Session = Depends(get_db),
) -> PlatformRead:
    """Create a new platform."""
    return platform_service.create_platform(db, payload)  # type: ignore[return-value]


@router.get(
    "/{platform_id}",
    response_model=PlatformRead,
    summary="Get Platform Details",
    description="Retrieve details and telemetry configuration for a platform.",
)
def get_platform(
    platform_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> PlatformRead:
    """Fetch platform by ID."""
    return platform_service.get_platform(db, platform_id)  # type: ignore[return-value]


@router.patch(
    "/{platform_id}",
    response_model=PlatformRead,
    summary="Update Platform",
    description="Update metadata or operator information for a platform.",
)
def update_platform(
    platform_id: uuid.UUID,
    payload: PlatformUpdate,
    db: Session = Depends(get_db),
) -> PlatformRead:
    """Update platform attributes."""
    return platform_service.update_platform(db, platform_id, payload)  # type: ignore[return-value]


@router.delete(
    "/{platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Platform",
    description="Delete an observation platform record.",
)
def delete_platform(
    platform_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a platform by ID."""
    platform_service.delete_platform(db, platform_id)
