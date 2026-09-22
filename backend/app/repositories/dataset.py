from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.dataset import Dataset
from app.schemas.geometry import geometry_to_shape, shape_to_wkb


class DatasetRepository:
    """Repository handling persistence and spatial/temporal queries for Datasets."""

    def get_by_id(self, db: Session, dataset_id: uuid.UUID) -> Optional[Dataset]:
        """Fetch a dataset by its unique primary key UUID."""
        stmt = (
            select(Dataset)
            .options(selectinload(Dataset.variables), selectinload(Dataset.array_assets))
            .where(Dataset.id == dataset_id)
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, db: Session, name: str) -> Optional[Dataset]:
        """Fetch a dataset by its unique machine code name."""
        stmt = select(Dataset).where(Dataset.name == name)
        return db.execute(stmt).scalar_one_or_none()

    def list_datasets(
        self,
        db: Session,
        dataset_type: Optional[str] = None,
        source: Optional[str] = None,
        temporal_min: Optional[Any] = None,
        temporal_max: Optional[Any] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dataset]:
        """List datasets with optional spatial bbox, temporal, and type filtering."""
        stmt = select(Dataset)

        if dataset_type:
            stmt = stmt.where(Dataset.dataset_type == dataset_type)
        if source:
            stmt = stmt.where(Dataset.source.ilike(f"%{source}%"))
        if temporal_min:
            stmt = stmt.where(
                (Dataset.temporal_end >= temporal_min) | (Dataset.temporal_end.is_(None))
            )
        if temporal_max:
            stmt = stmt.where(
                (Dataset.temporal_start <= temporal_max) | (Dataset.temporal_start.is_(None))
            )
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            bbox_geom = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
            stmt = stmt.where(func.ST_Intersects(Dataset.spatial_extent, bbox_geom))

        stmt = stmt.order_by(Dataset.created_at.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, dataset_data: Dict[str, Any]) -> Dataset:
        """Create and persist a new dataset entity."""
        raw_spatial = dataset_data.pop("spatial_extent", None)
        shape_geom = geometry_to_shape(raw_spatial) if raw_spatial else None
        spatial_wkb = shape_to_wkb(shape_geom) if shape_geom else None

        dataset = Dataset(
            **dataset_data,
            spatial_extent=spatial_wkb,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    def update(self, db: Session, dataset: Dataset, update_data: Dict[str, Any]) -> Dataset:
        """Update existing dataset attributes."""
        if "spatial_extent" in update_data:
            raw_spatial = update_data.pop("spatial_extent")
            shape_geom = geometry_to_shape(raw_spatial) if raw_spatial else None
            dataset.spatial_extent = shape_to_wkb(shape_geom) if shape_geom else None

        for field, value in update_data.items():
            setattr(dataset, field, value)

        db.commit()
        db.refresh(dataset)
        return dataset

    def delete(self, db: Session, dataset: Dataset) -> None:
        """Delete a dataset and cascade to related children."""
        db.delete(dataset)
        db.commit()
