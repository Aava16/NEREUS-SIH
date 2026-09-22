from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
import shapely.geometry
from app.schemas.geometry import GeoJSONPoint, geometry_to_shape


class ObservationBase(BaseModel):
    """Base schema for an individual in-situ observation point."""

    dataset_id: uuid.UUID = Field(..., description="Dataset foreign key")
    variable_id: uuid.UUID = Field(..., description="Variable foreign key")
    platform_id: Optional[uuid.UUID] = Field(None, description="Observation platform foreign key")
    observed_at: datetime = Field(..., description="Observation capture timestamp (UTC)")
    depth_m: Optional[float] = Field(None, description="Depth level in meters (positive down)")
    value: float = Field(..., description="Measured scientific physical value")
    quality_flag: int = Field(default=1, description="QC flag: 1=Good, 2=Probably Good, 3=Bad, 4=Rejected, 9=Missing")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Cast info, pressure (dbar), cycle number")


class ObservationCreate(ObservationBase):
    """Schema for registering a single observation with coordinates or GeoJSON Point."""

    geometry: GeoJSONPoint = Field(..., description="GeoJSON Point representing (lon, lat)")


class ObservationBulkCreate(BaseModel):
    """Schema for bulk ingestion of observations."""

    observations: List[ObservationCreate] = Field(..., max_length=1000, description="List of observation items to insert")


class ObservationRead(ObservationBase):
    """Schema for returning observation records."""

    id: uuid.UUID
    geometry: GeoJSONPoint
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("geometry", mode="before")
    @classmethod
    def serialize_geometry(cls, v: Any) -> Dict[str, Any]:
        shape_obj = geometry_to_shape(v)
        if shape_obj is None:
            return {"type": "Point", "coordinates": (0.0, 0.0)}
        return shapely.geometry.mapping(shape_obj)


class ObservationFilterParams(BaseModel):
    """Query parameters for spatial, vertical, and temporal observation filtering."""

    dataset_id: Optional[uuid.UUID] = None
    variable_id: Optional[uuid.UUID] = None
    platform_id: Optional[uuid.UUID] = None
    temporal_min: Optional[datetime] = None
    temporal_max: Optional[datetime] = None
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None
    quality_flag: Optional[int] = None
    bbox_min_lon: Optional[float] = None
    bbox_min_lat: Optional[float] = None
    bbox_max_lon: Optional[float] = None
    bbox_max_lat: Optional[float] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
