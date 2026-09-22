from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.validation_run import ValidationRun
from app.schemas.geometry import geometry_to_shape, shape_to_wkb


class ValidationRunRepository:
    """Repository handling persistence and lookup for scientific validation verification runs."""

    def get_by_id(self, db: Session, run_id: uuid.UUID) -> Optional[ValidationRun]:
        """Fetch validation run by UUID."""
        stmt = select(ValidationRun).where(ValidationRun.id == run_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_runs(
        self,
        db: Session,
        model_dataset_id: Optional[uuid.UUID] = None,
        variable_id: Optional[uuid.UUID] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ValidationRun]:
        """List validation runs with optional model dataset and variable filtering."""
        stmt = select(ValidationRun)

        if model_dataset_id:
            stmt = stmt.where(ValidationRun.model_dataset_id == model_dataset_id)
        if variable_id:
            stmt = stmt.where(ValidationRun.variable_id == variable_id)
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            bbox_geom = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
            stmt = stmt.where(func.ST_Intersects(ValidationRun.spatial_scope_geom, bbox_geom))

        stmt = stmt.order_by(ValidationRun.created_at.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, run_data: Dict[str, Any]) -> ValidationRun:
        """Create and persist a validation run."""
        raw_spatial = run_data.pop("spatial_scope_geom", None)
        shape_geom = geometry_to_shape(raw_spatial) if raw_spatial else None
        spatial_wkb = shape_to_wkb(shape_geom) if shape_geom else None

        run = ValidationRun(
            **run_data,
            spatial_scope_geom=spatial_wkb,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def delete(self, db: Session, run: ValidationRun) -> None:
        """Delete a validation run record."""
        db.delete(run)
        db.commit()
