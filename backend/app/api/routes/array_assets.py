from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.array_asset import ArrayAssetCreate, ArrayAssetRead
from app.services.array_asset import ArrayAssetService

router = APIRouter(prefix="/array-assets", tags=["Scientific Arrays"])
asset_service = ArrayAssetService()


@router.get(
    "",
    response_model=List[ArrayAssetRead],
    summary="List Scientific Array Assets",
    description="Retrieve multidimensional array assets (NetCDF4 / Zarr) linked to datasets.",
)
def list_assets(
    dataset_id: Optional[uuid.UUID] = Query(None, description="Filter by parent dataset ID"),
    storage_format: Optional[str] = Query(None, description="Filter by storage format (NETCDF4, ZARR)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[ArrayAssetRead]:
    """List registered array assets."""
    return asset_service.list_assets(  # type: ignore[return-value]
        db,
        dataset_id=dataset_id,
        storage_format=storage_format,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ArrayAssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Scientific Array Asset",
    description="Register metadata for a multidimensional scientific grid file (NetCDF4 / Zarr).",
)
def create_asset(
    payload: ArrayAssetCreate,
    db: Session = Depends(get_db),
) -> ArrayAssetRead:
    """Register an array asset."""
    return asset_service.create_asset(db, payload)  # type: ignore[return-value]


@router.get(
    "/{asset_id}",
    response_model=ArrayAssetRead,
    summary="Get Array Asset Details",
    description="Retrieve URI and dimension details for a specific array asset.",
)
def get_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ArrayAssetRead:
    """Fetch array asset by ID."""
    return asset_service.get_asset(db, asset_id)  # type: ignore[return-value]


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Array Asset",
    description="Remove an array asset metadata record.",
)
def delete_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an array asset by ID."""
    asset_service.delete_asset(db, asset_id)
