from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.array_asset import ArrayAssetRead
from app.schemas.dataset import DatasetRead
from app.schemas.geometry import GeoJSONPoint, GeoJSONPolygon
from app.schemas.processing_job import ProcessingJobRead
from app.schemas.provenance import ProvenanceRead
from app.schemas.variable import VariableRead


class DatasetVariableManifest(BaseModel):
    """Scientific parameter manifest for dataset ingestion."""

    name: str = Field(..., max_length=100, description="Machine parameter identifier (e.g., temperature, salinity)")
    standard_name: Optional[str] = Field(None, max_length=150, description="CF standard name (e.g., sea_water_temperature)")
    long_name: Optional[str] = Field(None, max_length=255, description="Human-readable parameter description")
    units: Optional[str] = Field(None, max_length=50, description="Physical units (e.g., degC, PSU, m/s)")
    data_type: str = Field(default="float32", max_length=50, description="Numeric data type")
    description: Optional[str] = Field(None, description="Detailed scientific definition")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Parameter attributes and colormaps")


class DatasetArrayAssetManifest(BaseModel):
    """Scientific multidimensional grid file manifest (NetCDF4 / Zarr)."""

    storage_format: str = Field(..., max_length=50, description="Storage format: NETCDF4, ZARR, HDF5")
    uri: str = Field(..., max_length=512, description="Filesystem or object storage S3/GCS URI")
    variable_info: Dict[str, Any] = Field(default_factory=dict, description="Internal array keys and mapping")
    dimensions: Dict[str, Any] = Field(default_factory=dict, description="Dimension ordering (time, depth, lat, lon)")
    checksum: Optional[str] = Field(None, max_length=128, description="Integrity checksum")


class DatasetIngestionRequest(BaseModel):
    """Complete manifest for atomic dataset registration with variables and array assets."""

    name: str = Field(..., max_length=100, description="Unique machine code name for dataset")
    title: str = Field(..., max_length=255, description="Human-readable title")
    description: Optional[str] = None
    source: Optional[str] = Field(None, max_length=255, description="Originator institution (e.g., INCOIS, CMEMS)")
    source_uri: Optional[str] = Field(None, max_length=512, description="Source download URL or provider endpoint")
    dataset_type: str = Field(
        ...,
        max_length=50,
        description="Dataset type: MODEL_FORECAST, REANALYSIS, SATELLITE_OBSERVATION, CLIMATOLOGY, IN_SITU_NETWORK",
    )
    temporal_start: Optional[datetime] = None
    temporal_end: Optional[datetime] = None
    spatial_extent: Optional[GeoJSONPolygon] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    variables: List[DatasetVariableManifest] = Field(default_factory=list, description="Variables contained in this dataset")
    array_assets: List[DatasetArrayAssetManifest] = Field(default_factory=list, description="Array asset files")
    initiated_by: Optional[str] = Field(default="ingestion-pipeline", max_length=128, description="User or pipeline actor")
    provenance_details: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance metadata")


class DatasetIngestionResponse(BaseModel):
    """Response returned upon successful atomic dataset ingestion."""

    dataset: DatasetRead
    variables: List[VariableRead]
    array_assets: List[ArrayAssetRead]
    processing_job: ProcessingJobRead
    provenance_record: ProvenanceRead

    model_config = ConfigDict(from_attributes=True)


class InSituPointManifest(BaseModel):
    """Single in-situ observation point within a batch ingestion request."""

    platform_id: Optional[uuid.UUID] = Field(None, description="Observation platform ID if known")
    observed_at: datetime = Field(..., description="Observation capture UTC timestamp")
    depth_m: Optional[float] = Field(None, description="Depth in meters (positive downward)")
    value: float = Field(..., description="Measured physical value")
    geometry: GeoJSONPoint = Field(..., description="GeoJSON Point representing (longitude, latitude)")
    quality_flag: int = Field(default=1, description="QC flag (1=Good, 2=Probably Good, 3=Bad, 4=Rejected)")
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class InSituBatchIngestionRequest(BaseModel):
    """Batch ingestion manifest for discrete in-situ ocean observation points."""

    dataset_id: uuid.UUID = Field(..., description="Target dataset ID")
    variable_id: uuid.UUID = Field(..., description="Target variable ID")
    default_platform_id: Optional[uuid.UUID] = Field(None, description="Fallback platform ID if not set per point")
    observations: List[InSituPointManifest] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of observation points to ingest (up to 1000 per batch)",
    )
    initiated_by: Optional[str] = Field(default="in-situ-loader", max_length=128)
    provenance_details: Dict[str, Any] = Field(default_factory=dict)


class InSituBatchIngestionResponse(BaseModel):
    """Summary response for batch in-situ observation ingestion."""

    dataset_id: uuid.UUID
    variable_id: uuid.UUID
    records_ingested: int
    quality_flags_summary: Dict[str, int]
    processing_job: ProcessingJobRead
    provenance_record: ProvenanceRead


class MetadataValidationResult(BaseModel):
    """Diagnostic validation and extraction report for a dataset manifest."""

    is_valid: bool
    dataset_name: str
    dataset_type: str
    variables_count: int
    array_assets_count: int
    temporal_coverage_valid: bool
    spatial_coverage_valid: bool
    validation_issues: List[str] = Field(default_factory=list)
    extracted_summary: Dict[str, Any] = Field(default_factory=dict)


class SingleArrayAssetIngestionRequest(BaseModel):
    """Schema for registering a standalone scientific array asset with provenance linkage."""

    dataset_id: uuid.UUID = Field(..., description="Parent dataset ID")
    storage_format: str = Field(..., max_length=50, description="Format: NETCDF4, ZARR, HDF5")
    uri: str = Field(..., max_length=512, description="Storage URI")
    variable_info: Dict[str, Any] = Field(default_factory=dict)
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    checksum: Optional[str] = Field(None, max_length=128)
    initiated_by: Optional[str] = Field(default="asset-registry-pipeline", max_length=128)
    provenance_details: Dict[str, Any] = Field(default_factory=dict)

