"""Pydantic schemas for scientific data analysis.

Provides strongly-typed, JSON-safe data models for dataset statistics,
spatial bounds, temporal ranges, ocean current velocity fields,
and comprehensive analysis summaries.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VariableStatistics(BaseModel):
    """Statistical summary for a single scientific variable."""

    variable_name: str = Field(..., description="Canonical or raw variable name")
    units: str | None = Field(None, description="Physical units of the variable")
    standard_name: str | None = Field(None, description="CF standard name if available")
    min: float | None = Field(None, description="Minimum valid value")
    max: float | None = Field(None, description="Maximum valid value")
    mean: float | None = Field(None, description="Arithmetic mean of valid values")
    median: float | None = Field(None, description="Median of valid values")
    std: float | None = Field(None, description="Standard deviation of valid values")
    p25: float | None = Field(None, description="25th percentile value")
    p50: float | None = Field(None, description="50th percentile value (median)")
    p75: float | None = Field(None, description="75th percentile value")
    p90: float | None = Field(None, description="90th percentile value")
    p95: float | None = Field(None, description="95th percentile value")
    valid_count: int = Field(..., description="Count of non-null, valid numerical values")
    missing_count: int = Field(..., description="Count of NaN, null, or masked values")
    shape: list[int] = Field(default_factory=list, description="Array shape dimensions")

    model_config = ConfigDict(from_attributes=True)


class DatasetStatisticsResponse(BaseModel):
    """Response containing statistics for one or all variables in a dataset."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset canonical name")
    asset_id: UUID | None = Field(None, description="Underlying scientific asset ID")
    variables: dict[str, VariableStatistics] = Field(
        ..., description="Statistical summary mapped by variable name"
    )
    analyzed_at: datetime = Field(..., description="Timestamp of analysis computation")

    model_config = ConfigDict(from_attributes=True)


class SpatialExtentSummary(BaseModel):
    """Spatial coordinate extent and resolution."""

    latitude_min: float = Field(..., description="Minimum latitude in degrees north [-90, 90]")
    latitude_max: float = Field(..., description="Maximum latitude in degrees north [-90, 90]")
    longitude_min: float = Field(..., description="Minimum longitude in degrees east [-180, 180]")
    longitude_max: float = Field(..., description="Maximum longitude in degrees east [-180, 180]")
    latitude_points: int = Field(..., description="Number of latitude grid points")
    longitude_points: int = Field(..., description="Number of longitude grid points")
    latitude_step: float | None = Field(None, description="Approximate latitude grid spacing")
    longitude_step: float | None = Field(None, description="Approximate longitude grid spacing")


class DepthRangeSummary(BaseModel):
    """Vertical depth coordinate summary."""

    depth_min: float | None = Field(None, description="Minimum depth in meters")
    depth_max: float | None = Field(None, description="Maximum depth in meters")
    depth_levels_count: int = Field(0, description="Number of discrete vertical depth levels")
    levels: list[float] = Field(default_factory=list, description="List of vertical depth levels")


class SpatialAnalysisResponse(BaseModel):
    """Spatial bounds, coordinate ranges, and vertical depth summary."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset canonical name")
    asset_id: UUID | None = Field(None, description="Underlying scientific asset ID")
    spatial_extent: SpatialExtentSummary = Field(..., description="2D spatial bounding box")
    depth_range: DepthRangeSummary = Field(..., description="Vertical depth range")
    coordinate_names: list[str] = Field(default_factory=list, description="Identified coordinate names")
    analyzed_at: datetime = Field(..., description="Timestamp of analysis computation")

    model_config = ConfigDict(from_attributes=True)


class TemporalRangeSummary(BaseModel):
    """Temporal coordinate bounds and sampling interval."""

    start_time: str = Field(..., description="Earliest timestamp in ISO 8601")
    end_time: str = Field(..., description="Latest timestamp in ISO 8601")
    total_timesteps: int = Field(..., description="Total count of temporal steps")
    timestep_interval_seconds: float | None = Field(
        None, description="Median timestep delta in seconds"
    )
    is_regular_interval: bool = Field(
        False, description="True if sampling intervals are uniform within tolerance"
    )


class TemporalAnalysisResponse(BaseModel):
    """Temporal range, resolution, and step analysis for a dataset."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset canonical name")
    asset_id: UUID | None = Field(None, description="Underlying scientific asset ID")
    temporal_range: TemporalRangeSummary = Field(..., description="Temporal coverage summary")
    timesteps_sample: list[str] = Field(
        default_factory=list, description="Sample of first and last timesteps in ISO 8601"
    )
    analyzed_at: datetime = Field(..., description="Timestamp of analysis computation")

    model_config = ConfigDict(from_attributes=True)


class CurrentsAnalysisResponse(BaseModel):
    """Ocean current velocity field analysis (magnitude, direction, components)."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset canonical name")
    asset_id: UUID | None = Field(None, description="Underlying scientific asset ID")
    velocity_dimensions: str = Field(
        ..., description="Dimensionality of velocity field: '2D (horizontal)' or '3D (total)'"
    )
    variables_used: dict[str, str] = Field(
        ..., description="Mapping of velocity components to dataset variables (e.g. {'u': 'u_curr', 'v': 'v_curr'})"
    )
    speed_statistics: VariableStatistics = Field(
        ..., description="Statistical distribution of current speed magnitude (m/s)"
    )
    direction_statistics: dict[str, Any] = Field(
        ..., description="Statistical summary of current flow direction in degrees [0, 360)"
    )
    component_statistics: dict[str, VariableStatistics] = Field(
        ..., description="Statistics for individual velocity components (u, v, w)"
    )
    analyzed_at: datetime = Field(..., description="Timestamp of analysis computation")

    model_config = ConfigDict(from_attributes=True)


class DatasetAnalysisSummaryResponse(BaseModel):
    """Comprehensive analysis summary combining spatial, temporal, and variable metadata."""

    dataset_id: UUID = Field(..., description="Dataset identifier")
    dataset_name: str = Field(..., description="Dataset canonical name")
    data_type: str = Field(..., description="Dataset type (e.g., GRIDDED_SATELLITE, MODEL_OUTPUT)")
    asset_id: UUID | None = Field(None, description="Primary scientific asset identifier")
    asset_format: str | None = Field(None, description="Scientific format (e.g., NETCDF4, ZARR)")
    spatial_extent: SpatialExtentSummary = Field(..., description="Spatial bounding extent")
    depth_range: DepthRangeSummary = Field(..., description="Vertical depth extent")
    temporal_range: TemporalRangeSummary | None = Field(None, description="Temporal range if available")
    available_variables: list[str] = Field(..., description="List of variable names in asset")
    variables_summary: dict[str, VariableStatistics] = Field(
        default_factory=dict, description="Basic statistics for key variables"
    )
    analyzed_at: datetime = Field(..., description="Timestamp of summary generation")

    model_config = ConfigDict(from_attributes=True)
