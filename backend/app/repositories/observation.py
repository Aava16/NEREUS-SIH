from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.schemas.geometry import geometry_to_shape, shape_to_wkb


class ObservationRepository:
    """Repository handling in-situ observation point persistence and spatial/depth filtering."""

    def get_by_id(self, db: Session, observation_id: uuid.UUID) -> Optional[Observation]:
        """Fetch an individual observation by UUID."""
        stmt = select(Observation).where(Observation.id == observation_id)
        return db.execute(stmt).scalar_one_or_none()

    def list_observations(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        variable_id: Optional[uuid.UUID] = None,
        platform_id: Optional[uuid.UUID] = None,
        temporal_min: Optional[Any] = None,
        temporal_max: Optional[Any] = None,
        depth_min: Optional[float] = None,
        depth_max: Optional[float] = None,
        quality_flag: Optional[int] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Observation]:
        """Query observations with spatio-temporal and vertical depth bounding criteria."""
        stmt = select(Observation)

        if dataset_id:
            stmt = stmt.where(Observation.dataset_id == dataset_id)
        if variable_id:
            stmt = stmt.where(Observation.variable_id == variable_id)
        if platform_id:
            stmt = stmt.where(Observation.platform_id == platform_id)
        if temporal_min:
            stmt = stmt.where(Observation.observed_at >= temporal_min)
        if temporal_max:
            stmt = stmt.where(Observation.observed_at <= temporal_max)
        if depth_min is not None:
            stmt = stmt.where(Observation.depth_m >= depth_min)
        if depth_max is not None:
            stmt = stmt.where(Observation.depth_m <= depth_max)
        if quality_flag is not None:
            stmt = stmt.where(Observation.quality_flag == quality_flag)
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            bbox_geom = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
            stmt = stmt.where(func.ST_Intersects(Observation.geometry, bbox_geom))

        stmt = stmt.order_by(Observation.observed_at.desc(), Observation.depth_m.asc().nulls_last())
        stmt = stmt.offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, observation_data: Dict[str, Any]) -> Observation:
        """Create and persist a single observation point."""
        raw_geom = observation_data.pop("geometry", None)
        shape_geom = geometry_to_shape(raw_geom)
        geom_wkb = shape_to_wkb(shape_geom)

        observation = Observation(
            **observation_data,
            geometry=geom_wkb,
        )
        db.add(observation)
        db.commit()
        db.refresh(observation)
        return observation

    def bulk_create(self, db: Session, observations_data: List[Dict[str, Any]]) -> List[Observation]:
        """Bulk create and persist multiple observation points in a single transaction."""
        objects = []
        for item in observations_data:
            item_copy = dict(item)
            raw_geom = item_copy.pop("geometry", None)
            shape_geom = geometry_to_shape(raw_geom)
            geom_wkb = shape_to_wkb(shape_geom)

            obj = Observation(
                **item_copy,
                geometry=geom_wkb,
            )
            objects.append(obj)

        db.add_all(objects)
        db.commit()
        for obj in objects:
            db.refresh(obj)
        return objects

    def delete(self, db: Session, observation: Observation) -> None:
        """Delete an observation record."""
        db.delete(observation)
        db.commit()
