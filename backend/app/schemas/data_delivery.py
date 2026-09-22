"""Pydantic schemas for scientific data delivery and visualization.

Defines frontend-friendly, strongly-typed JSON response models for
dataset metadata, variable discovery, map grids, vertical profiles,
point time-series, and ocean current vector fields.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import (
    DepthRangeSummary,
    SpatialExtentSummary,
    TemporalRangeSummary,
)


class FrontendDatasetMetadata(BaseModel):
    """Complete, frontend-ready description of a scientific ocean dataset."""

    dataset_id: UUID = Field(..., description="Canonical dataset unique identifier")
    name: str = Field(..., description="Short canonical identifier name")
    title: str = Field(..., description="Human-readable dataset title")
    description: Optional[str] = Field(None, description="Detailed dataset narrative")
    source: Optional[str] = Field(None, description="Originating agency / institution")
    source_uri: Optional[str] = Field(None, description="Source catalog or file URI")
    dataset_type: str = Field(..., description="Classification (e.g. GRIDDED_MODEL, SATELLITE_L3)")
    variables: List[str] = Field(default_factory=list, description="List of variable names present")
    dimensions: Dict[str, int] = Field(default_factory=dict, description="Named dimensions and sizes")
    spatial_extent: SpatialExtentSummary = Field(..., description="Spatial bounding extent and resolution")
    depth_extent: DepthRangeSummary = Field(..., description="Vertical depth coordinate extent")
    temporal_extent: Optional[TemporalRangeSummary] = Field(None, description="Temporal range and resolution")
    primary_asset_id: Optional[UUID] = Field(None, description="Primary underlying array asset ID")
    primary_asset_format: Optional[str] = Field(None, description="Scientific format (e.g. NETCDF4, ZARR)")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Raw CF/ISO metadata attributes")
    created_at: datetime = Field(..., description="Dataset catalog registration timestamp")
    updated_at: datetime = Field(..., description="Last catalog update timestamp")

    model_config = ConfigDict(from_attributes=True)


class VariableMetadataItem(BaseModel):
    """Discovery metadata for a single oceanographic variable."""

    variable_name: str = Field(..., description="Variable identifier in the scientific array")
    standard_name: Optional[str] = Field(None, description="CF standard name attribute")
    long_name: Optional[str] = Field(None, description="Descriptive long name")
    units: Optional[str] = Field(None, description="Physical units")
    dtype: str = Field(..., description="Array element data type (e.g. float32, float64)")
    dimensions: List[str] = Field(..., description="Named dimension coordinates (e.g. ['time', 'lat', 'lon'])")
    shape: List[int] = Field(..., description="Dimension lengths")
    valid_min: Optional[float] = Field(None, description="Minimum valid physical range value")
    valid_max: Optional[float] = Field(None, description="Maximum valid physical range value")
    fill_value: Optional[float] = Field(None, description="Missing / fill value indicator")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="All custom variable attributes")

    model_config = ConfigDict(from_attributes=True)


class VariableDiscoveryResponse(BaseModel):
    """Response containing all discoverable variables for a dataset."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset name")
    asset_id: Optional[UUID] = Field(None, description="Array asset ID")
    variables: List[VariableMetadataItem] = Field(..., description="List of discovered variables")
    total_variables: int = Field(..., description="Count of variables")

    model_config = ConfigDict(from_attributes=True)


class DownsampleMetadata(BaseModel):
    """Metadata regarding level-of-detail decimation and downsampling."""

    downsampled: bool = Field(False, description="True if response was downsampled for safety")
    original_points: int = Field(..., description="Total points in un-decimated selection")
    returned_points: int = Field(..., description="Total points returned in response")
    decimation_factor: int = Field(1, description="Decimation stride applied across spatial/temporal axes")


class GridDeliveryResponse(BaseModel):
    """2D spatial grid response formatted for map heatmaps, contours, and raster layers."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    variable_name: str = Field(..., description="Variable name")
    units: Optional[str] = Field(None, description="Variable physical units")
    time: Optional[str] = Field(None, description="Selected timestamp in ISO 8601")
    depth: Optional[float] = Field(None, description="Selected depth level in meters")
    latitudes: List[float] = Field(..., description="1D array of latitude coordinates in degrees north")
    longitudes: List[float] = Field(..., description="1D array of longitude coordinates in degrees east")
    values: List[List[Optional[float]]] = Field(
        ..., description="2D array of values (lat x lon matrix, with null for missing/masked cells)"
    )
    min_value: Optional[float] = Field(None, description="Minimum value in sliced grid")
    max_value: Optional[float] = Field(None, description="Maximum value in sliced grid")
    downsample: DownsampleMetadata = Field(..., description="Downsample tracking metadata")
    delivered_at: datetime = Field(..., description="Delivery response timestamp")

    model_config = ConfigDict(from_attributes=True)


class ProfileDeliveryResponse(BaseModel):
    """Vertical depth profile response for a specific ocean geographic location."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    variable_name: str = Field(..., description="Variable name")
    units: Optional[str] = Field(None, description="Physical units")
    requested_latitude: float = Field(..., description="Requested latitude coordinate")
    requested_longitude: float = Field(..., description="Requested longitude coordinate")
    actual_latitude: float = Field(..., description="Nearest grid point latitude")
    actual_longitude: float = Field(..., description="Nearest grid point longitude")
    time: Optional[str] = Field(None, description="Timestamp context in ISO 8601")
    depths: List[float] = Field(..., description="Vertical depth coordinates in meters")
    values: List[Optional[float]] = Field(..., description="Variable values at each depth level")
    valid_levels: int = Field(..., description="Count of non-null depth levels")
    delivered_at: datetime = Field(..., description="Delivery response timestamp")

    model_config = ConfigDict(from_attributes=True)


class TimeSeriesPoint(BaseModel):
    """Single time-series point."""

    timestamp: str = Field(..., description="ISO 8601 timestamp")
    value: Optional[float] = Field(None, description="Measurement value (null if missing/masked)")


class TimeSeriesDeliveryResponse(BaseModel):
    """Point time-series response across a bounded temporal range."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    variable_name: str = Field(..., description="Variable name")
    units: Optional[str] = Field(None, description="Physical units")
    latitude: float = Field(..., description="Point latitude")
    longitude: float = Field(..., description="Point longitude")
    depth: Optional[float] = Field(None, description="Point depth in meters")
    points: List[TimeSeriesPoint] = Field(..., description="Array of timestamp-value pairs")
    total_points: int = Field(..., description="Count of returned points")
    downsample: DownsampleMetadata = Field(..., description="Downsampling metadata")
    delivered_at: datetime = Field(..., description="Delivery response timestamp")

    model_config = ConfigDict(from_attributes=True)


class CurrentVectorItem(BaseModel):
    """Single current velocity vector element."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    u: Optional[float] = Field(None, description="Eastward velocity component (m/s)")
    v: Optional[float] = Field(None, description="Northward velocity component (m/s)")
    w: Optional[float] = Field(None, description="Vertical velocity component (m/s)")
    speed: Optional[float] = Field(None, description="Speed magnitude (m/s)")
    direction: Optional[float] = Field(None, description="Flow direction in degrees [0, 360) from North")


class CurrentsDeliveryResponse(BaseModel):
    """Ocean current velocity vector field response for particle and arrow visualization."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset name")
    velocity_dimensions: str = Field(..., description="'2D (horizontal: u, v)' or '3D (total: u, v, w)'")
    time: Optional[str] = Field(None, description="Timestamp context in ISO 8601")
    depth: Optional[float] = Field(None, description="Depth level context in meters")
    vectors: List[CurrentVectorItem] = Field(..., description="Sampled vector elements")
    total_vectors: int = Field(..., description="Number of vectors returned")
    speed_min: Optional[float] = Field(None, description="Minimum vector speed magnitude (m/s)")
    speed_max: Optional[float] = Field(None, description="Maximum vector speed magnitude (m/s)")
    downsample: DownsampleMetadata = Field(..., description="Downsample tracking metadata")
    delivered_at: datetime = Field(..., description="Delivery response timestamp")

    model_config = ConfigDict(from_attributes=True)


class SliceDeliveryResponse(BaseModel):
    """General bounded multidimensional array slice response."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    variable_name: str = Field(..., description="Variable name")
    units: Optional[str] = Field(None, description="Variable physical units")
    dimensions: List[str] = Field(..., description="Names of dimensions present in this slice")
    shape: List[int] = Field(..., description="Shape of the delivered slice")
    dimension_coordinates: Dict[str, List[Any]] = Field(
        default_factory=dict, description="Coordinate values along each sliced axis"
    )
    values: Any = Field(..., description="Nested multi-dimensional values array or flattened list")
    downsample: DownsampleMetadata = Field(..., description="Downsampling metadata")
    delivered_at: datetime = Field(..., description="Delivery response timestamp")

    model_config = ConfigDict(from_attributes=True)


class TransectPoint(BaseModel):
    """Single point sampled along a scientific ocean transect line."""

    latitude: float = Field(..., description="Sampled point latitude in degrees north")
    longitude: float = Field(..., description="Sampled point longitude in degrees east")
    distance_km: float = Field(..., description="Cumulative distance from start point in kilometers")
    value: Optional[float] = Field(None, description="Variable value at sampled coordinate (null if masked)")


class TransectDeliveryResponse(BaseModel):
    """Scientific transect cross-section response between two coordinates."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    variable_name: str = Field(..., description="Variable name")
    units: Optional[str] = Field(None, description="Physical units")
    time: Optional[str] = Field(None, description="Timestamp context in ISO 8601")
    depth: Optional[float] = Field(None, description="Depth level in meters")
    start_latitude: float = Field(..., description="Transect origin latitude")
    start_longitude: float = Field(..., description="Transect origin longitude")
    end_latitude: float = Field(..., description="Transect termination latitude")
    end_longitude: float = Field(..., description="Transect termination longitude")
    points: List[TransectPoint] = Field(..., description="Sampled points along the transect")
    total_points: int = Field(..., description="Total points sampled")
    total_distance_km: float = Field(..., description="Total length of the transect in kilometers")
    min_value: Optional[float] = Field(None, description="Minimum value observed along transect")
    max_value: Optional[float] = Field(None, description="Maximum value observed along transect")
    delivered_at: datetime = Field(..., description="Delivery response timestamp")

    model_config = ConfigDict(from_attributes=True)

