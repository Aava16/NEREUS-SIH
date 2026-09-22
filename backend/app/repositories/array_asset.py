from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.array_asset import ArrayAsset


class ArrayAssetRepository:
    """Repository handling persistence and lookup for scientific multidimensional array asset metadata."""

    def get_by_id(self, db: Session, asset_id: uuid.UUID) -> Optional[ArrayAsset]:
        """Fetch an array asset by UUID."""
        stmt = select(ArrayAsset).where(ArrayAsset.id == asset_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_assets(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        storage_format: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ArrayAsset]:
        """List array assets with optional dataset and format filtering."""
        stmt = select(ArrayAsset)

        if dataset_id:
            stmt = stmt.where(ArrayAsset.dataset_id == dataset_id)
        if storage_format:
            stmt = stmt.where(ArrayAsset.storage_format == storage_format)

        stmt = stmt.order_by(ArrayAsset.created_at.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, asset_data: Dict[str, Any]) -> ArrayAsset:
        """Create and persist an array asset entity."""
        asset = ArrayAsset(**asset_data)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def delete(self, db: Session, asset: ArrayAsset) -> None:
        """Delete an array asset."""
        db.delete(asset)
        db.commit()
