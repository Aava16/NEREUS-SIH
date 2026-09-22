"""API endpoints for scientific data delivery and visualization in NEREUS.

Exposes processed and analyzed ocean dataset variables, 2D map grids,
vertical depth profiles, point time-series, and vector fields.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.data_delivery import (
    CurrentsDeliveryResponse,
    FrontendDatasetMetadata,
    GridDeliveryResponse,
    ProfileDeliveryResponse,
    SliceDeliveryResponse,
    TimeSeriesDeliveryResponse,
    TransectDeliveryResponse,
    VariableDiscoveryResponse,
)
from app.services.data_delivery.service import DataDeliveryService

router = APIRouter(prefix="/datasets", tags=["Scientific Data Delivery"])
delivery_service = DataDeliveryService()


@router.get(
    "/{dataset_id}/metadata",
    response_model=FrontendDatasetMetadata,
    status_code=status.HTTP_200_OK,
    summary="Get Complete Dataset Metadata for Visualizers",
    description="Returns complete frontend-safe dataset metadata including variables, dimensions, spatial extent, depth extent, and temporal coverage.",
)
def get_dataset_metadata(
    dataset_id: UUID,
    db: Session = Depends(get_db),
) -> FrontendDatasetMetadata:
    """Fetch complete frontend-safe dataset description."""
    return delivery_service.get_dataset_metadata(db, dataset_id)


@router.get(
    "/{dataset_id}/variables",
    response_model=VariableDiscoveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover Dataset Variables",
    description="Returns all variables in the scientific array asset with physical units, dimensions, shapes, dtypes, and CF metadata.",
)
def discover_variables(
    dataset_id: UUID,
    asset_id: Optional[UUID] = Query(None, description="Optional array asset ID"),
    db: Session = Depends(get_db),
) -> VariableDiscoveryResponse:
    """Discover scientific variables for a dataset."""
    return delivery_service.discover_variables(db, dataset_id, asset_id)


@router.get(
    "/{dataset_id}/variables/{variable}/grid",
    response_model=GridDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Bounded 2D Map / Grid Surface",
    description="Returns a 2D spatial grid (latitudes, longitudes, values matrix) at specified time and depth indices with LOD decimation for web maps, heatmaps, and contours.",
)
def get_variable_grid(
    dataset_id: UUID,
    variable: str,
    time_index: int = Query(0, description="Time step index (0-indexed)"),
    depth_index: int = Query(0, description="Vertical depth level index (0-indexed)"),
    min_lat: Optional[float] = Query(None, description="Minimum latitude bounding filter [-90, 90]"),
    max_lat: Optional[float] = Query(None, description="Maximum latitude bounding filter [-90, 90]"),
    min_lon: Optional[float] = Query(None, description="Minimum longitude bounding filter [-180, 180]"),
    max_lon: Optional[float] = Query(None, description="Maximum longitude bounding filter [-180, 180]"),
    decimation: int = Query(1, ge=1, le=100, description="Spatial stride decimation factor for level-of-detail downsampling"),
    asset_id: Optional[UUID] = Query(None, description="Optional specific array asset ID"),
    db: Session = Depends(get_db),
) -> GridDeliveryResponse:
    """Extract bounded 2D map/grid slice."""
    return delivery_service.get_grid(
        db=db,
        dataset_id=dataset_id,
        variable_name=variable,
        time_index=time_index,
        depth_index=depth_index,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        decimation=decimation,
        asset_id=asset_id,
    )


@router.get(
    "/{dataset_id}/variables/{variable}/profile",
    response_model=ProfileDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Vertical Depth Profile",
    description="Extracts vertical depth levels and values at the nearest grid point to requested latitude and longitude coordinates.",
)
def get_variable_profile(
    dataset_id: UUID,
    variable: str,
    latitude: float = Query(..., description="Target latitude in degrees north [-90, 90]"),
    longitude: float = Query(..., description="Target longitude in degrees east [-180, 180]"),
    time_index: int = Query(0, description="Time step index (0-indexed)"),
    asset_id: Optional[UUID] = Query(None, description="Optional specific array asset ID"),
    db: Session = Depends(get_db),
) -> ProfileDeliveryResponse:
    """Extract vertical depth profile for a station/coordinate point."""
    return delivery_service.get_profile(
        db=db,
        dataset_id=dataset_id,
        variable_name=variable,
        latitude=latitude,
        longitude=longitude,
        time_index=time_index,
        asset_id=asset_id,
    )


@router.get(
    "/{dataset_id}/variables/{variable}/timeseries",
    response_model=TimeSeriesDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Point Time-Series Sequence",
    description="Extracts temporal sequence points for a specific geographical location and depth with bounded start/end ranges and LOD decimation.",
)
def get_variable_timeseries(
    dataset_id: UUID,
    variable: str,
    latitude: float = Query(..., description="Target latitude in degrees north [-90, 90]"),
    longitude: float = Query(..., description="Target longitude in degrees east [-180, 180]"),
    depth: Optional[float] = Query(None, description="Optional depth level in meters"),
    start_time: Optional[str] = Query(None, description="ISO 8601 start date-time filter"),
    end_time: Optional[str] = Query(None, description="ISO 8601 end date-time filter"),
    decimation: int = Query(1, ge=1, le=100, description="Temporal decimation stride factor"),
    asset_id: Optional[UUID] = Query(None, description="Optional specific array asset ID"),
    db: Session = Depends(get_db),
) -> TimeSeriesDeliveryResponse:
    """Extract point time-series sequence."""
    return delivery_service.get_timeseries(
        db=db,
        dataset_id=dataset_id,
        variable_name=variable,
        latitude=latitude,
        longitude=longitude,
        depth=depth,
        start_time=start_time,
        end_time=end_time,
        decimation=decimation,
        asset_id=asset_id,
    )


@router.get(
    "/{dataset_id}/currents/vectors",
    response_model=CurrentsDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Ocean Current Vectors for Visualizers",
    description="Extracts current velocity vectors (lat, lon, u, v, w, speed, direction) for particle animations and flow arrows with LOD decimation.",
)
def get_current_vectors(
    dataset_id: UUID,
    u_var: Optional[str] = Query(None, description="Optional eastward velocity variable name"),
    v_var: Optional[str] = Query(None, description="Optional northward velocity variable name"),
    w_var: Optional[str] = Query(None, description="Optional vertical velocity variable name"),
    time_index: int = Query(0, description="Time step index (0-indexed)"),
    depth_index: int = Query(0, description="Vertical depth level index (0-indexed)"),
    min_lat: Optional[float] = Query(None, description="Minimum latitude bounding filter [-90, 90]"),
    max_lat: Optional[float] = Query(None, description="Maximum latitude bounding filter [-90, 90]"),
    min_lon: Optional[float] = Query(None, description="Minimum longitude bounding filter [-180, 180]"),
    max_lon: Optional[float] = Query(None, description="Maximum longitude bounding filter [-180, 180]"),
    decimation: int = Query(1, ge=1, le=100, description="Spatial decimation factor"),
    asset_id: Optional[UUID] = Query(None, description="Optional specific array asset ID"),
    db: Session = Depends(get_db),
) -> CurrentsDeliveryResponse:
    """Extract ocean current velocity vectors."""
    return delivery_service.get_current_vectors(
        db=db,
        dataset_id=dataset_id,
        u_var=u_var,
        v_var=v_var,
        w_var=w_var,
        time_index=time_index,
        depth_index=depth_index,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        decimation=decimation,
        asset_id=asset_id,
    )


@router.get(
    "/{dataset_id}/variables/{variable}/slice",
    response_model=SliceDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Controlled Scientific Array Slice",
    description="Extracts a bounded slice from any multi-dimensional variable with strict server-side cell limits.",
)
def get_variable_slice(
    dataset_id: UUID,
    variable: str,
    time_index: Optional[int] = Query(None, description="Optional time index"),
    depth_index: Optional[int] = Query(None, description="Optional depth index"),
    min_lat: Optional[float] = Query(None, description="Minimum latitude bounding filter"),
    max_lat: Optional[float] = Query(None, description="Maximum latitude bounding filter"),
    min_lon: Optional[float] = Query(None, description="Minimum longitude bounding filter"),
    max_lon: Optional[float] = Query(None, description="Maximum longitude bounding filter"),
    decimation: int = Query(1, ge=1, le=100, description="Decimation stride factor"),
    asset_id: Optional[UUID] = Query(None, description="Optional specific array asset ID"),
    db: Session = Depends(get_db),
) -> SliceDeliveryResponse:
    """Extract a bounded slice for any scientific variable."""
    return delivery_service.get_slice(
        db=db,
        dataset_id=dataset_id,
        variable_name=variable,
        time_index=time_index,
        depth_index=depth_index,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        decimation=decimation,
        asset_id=asset_id,
    )


@router.get(
    "/{dataset_id}/variables/{variable}/transect",
    response_model=TransectDeliveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract 1D Transect Cross-Section Between Two Coordinates",
    description="Samples scalar field values along a great-circle path from Point A (lat1, lon1) to Point B (lat2, lon2) with cumulative distance in km.",
)
def get_variable_transect(
    dataset_id: UUID,
    variable: str,
    lat1: float = Query(..., description="Start point latitude [-90, 90]"),
    lon1: float = Query(..., description="Start point longitude [-180, 180]"),
    lat2: float = Query(..., description="End point latitude [-90, 90]"),
    lon2: float = Query(..., description="End point longitude [-180, 180]"),
    num_points: int = Query(50, ge=2, le=500, description="Number of sample points along transect"),
    time_index: int = Query(0, description="Time step index (0-indexed)"),
    depth_index: int = Query(0, description="Depth level index (0-indexed)"),
    asset_id: Optional[UUID] = Query(None, description="Optional specific array asset ID"),
    db: Session = Depends(get_db),
) -> TransectDeliveryResponse:
    """Extract 1D transect cross-section between two coordinates."""
    return delivery_service.get_transect(
        db=db,
        dataset_id=dataset_id,
        variable_name=variable,
        lat1=lat1,
        lon1=lon1,
        lat2=lat2,
        lon2=lon2,
        num_points=num_points,
        time_index=time_index,
        depth_index=depth_index,
        asset_id=asset_id,
    )

