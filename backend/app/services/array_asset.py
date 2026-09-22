import logging
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.array_asset import ArrayAsset
from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.array_asset import ArrayAssetCreate

logger = logging.getLogger(__name__)


class ArrayAssetService:
    """Service layer managing scientific multidimensional array asset registration."""

    def __init__(
        self,
        repository: Optional[ArrayAssetRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
    ) -> None:
        self.repository = repository or ArrayAssetRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()

    def get_asset(self, db: Session, asset_id: uuid.UUID) -> ArrayAsset:
        """Fetch array asset by ID or raise 404."""
        asset = self.repository.get_by_id(db, asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Array asset with ID '{asset_id}' was not found.",
            )
        return asset

    def list_assets(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        storage_format: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ArrayAsset]:
        """List array assets with optional dataset and format filters."""
        if dataset_id and not self.dataset_repo.get_by_id(db, dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent dataset with ID '{dataset_id}' was not found.",
            )
        return self.repository.list_assets(
            db,
            dataset_id=dataset_id,
            storage_format=storage_format,
            limit=limit,
            offset=offset,
        )

    def create_asset(self, db: Session, payload: ArrayAssetCreate) -> ArrayAsset:
        """Validate parent dataset and create a new array asset entry."""
        dataset = self.dataset_repo.get_by_id(db, payload.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent dataset with ID '{payload.dataset_id}' was not found.",
            )
        return self.repository.create(db, payload.model_dump())

    def delete_asset(self, db: Session, asset_id: uuid.UUID) -> None:
        """Delete an array asset by ID."""
        asset = self.get_asset(db, asset_id)
        self.repository.delete(db, asset)
