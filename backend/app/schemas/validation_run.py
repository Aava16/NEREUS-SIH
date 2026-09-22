from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
import shapely.geometry
from app.schemas.geometry import GeoJSONPolygon, geometry_to_shape


class ValidationRunBase(BaseModel):
    """Base schema for scientific validation comparing model output vs observations."""

    model_dataset_id: uuid.UUID = Field(..., description="Numerical model dataset under evaluation")
    observation_dataset_id: Optional[uuid.UUID] = Field(None, description="Observational reference dataset")
    variable_id: uuid.UUID = Field(..., description="Target evaluated variable ID")
    time_range_start: Optional[datetime] = Field(None, description="Evaluation window start")
    time_range_end: Optional[datetime] = Field(None, description="Evaluation window end")
    depth_level_min: Optional[float] = Field(None, description="Minimum depth level (m)")
    depth_level_max: Optional[float] = Field(None, description="Maximum depth level (m)")
    metric_mae: Optional[float] = Field(None, description="Mean Absolute Error")
    metric_rmse: Optional[float] = Field(None, description="Root Mean Square Error")
    metric_bias: Optional[float] = Field(None, description="Mean Model Bias (Model - Observed)")
    metric_correlation: Optional[float] = Field(None, description="Pearson Correlation Coefficient (r)")
    sample_count: int = Field(default=0, description="Number of collocated point pairs")
    result_payload: Dict[str, Any] = Field(default_factory=dict, description="Scatter points, residual distribution, depth curves")


class ValidationRunCreate(ValidationRunBase):
    """Schema for creating a validation run record."""

    spatial_scope_geom: Optional[GeoJSONPolygon] = Field(None, description="Spatial scope polygon in GeoJSON format")


class ValidationComputeRequest(BaseModel):
    """Request payload to calculate statistical validation metrics on-the-fly from model vs observation pairs."""

    model_dataset_id: uuid.UUID = Field(..., description="Numerical model dataset ID")
    observation_dataset_id: Optional[uuid.UUID] = Field(None, description="Observational dataset ID")
    variable_id: uuid.UUID = Field(..., description="Evaluated variable ID")
    paired_data: List[Tuple[float, float]] = Field(
        ...,
        min_length=2,
        description="List of paired measurement values: [(model_predicted_val, observed_truth_val), ...]",
    )
    spatial_scope_geom: Optional[GeoJSONPolygon] = Field(None, description="Spatial scope polygon")
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    depth_level_min: Optional[float] = None
    depth_level_max: Optional[float] = None


class ValidationRunRead(ValidationRunBase):
    """Schema for returning validation run records."""

    id: uuid.UUID
    spatial_scope_geom: Optional[GeoJSONPolygon] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("spatial_scope_geom", mode="before")
    @classmethod
    def serialize_spatial_scope(cls, v: Any) -> Optional[Dict[str, Any]]:
        shape_obj = geometry_to_shape(v)
        if shape_obj is None:
            return None
        return shapely.geometry.mapping(shape_obj)


class ValidationRunFilterParams(BaseModel):
    """Query parameters for filtering validation runs."""

    model_dataset_id: Optional[uuid.UUID] = None
    variable_id: Optional[uuid.UUID] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
