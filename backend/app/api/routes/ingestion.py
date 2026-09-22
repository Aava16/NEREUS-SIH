from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.array_asset import ArrayAssetRead
from app.schemas.ingestion import (
    DatasetIngestionRequest,
    DatasetIngestionResponse,
    InSituBatchIngestionRequest,
    InSituBatchIngestionResponse,
    MetadataValidationResult,
    SingleArrayAssetIngestionRequest,
)
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Catalog"])
ingestion_service = IngestionService()


@router.post(
    "/dataset",
    response_model=DatasetIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Atomic Dataset Catalog Registration",
    description="Ingest and catalog a complete oceanographic dataset along with its scientific variables, multidimensional array assets (NetCDF4/Zarr), processing job record, and lineage provenance log.",
)
def ingest_dataset_manifest(
    payload: DatasetIngestionRequest,
    db: Session = Depends(get_db),
) -> DatasetIngestionResponse:
    """Atomically register a complete dataset catalog manifest."""
    return ingestion_service.ingest_dataset(db, payload)


@router.post(
    "/validate-metadata",
    response_model=MetadataValidationResult,
    summary="Validate & Extract Dataset Metadata",
    description="Dry-run validation of a dataset manifest: verifies temporal coverage, spatial coordinate polygons, variable validity ranges, and array dimension specifications without persisting.",
)
def validate_metadata_endpoint(
    payload: DatasetIngestionRequest,
) -> MetadataValidationResult:
    """Extract and validate dataset metadata parameters."""
    return ingestion_service.validate_metadata(payload)


@router.post(
    "/array-asset",
    response_model=ArrayAssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Scientific Array Asset with Provenance",
    description="Register a NetCDF4 or Zarr scientific multidimensional grid file reference and automatically append an audit provenance log.",
)
def ingest_array_asset(
    payload: SingleArrayAssetIngestionRequest,
    db: Session = Depends(get_db),
) -> ArrayAssetRead:
    """Register array asset with provenance linkage."""
    return ingestion_service.ingest_single_array_asset(db, payload)


@router.post(
    "/observations",
    response_model=InSituBatchIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch In-Situ Observation Ingestion",
    description="Batch ingest up to 1000 in-situ observation point measurements with automatic coordinate validation, QC flag summarization, and pipeline job logging.",
)
def ingest_insitu_observations_batch(
    payload: InSituBatchIngestionRequest,
    db: Session = Depends(get_db),
) -> InSituBatchIngestionResponse:
    """Batch ingest in-situ observation measurements."""
    return ingestion_service.ingest_insitu_batch(db, payload)
