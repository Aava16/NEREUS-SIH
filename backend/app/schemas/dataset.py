from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
import shapely.geometry
from app.schemas.geometry import GeoJSONPolygon, geometry_to_shape


class DatasetBase(BaseModel):
    """Base scientific attributes for an oceanographic dataset."""

    name: str = Field(..., max_length=100, description="Unique machine identifier for dataset")
    title: str = Field(..., max_length=255, description="Human-readable title")
    description: Optional[str] = Field(None, description="Detailed scientific description and methodology")
    source: Optional[str] = Field(None, max_length=255, description="Originator/institute (e.g., INCOIS, NOAA, CMEMS)")
    source_uri: Optional[str] = Field(None, max_length=512, description="Download or source endpoint URL")
    dataset_type: str = Field(
        ...,
        max_length=50,
        description="Type (e.g., MODEL_FORECAST, REANALYSIS, SATELLITE_OBSERVATION, CLIMATOLOGY, IN_SITU_NETWORK)",
    )
    temporal_start: Optional[datetime] = Field(None, description="Start timestamp of available coverage")
    temporal_end: Optional[datetime] = Field(None, description="End timestamp of available coverage")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary provenance and domain attributes")


class DatasetCreate(DatasetBase):
    """Schema for registering a new dataset."""

    spatial_extent: Optional[GeoJSONPolygon] = Field(None, description="Spatial bounding polygon in GeoJSON format")


class DatasetUpdate(BaseModel):
    """Schema for updating an existing dataset."""

    name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    source: Optional[str] = Field(None, max_length=255)
    source_uri: Optional[str] = Field(None, max_length=512)
    dataset_type: Optional[str] = Field(None, max_length=50)
    temporal_start: Optional[datetime] = None
    temporal_end: Optional[datetime] = None
    spatial_extent: Optional[GeoJSONPolygon] = None
    metadata_json: Optional[Dict[str, Any]] = None


class DatasetRead(DatasetBase):
    """Schema for returning dataset metadata."""

    id: uuid.UUID
    spatial_extent: Optional[GeoJSONPolygon] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("spatial_extent", mode="before")
    @classmethod
    def serialize_spatial_extent(cls, v: Any) -> Optional[Dict[str, Any]]:
        shape_obj = geometry_to_shape(v)
        if shape_obj is None:
            return None
        return shapely.geometry.mapping(shape_obj)


class DatasetDetailRead(DatasetRead):
    """Detailed dataset schema including variable count and asset count."""

    variables_count: int = Field(default=0, description="Number of variables associated with this dataset")
    array_assets_count: int = Field(default=0, description="Number of scientific array assets associated")



class DatasetFilterParams(BaseModel):
    """Query parameters for filtering datasets."""

    dataset_type: Optional[str] = None
    source: Optional[str] = None
    temporal_min: Optional[datetime] = None
    temporal_max: Optional[datetime] = None
    bbox_min_lon: Optional[float] = None
    bbox_min_lat: Optional[float] = None
    bbox_max_lon: Optional[float] = None
    bbox_max_lat: Optional[float] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
