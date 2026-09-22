from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class VariableBase(BaseModel):
    """Base scientific attributes for an oceanographic variable."""

    name: str = Field(..., max_length=100, description="Machine parameter key (e.g., temperature, salinity, u_current)")
    standard_name: Optional[str] = Field(None, max_length=150, description="CF convention standard name")
    long_name: Optional[str] = Field(None, max_length=255, description="Full descriptive title")
    units: Optional[str] = Field(None, max_length=50, description="Standard oceanographic or SI physical units")
    data_type: str = Field(default="float32", max_length=50, description="Data type representation")
    description: Optional[str] = Field(None, description="Detailed scientific definition")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Colormap defaults, valid ranges, vector flags")


class VariableCreate(VariableBase):
    """Schema for creating a variable associated with a dataset."""

    dataset_id: uuid.UUID = Field(..., description="Foreign key reference to parent dataset")


class VariableUpdate(BaseModel):
    """Schema for updating a variable."""

    name: Optional[str] = Field(None, max_length=100)
    standard_name: Optional[str] = Field(None, max_length=150)
    long_name: Optional[str] = Field(None, max_length=255)
    units: Optional[str] = Field(None, max_length=50)
    data_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class VariableRead(VariableBase):
    """Schema for returning variable details."""

    id: uuid.UUID
    dataset_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
