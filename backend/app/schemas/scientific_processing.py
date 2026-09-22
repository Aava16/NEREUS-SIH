from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DimensionMetadata(BaseModel):
    """Metadata describing a single dimension in a scientific array."""

    name: str = Field(..., description="Dimension name (e.g., time, depth, lat, lon)")
    size: int = Field(..., description="Number of elements along this dimension")
    min_value: Optional[float] = Field(None, description="Minimum coordinate value if numeric")
    max_value: Optional[float] = Field(None, description="Maximum coordinate value if numeric")
    step: Optional[float] = Field(None, description="Coordinate step/resolution if regular")
    units: Optional[str] = Field(None, description="Dimension units (e.g., degrees_north, meters, seconds)")


class VariableArrayMetadata(BaseModel):
    """Metadata describing a scientific variable within an array file."""

    name: str = Field(..., description="Variable parameter key in array (e.g., thetao, so, uo)")
    dimensions: List[str] = Field(..., description="List of dimension names for this variable")
    shape: List[int] = Field(..., description="Shape tuple as list of integers")
    dtype: str = Field(..., description="Numeric data type (e.g., float32, float64)")
    units: Optional[str] = Field(None, description="Physical units attribute")
    standard_name: Optional[str] = Field(None, description="CF standard name attribute")
    long_name: Optional[str] = Field(None, description="Descriptive parameter name")
    valid_min: Optional[float] = None
    valid_max: Optional[float] = None
    fill_value: Optional[float] = None


class ScientificAssetInspectionResponse(BaseModel):
    """Complete inspection report for a registered scientific array asset."""

    asset_id: uuid.UUID
    dataset_id: uuid.UUID
    storage_format: str
    uri: str
    dimensions: Dict[str, DimensionMetadata]
    variables: Dict[str, VariableArrayMetadata]
    spatial_extent: Optional[Dict[str, float]] = Field(
        None, description="Bounding coordinates {min_lon, min_lat, max_lon, max_lat}"
    )
    temporal_coverage: Optional[Dict[str, Optional[str]]] = Field(
        None, description="Temporal range {start, end}"
    )
    depth_coverage: Optional[Dict[str, Optional[float]]] = Field(
        None, description="Depth range {min_m, max_m}"
    )
    global_attributes: Dict[str, Any] = Field(default_factory=dict)
    is_valid_ocean_grid: bool = Field(True, description="Indicates if spatial/temporal coordinates are valid")
    validation_warnings: List[str] = Field(default_factory=list)


class GridSliceRequest(BaseModel):
    """Request to extract a bounded 2D or 1D array slice from a scientific grid file."""

    variable_name: str = Field(..., description="Target array variable key (e.g., temperature, water_temp)")
    time_index: Optional[int] = Field(default=0, ge=0, description="Time step index")
    depth_index: Optional[int] = Field(default=0, ge=0, description="Depth level index")
    bbox_min_lon: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Bounding box min longitude")
    bbox_min_lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Bounding box min latitude")
    bbox_max_lon: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Bounding box max longitude")
    bbox_max_lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Bounding box max latitude")
    decimation_step: int = Field(default=1, ge=1, le=20, description="Sub-sampling stride for LOD downsampling")


class GridSliceStatistics(BaseModel):
    """Statistical summary of an extracted scientific array slice."""

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    sample_count: int
    null_count: int


class GridSliceResponse(BaseModel):
    """Extracted array slice payload formatted for client rendering."""

    variable_name: str
    units: Optional[str] = None
    dimensions: List[str]
    shape: List[int]
    lons: List[float]
    lats: List[float]
    depth_m: Optional[float] = None
    timestamp: Optional[str] = None
    data_grid: List[List[Optional[float]]] = Field(
        ..., description="2D matrix of values indexed as [lat_idx][lon_idx]"
    )
    statistics: GridSliceStatistics
    provenance_id: uuid.UUID


class DerivedFieldRequest(BaseModel):
    """Request to compute an on-the-fly scientific derived parameter (e.g., velocity magnitude)."""

    derived_type: str = Field(
        ...,
        description="Type: CURRENT_SPEED_MAGNITUDE, CELSIUS_FROM_KELVIN",
    )
    variable_u: Optional[str] = Field(None, description="Zonal current velocity variable key (for speed magnitude)")
    variable_v: Optional[str] = Field(None, description="Meridional current velocity variable key (for speed magnitude)")
    variable_source: Optional[str] = Field(None, description="Source variable for single-variable transformation")
    time_index: int = Field(default=0, ge=0)
    depth_index: int = Field(default=0, ge=0)
    decimation_step: int = Field(default=1, ge=1, le=20)


class DerivedFieldResponse(BaseModel):
    """Result of scientific derived parameter computation."""

    derived_type: str
    units: str
    shape: List[int]
    lons: List[float]
    lats: List[float]
    data_grid: List[List[Optional[float]]]
    statistics: GridSliceStatistics
    provenance_id: uuid.UUID
