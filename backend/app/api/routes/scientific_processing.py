import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.scientific_processing import (
    DerivedFieldRequest,
    DerivedFieldResponse,
    GridSliceRequest,
    GridSliceResponse,
    ScientificAssetInspectionResponse,
)
from app.services.scientific_processing import ScientificProcessingService

router = APIRouter(prefix="/processing", tags=["Scientific Data Processing"])
processing_service = ScientificProcessingService()


@router.get(
    "/assets/{asset_id}/inspect",
    response_model=ScientificAssetInspectionResponse,
    summary="Inspect Scientific Array Asset",
    description="Inspect multidimensional scientific array file (NetCDF4 / Zarr) to extract dimensions, coordinate ranges, variable parameters, and spatial/temporal bounds.",
)
def inspect_asset_endpoint(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ScientificAssetInspectionResponse:
    """Inspect scientific array metadata and coordinates."""
    return processing_service.inspect_asset(db, asset_id)


@router.post(
    "/assets/{asset_id}/slice",
    response_model=GridSliceResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Bounded Scientific Grid Slice",
    description="Extract a 2D spatial-temporal grid slice at specified depth/time with optional decimation and bounding box subsetting, recording an audit provenance trace.",
)
def slice_grid_endpoint(
    asset_id: uuid.UUID,
    payload: GridSliceRequest,
    db: Session = Depends(get_db),
) -> GridSliceResponse:
    """Extract decimated 2D slice from array asset."""
    return processing_service.slice_grid(db, asset_id, payload)


@router.post(
    "/assets/{asset_id}/derive",
    response_model=DerivedFieldResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Scientific Derived Field",
    description="Calculate derived scientific ocean parameters (e.g., Current Velocity Speed Magnitude from U and V components) on-the-fly with full provenance traceability.",
)
def compute_derived_field_endpoint(
    asset_id: uuid.UUID,
    payload: DerivedFieldRequest,
    db: Session = Depends(get_db),
) -> DerivedFieldResponse:
    """Compute derived ocean parameter field."""
    return processing_service.compute_derived_field(db, asset_id, payload)
