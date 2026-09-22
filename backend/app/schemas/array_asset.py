from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ArrayAssetBase(BaseModel):
    """Base schema for scientific multidimensional array asset metadata."""

    dataset_id: uuid.UUID = Field(..., description="Parent dataset ID")
    storage_format: str = Field(..., max_length=50, description="Format (NETCDF4, ZARR, HDF5, CLOUD_ZARR)")
    uri: str = Field(..., max_length=512, description="Filesystem path or object store S3/GCS URI")
    variable_info: Dict[str, Any] = Field(default_factory=dict, description="Internal array variable names and shape info")
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Dimension ordering (time, depth, lat, lon)")
    checksum: Optional[str] = Field(None, max_length=128, description="SHA256 or MD5 integrity checksum")


class ArrayAssetCreate(ArrayAssetBase):
    """Schema for registering a multidimensional array asset."""

    pass


class ArrayAssetRead(ArrayAssetBase):
    """Schema for reading array asset metadata."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
