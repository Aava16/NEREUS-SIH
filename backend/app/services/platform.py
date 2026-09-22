import logging
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.platform import Platform
from app.repositories.platform import PlatformRepository
from app.schemas.platform import PlatformCreate, PlatformFilterParams, PlatformUpdate

logger = logging.getLogger(__name__)


class PlatformService:
    """Service layer managing business logic and validation for ocean observation platforms."""

    def __init__(self, repository: Optional[PlatformRepository] = None) -> None:
        self.repository = repository or PlatformRepository()

    def get_platform(self, db: Session, platform_id: uuid.UUID) -> Platform:
        """Fetch platform by ID or raise 404."""
        platform = self.repository.get_by_id(db, platform_id)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform with ID '{platform_id}' was not found.",
            )
        return platform

    def list_platforms(self, db: Session, filters: PlatformFilterParams) -> List[Platform]:
        """List platforms with optional filters."""
        return self.repository.list_platforms(
            db,
            platform_type=filters.platform_type,
            operator=filters.operator,
            limit=filters.limit,
            offset=filters.offset,
        )

    def create_platform(self, db: Session, payload: PlatformCreate) -> Platform:
        """Validate uniqueness and create a new platform."""
        existing = self.repository.get_by_name(db, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Platform with name/code '{payload.name}' already exists.",
            )
        return self.repository.create(db, payload.model_dump())

    def update_platform(self, db: Session, platform_id: uuid.UUID, payload: PlatformUpdate) -> Platform:
        """Update platform attributes."""
        platform = self.get_platform(db, platform_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != platform.name:
            conflict = self.repository.get_by_name(db, update_data["name"])
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Platform with name/code '{update_data['name']}' already exists.",
                )

        return self.repository.update(db, platform, update_data)

    def delete_platform(self, db: Session, platform_id: uuid.UUID) -> None:
        """Delete platform by ID."""
        platform = self.get_platform(db, platform_id)
        self.repository.delete(db, platform)
