import logging
from typing import List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.repositories.dataset import DatasetRepository
from app.repositories.observation import ObservationRepository
from app.repositories.platform import PlatformRepository
from app.repositories.variable import VariableRepository
from app.schemas.observation import (
    ObservationBulkCreate,
    ObservationCreate,
    ObservationFilterParams,
)

logger = logging.getLogger(__name__)


class ObservationService:
    """Service layer managing validation and ingestion of discrete in-situ ocean observations."""

    def __init__(
        self,
        repository: Optional[ObservationRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
        variable_repo: Optional[VariableRepository] = None,
        platform_repo: Optional[PlatformRepository] = None,
    ) -> None:
        self.repository = repository or ObservationRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.variable_repo = variable_repo or VariableRepository()
        self.platform_repo = platform_repo or PlatformRepository()

    def get_observation(self, db: Session, observation_id: uuid.UUID) -> Observation:
        """Fetch observation by ID or raise 404."""
        observation = self.repository.get_by_id(db, observation_id)
        if not observation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observation with ID '{observation_id}' was not found.",
            )
        return observation

    def list_observations(self, db: Session, filters: ObservationFilterParams) -> List[Observation]:
        """Query observation records matching spatio-temporal and vertical depth criteria."""
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

        return self.repository.list_observations(
            db,
            dataset_id=filters.dataset_id,
            variable_id=filters.variable_id,
            platform_id=filters.platform_id,
            temporal_min=filters.temporal_min,
            temporal_max=filters.temporal_max,
            depth_min=filters.depth_min,
            depth_max=filters.depth_max,
            quality_flag=filters.quality_flag,
            bbox=bbox,
            limit=filters.limit,
            offset=filters.offset,
        )

    def _validate_references(
        self,
        db: Session,
        dataset_id: uuid.UUID,
        variable_id: uuid.UUID,
        platform_id: Optional[uuid.UUID],
    ) -> None:
        """Verify foreign key integrity for observation associations."""
        if not self.dataset_repo.get_by_id(db, dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated dataset with ID '{dataset_id}' was not found.",
            )
        if not self.variable_repo.get_by_id(db, variable_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated variable with ID '{variable_id}' was not found.",
            )
        if platform_id and not self.platform_repo.get_by_id(db, platform_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated platform with ID '{platform_id}' was not found.",
            )

    def create_observation(self, db: Session, payload: ObservationCreate) -> Observation:
        """Create a single observation point."""
        self._validate_references(db, payload.dataset_id, payload.variable_id, payload.platform_id)
        return self.repository.create(db, payload.model_dump())

    def bulk_create_observations(self, db: Session, payload: ObservationBulkCreate) -> List[Observation]:
        """Bulk create observation points with validated references."""
        if not payload.observations:
            return []

        # Validate distinct dataset, variable, and platform references
        datasets_seen = {item.dataset_id for item in payload.observations}
        variables_seen = {item.variable_id for item in payload.observations}
        platforms_seen = {item.platform_id for item in payload.observations if item.platform_id}

        for ds_id in datasets_seen:
            if not self.dataset_repo.get_by_id(db, ds_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset with ID '{ds_id}' was not found.",
                )
        for var_id in variables_seen:
            if not self.variable_repo.get_by_id(db, var_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variable with ID '{var_id}' was not found.",
                )
        for plat_id in platforms_seen:
            if not self.platform_repo.get_by_id(db, plat_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Platform with ID '{plat_id}' was not found.",
                )

        items_data = [item.model_dump() for item in payload.observations]
        return self.repository.bulk_create(db, items_data)

    def delete_observation(self, db: Session, observation_id: uuid.UUID) -> None:
        """Delete an observation record by ID."""
        observation = self.get_observation(db, observation_id)
        self.repository.delete(db, observation)
