import logging
from typing import List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.repositories.dataset import DatasetRepository
from app.schemas.dataset import DatasetCreate, DatasetDetailRead, DatasetFilterParams, DatasetRead, DatasetUpdate

logger = logging.getLogger(__name__)


class DatasetService:
    """Service layer managing business logic and validation for oceanographic datasets."""

    def __init__(self, repository: Optional[DatasetRepository] = None) -> None:
        self.repository = repository or DatasetRepository()

    def get_dataset(self, db: Session, dataset_id: uuid.UUID) -> Dataset:
        """Retrieve dataset by ID or raise 404."""
        dataset = self.repository.get_by_id(db, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{dataset_id}' was not found.",
            )
        return dataset

    def get_dataset_detail(self, db: Session, dataset_id: uuid.UUID) -> DatasetDetailRead:
        """Retrieve dataset with variable count and asset count."""
        dataset = self.get_dataset(db, dataset_id)
        return DatasetDetailRead(
            id=dataset.id,
            name=dataset.name,
            title=dataset.title,
            description=dataset.description,
            source=dataset.source,
            source_uri=dataset.source_uri,
            dataset_type=dataset.dataset_type,
            temporal_start=dataset.temporal_start,
            temporal_end=dataset.temporal_end,
            spatial_extent=dataset.spatial_extent,
            metadata_json=dataset.metadata_json,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            variables_count=len(dataset.variables) if dataset.variables else 0,
            array_assets_count=len(dataset.array_assets) if dataset.array_assets else 0,
        )

    def list_datasets(self, db: Session, filters: DatasetFilterParams) -> List[Dataset]:
        """List datasets applying optional spatial bounding box and metadata filters."""
        bbox: Optional[Tuple[float, float, float, float]] = None
        if all(
            x is not None
            for x in [
                filters.bbox_min_lon,
                filters.bbox_min_lat,
                filters.bbox_max_lon,
                filters.bbox_max_lat,
            ]
        ):
            bbox = (
                filters.bbox_min_lon,  # type: ignore[arg-type]
                filters.bbox_min_lat,  # type: ignore[arg-type]
                filters.bbox_max_lon,  # type: ignore[arg-type]
                filters.bbox_max_lat,  # type: ignore[arg-type]
            )

        try:
            return self.repository.list_datasets(
                db,
                dataset_type=filters.dataset_type,
                source=filters.source,
                temporal_min=filters.temporal_min,
                temporal_max=filters.temporal_max,
                bbox=bbox,
                limit=filters.limit,
                offset=filters.offset,
            )
        except Exception as exc:
            logger.error("Failed to query datasets catalog: %s - %s", type(exc).__name__, exc)
            raise

    def create_dataset(self, db: Session, payload: DatasetCreate) -> Dataset:
        """Validate uniqueness and create a new dataset."""
        existing = self.repository.get_by_name(db, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A dataset with name '{payload.name}' already exists.",
            )

        data = payload.model_dump()
        return self.repository.create(db, data)

    def update_dataset(self, db: Session, dataset_id: uuid.UUID, payload: DatasetUpdate) -> Dataset:
        """Update dataset attributes."""
        dataset = self.get_dataset(db, dataset_id)

        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != dataset.name:
            conflict = self.repository.get_by_name(db, update_data["name"])
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A dataset with name '{update_data['name']}' already exists.",
                )

        return self.repository.update(db, dataset, update_data)

    def delete_dataset(self, db: Session, dataset_id: uuid.UUID) -> None:
        """Delete dataset."""
        dataset = self.get_dataset(db, dataset_id)
        self.repository.delete(db, dataset)
