from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.validation_run import (
    ValidationComputeRequest,
    ValidationRunCreate,
    ValidationRunFilterParams,
    ValidationRunRead,
)
from app.services.validation_run import ValidationRunService

router = APIRouter(prefix="/validation-runs", tags=["Scientific Validation"])
validation_service = ValidationRunService()


@router.get(
    "",
    response_model=List[ValidationRunRead],
    summary="List Validation Runs",
    description="Retrieve scientific verification records comparing numerical models with observations.",
)
def list_runs(
    filters: ValidationRunFilterParams = Depends(),
    db: Session = Depends(get_db),
) -> List[ValidationRunRead]:
    """List validation runs."""
    return validation_service.list_runs(db, filters)  # type: ignore[return-value]


@router.post(
    "",
    response_model=ValidationRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record Validation Run",
    description="Persist pre-calculated validation statistics (MAE, RMSE, Bias, Correlation).",
)
def create_run(
    payload: ValidationRunCreate,
    db: Session = Depends(get_db),
) -> ValidationRunRead:
    """Create validation run record."""
    return validation_service.create_run(db, payload)  # type: ignore[return-value]


@router.post(
    "/compute",
    response_model=ValidationRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Compute & Record Validation Metrics",
    description="Calculate MAE, RMSE, Bias, and Pearson Correlation from collocated (model, observed) pairs and record results.",
)
def compute_validation(
    payload: ValidationComputeRequest,
    db: Session = Depends(get_db),
) -> ValidationRunRead:
    """Compute validation metrics dynamically and store result."""
    return validation_service.compute_and_record(db, payload)  # type: ignore[return-value]


@router.get(
    "/{run_id}",
    response_model=ValidationRunRead,
    summary="Get Validation Run Details",
    description="Retrieve detailed statistical validation curves and metrics.",
)
def get_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ValidationRunRead:
    """Fetch validation run by ID."""
    return validation_service.get_run(db, run_id)  # type: ignore[return-value]


@router.delete(
    "/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Validation Run",
    description="Delete a validation run record.",
)
def delete_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a validation run by ID."""
    validation_service.delete_run(db, run_id)
