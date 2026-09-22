from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.platform import Platform


class PlatformRepository:
    """Repository handling persistence and lookup for ocean observation platforms."""

    def get_by_id(self, db: Session, platform_id: uuid.UUID) -> Optional[Platform]:
        """Fetch a platform by its unique UUID."""
        stmt = select(Platform).where(Platform.id == platform_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, db: Session, name: str) -> Optional[Platform]:
        """Fetch a platform by its unique instrument code or name."""
        stmt = select(Platform).where(Platform.name == name)
        return db.execute(stmt).scalar_one_or_none()

    def list_platforms(
        self,
        db: Session,
        platform_type: Optional[str] = None,
        operator: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Platform]:
        """List platforms with optional type and operator filters."""
        stmt = select(Platform)

        if platform_type:
            stmt = stmt.where(Platform.platform_type == platform_type)
        if operator:
            stmt = stmt.where(Platform.operator.ilike(f"%{operator}%"))

        stmt = stmt.order_by(Platform.created_at.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, platform_data: Dict[str, Any]) -> Platform:
        """Create and persist a new platform entity."""
        platform = Platform(**platform_data)
        db.add(platform)
        db.commit()
        db.refresh(platform)
        return platform

    def update(self, db: Session, platform: Platform, update_data: Dict[str, Any]) -> Platform:
        """Update existing platform attributes."""
        for field, value in update_data.items():
            setattr(platform, field, value)
        db.commit()
        db.refresh(platform)
        return platform

    def delete(self, db: Session, platform: Platform) -> None:
        """Delete a platform entity."""
        db.delete(platform)
        db.commit()
