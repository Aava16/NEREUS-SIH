from typing import List
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dataset import (
    DatasetCreate,
    DatasetDetailRead,
    DatasetFilterParams,
    DatasetRead,
    DatasetUpdate,
)
from app.services.dataset import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])
dataset_service = DatasetService()


@router.get(
    "",
    response_model=List[DatasetRead],
    summary="List Ocean Datasets",
    description="Retrieve cataloged oceanographic datasets with optional type, temporal, and spatial bounding box filters.",
)
def list_datasets(
    filters: DatasetFilterParams = Depends(),
    db: Session = Depends(get_db),
) -> List[DatasetRead]:
    """List datasets matching filter parameters."""
    return dataset_service.list_datasets(db, filters)  # type: ignore[return-value]


@router.post(
    "",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Dataset",
    description="Register a new authoritative ocean dataset or model forecast collection.",
)
def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
) -> DatasetRead:
    """Register a new dataset in the catalog."""
    return dataset_service.create_dataset(db, payload)  # type: ignore[return-value]


@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailRead,
    summary="Get Dataset Details",
    description="Retrieve complete metadata, spatial extent, and parameter counts for a dataset.",
)
def get_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DatasetDetailRead:
    """Fetch dataset metadata by ID."""
    return dataset_service.get_dataset_detail(db, dataset_id)


@router.patch(
    "/{dataset_id}",
    response_model=DatasetRead,
    summary="Update Dataset",
    description="Update metadata, spatial extent, or time coverage of an existing dataset.",
)
def update_dataset(
    dataset_id: uuid.UUID,
    payload: DatasetUpdate,
    db: Session = Depends(get_db),
) -> DatasetRead:
    """Update dataset attributes."""
    return dataset_service.update_dataset(db, dataset_id, payload)  # type: ignore[return-value]


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Dataset",
    description="Remove a dataset and cascade deletion to associated variables and observations.",
)
def delete_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a dataset by ID."""
    dataset_service.delete_dataset(db, dataset_id)
