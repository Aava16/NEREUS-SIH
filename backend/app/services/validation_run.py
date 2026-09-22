import logging
import math
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
import numpy as np
from sqlalchemy.orm import Session

from app.models.validation_run import ValidationRun
from app.repositories.dataset import DatasetRepository
from app.repositories.validation_run import ValidationRunRepository
from app.repositories.variable import VariableRepository
from app.schemas.validation_run import (
    ValidationComputeRequest,
    ValidationRunCreate,
    ValidationRunFilterParams,
)

logger = logging.getLogger(__name__)


class ValidationRunService:
    """Service layer managing scientific verification metrics comparing model forecasts against observations."""

    def __init__(
        self,
        repository: Optional[ValidationRunRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
        variable_repo: Optional[VariableRepository] = None,
    ) -> None:
        self.repository = repository or ValidationRunRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.variable_repo = variable_repo or VariableRepository()

    def get_run(self, db: Session, run_id: uuid.UUID) -> ValidationRun:
        """Fetch validation run by ID or raise 404."""
        run = self.repository.get_by_id(db, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation run with ID '{run_id}' was not found.",
            )
        return run

    def list_runs(self, db: Session, filters: ValidationRunFilterParams) -> List[ValidationRun]:
        """List validation runs with optional filters."""
        if filters.model_dataset_id and not self.dataset_repo.get_by_id(db, filters.model_dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model dataset with ID '{filters.model_dataset_id}' was not found.",
            )
        if filters.variable_id and not self.variable_repo.get_by_id(db, filters.variable_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable with ID '{filters.variable_id}' was not found.",
            )
        return self.repository.list_runs(
            db,
            model_dataset_id=filters.model_dataset_id,
            variable_id=filters.variable_id,
            limit=filters.limit,
            offset=filters.offset,
        )

    def create_run(self, db: Session, payload: ValidationRunCreate) -> ValidationRun:
        """Create a validation verification record with validated foreign keys."""
        if not self.dataset_repo.get_by_id(db, payload.model_dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model dataset with ID '{payload.model_dataset_id}' was not found.",
            )
        if payload.observation_dataset_id and not self.dataset_repo.get_by_id(db, payload.observation_dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observation dataset with ID '{payload.observation_dataset_id}' was not found.",
            )
        if not self.variable_repo.get_by_id(db, payload.variable_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable with ID '{payload.variable_id}' was not found.",
            )

        return self.repository.create(db, payload.model_dump())

    def compute_and_record(self, db: Session, payload: ValidationComputeRequest) -> ValidationRun:
        """Compute statistical validation metrics (MAE, RMSE, Bias, Correlation) and persist run record."""
        if not self.dataset_repo.get_by_id(db, payload.model_dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model dataset with ID '{payload.model_dataset_id}' was not found.",
            )
        if payload.observation_dataset_id and not self.dataset_repo.get_by_id(db, payload.observation_dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observation dataset with ID '{payload.observation_dataset_id}' was not found.",
            )
        if not self.variable_repo.get_by_id(db, payload.variable_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable with ID '{payload.variable_id}' was not found.",
            )

        model_vals = np.array([p[0] for p in payload.paired_data], dtype=np.float64)
        obs_vals = np.array([p[1] for p in payload.paired_data], dtype=np.float64)

        diffs = model_vals - obs_vals
        mae = float(np.mean(np.abs(diffs)))
        rmse = float(np.sqrt(np.mean(diffs**2)))
        bias = float(np.mean(diffs))

        # Pearson correlation
        if len(model_vals) > 1 and np.std(model_vals) > 1e-9 and np.std(obs_vals) > 1e-9:
            corr_matrix = np.corrcoef(model_vals, obs_vals)
            correlation = float(corr_matrix[0, 1])
            if math.isnan(correlation):
                correlation = None
        else:
            correlation = None

        run_data = {
            "model_dataset_id": payload.model_dataset_id,
            "observation_dataset_id": payload.observation_dataset_id,
            "variable_id": payload.variable_id,
            "spatial_scope_geom": payload.spatial_scope_geom,
            "time_range_start": payload.time_range_start,
            "time_range_end": payload.time_range_end,
            "depth_level_min": payload.depth_level_min,
            "depth_level_max": payload.depth_level_max,
            "metric_mae": round(mae, 4),
            "metric_rmse": round(rmse, 4),
            "metric_bias": round(bias, 4),
            "metric_correlation": round(correlation, 4) if correlation is not None else None,
            "sample_count": len(payload.paired_data),
            "result_payload": {
                "sample_pairs_count": len(payload.paired_data),
                "model_mean": round(float(np.mean(model_vals)), 4),
                "obs_mean": round(float(np.mean(obs_vals)), 4),
                "model_std": round(float(np.std(model_vals)), 4),
                "obs_std": round(float(np.std(obs_vals)), 4),
            },
        }

        return self.repository.create(db, run_data)

    def delete_run(self, db: Session, run_id: uuid.UUID) -> None:
        """Delete validation run."""
        run = self.get_run(db, run_id)
        self.repository.delete(db, run)
