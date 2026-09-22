from collections import Counter
from datetime import datetime, timezone
import logging
from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.array_asset import ArrayAsset
from app.models.dataset import Dataset
from app.models.observation import Observation
from app.models.processing_job import ProcessingJob
from app.models.provenance import Provenance
from app.models.variable import Variable
from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.observation import ObservationRepository
from app.repositories.platform import PlatformRepository
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.provenance import ProvenanceRepository
from app.repositories.variable import VariableRepository
from app.schemas.array_asset import ArrayAssetRead
from app.schemas.dataset import DatasetRead
from app.schemas.geometry import geometry_to_shape, shape_to_wkb
from app.schemas.ingestion import (
    DatasetIngestionRequest,
    DatasetIngestionResponse,
    InSituBatchIngestionRequest,
    InSituBatchIngestionResponse,
    MetadataValidationResult,
    SingleArrayAssetIngestionRequest,
)
from app.schemas.processing_job import ProcessingJobRead
from app.schemas.provenance import ProvenanceRead
from app.schemas.variable import VariableRead


logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def validate_dataset_metadata(payload: DatasetIngestionRequest) -> MetadataValidationResult:
    """Validate and extract scientific metadata from a dataset manifest without modifying the database."""
    issues: list[str] = []
    temporal_valid = True
    spatial_valid = True

    # 1. Temporal bounds validation
    if payload.temporal_start and payload.temporal_end:
        if payload.temporal_start > payload.temporal_end:
            temporal_valid = False
            issues.append(
                f"Invalid temporal coverage: temporal_start ({payload.temporal_start.isoformat()}) is after temporal_end ({payload.temporal_end.isoformat()})."
            )

    # 2. Spatial polygon bounds validation
    if payload.spatial_extent:
        coords_rings = payload.spatial_extent.coordinates
        if not coords_rings or len(coords_rings) == 0 or len(coords_rings[0]) < 4:
            spatial_valid = False
            issues.append("Spatial polygon must have at least one linear ring with at least 4 coordinate vertices.")
        else:
            ring = coords_rings[0]
            if ring[0] != ring[-1]:
                spatial_valid = False
                issues.append("Spatial polygon ring must be closed (first coordinate vertex must equal last).")
            for lon, lat in ring:
                if not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
                    spatial_valid = False
                    issues.append(f"Vertex ({lon}, {lat}) is outside valid WGS84 range (lon [-180, 180], lat [-90, 90]).")
                    break

    # 3. Variable parameter validation
    for var in payload.variables:
        if not var.name or len(var.name.strip()) == 0:
            issues.append("Variable name cannot be empty.")
        if var.metadata_json:
            vmin = var.metadata_json.get("valid_min")
            vmax = var.metadata_json.get("valid_max")
            if vmin is not None and vmax is not None and vmin > vmax:
                issues.append(f"Variable '{var.name}' has invalid range: valid_min ({vmin}) > valid_max ({vmax}).")

    # 4. Array asset validation
    allowed_formats = {"NETCDF4", "ZARR", "HDF5", "CSV_INSITU", "CLOUD_ZARR"}
    for asset in payload.array_assets:
        if asset.storage_format.upper() not in allowed_formats:
            issues.append(f"Array asset format '{asset.storage_format}' is not among recognized formats: {sorted(allowed_formats)}.")

    summary = {
        "dataset_type": payload.dataset_type,
        "variables": [v.name for v in payload.variables],
        "array_assets_count": len(payload.array_assets),
        "has_spatial_extent": payload.spatial_extent is not None,
        "has_temporal_bounds": payload.temporal_start is not None or payload.temporal_end is not None,
    }

    return MetadataValidationResult(
        is_valid=len(issues) == 0,
        dataset_name=payload.name,
        dataset_type=payload.dataset_type,
        variables_count=len(payload.variables),
        array_assets_count=len(payload.array_assets),
        temporal_coverage_valid=temporal_valid,
        spatial_coverage_valid=spatial_valid,
        validation_issues=issues,
        extracted_summary=summary,
    )


class IngestionService:
    """Service layer orchestrating atomic scientific dataset and in-situ batch ingestion workflows."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        variable_repo: Optional[VariableRepository] = None,
        asset_repo: Optional[ArrayAssetRepository] = None,
        platform_repo: Optional[PlatformRepository] = None,
        observation_repo: Optional[ObservationRepository] = None,
        job_repo: Optional[ProcessingJobRepository] = None,
        provenance_repo: Optional[ProvenanceRepository] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.variable_repo = variable_repo or VariableRepository()
        self.asset_repo = asset_repo or ArrayAssetRepository()
        self.platform_repo = platform_repo or PlatformRepository()
        self.observation_repo = observation_repo or ObservationRepository()
        self.job_repo = job_repo or ProcessingJobRepository()
        self.provenance_repo = provenance_repo or ProvenanceRepository()

    def validate_metadata(self, payload: DatasetIngestionRequest) -> MetadataValidationResult:
        """Validate and extract metadata from manifest without modifying database."""
        return validate_dataset_metadata(payload)

    def ingest_dataset(self, db: Session, payload: DatasetIngestionRequest) -> DatasetIngestionResponse:
        """Register a dataset along with its scientific variables, array assets, job log, and provenance."""
        # 1. Run strict metadata validation
        validation_report = validate_dataset_metadata(payload)
        if not validation_report.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset metadata validation failed: {'; '.join(validation_report.validation_issues)}",
            )

        # 2. Check uniqueness of dataset name
        existing_ds = self.dataset_repo.get_by_name(db, payload.name)
        if existing_ds:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Dataset with identifier code '{payload.name}' already exists in catalog.",
            )

        # 3. Check for duplicate variable names within manifest
        var_names = [v.name for v in payload.variables]
        if len(var_names) != len(set(var_names)):
            duplicates = [item for item, count in Counter(var_names).items() if count > 1]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate variable names detected in manifest: {duplicates}",
            )


        # 3. Create Dataset entity
        raw_spatial = payload.spatial_extent
        shape_geom = geometry_to_shape(raw_spatial) if raw_spatial else None
        spatial_wkb = shape_to_wkb(shape_geom) if shape_geom else None

        dataset = Dataset(
            name=payload.name,
            title=payload.title,
            description=payload.description,
            source=payload.source,
            source_uri=payload.source_uri,
            dataset_type=payload.dataset_type,
            temporal_start=payload.temporal_start,
            temporal_end=payload.temporal_end,
            spatial_extent=spatial_wkb,
            metadata_json=payload.metadata_json,
        )
        db.add(dataset)
        db.flush()

        # 4. Create Variable entities
        created_variables: list[Variable] = []
        for var_m in payload.variables:
            var_obj = Variable(
                dataset_id=dataset.id,
                name=var_m.name,
                standard_name=var_m.standard_name,
                long_name=var_m.long_name,
                units=var_m.units,
                data_type=var_m.data_type,
                description=var_m.description,
                metadata_json=var_m.metadata_json,
            )
            db.add(var_obj)
            created_variables.append(var_obj)

        # 5. Create ArrayAsset entities
        created_assets: list[ArrayAsset] = []
        for asset_m in payload.array_assets:
            asset_obj = ArrayAsset(
                dataset_id=dataset.id,
                storage_format=asset_m.storage_format,
                uri=asset_m.uri,
                variable_info=asset_m.variable_info,
                dimensions=asset_m.dimensions,
                checksum=asset_m.checksum,
            )
            db.add(asset_obj)
            created_assets.append(asset_obj)

        now_utc = get_utc_now()

        # 6. Create ProcessingJob entry
        job = ProcessingJob(
            dataset_id=dataset.id,
            job_type="DATASET_INGESTION",
            status="COMPLETED",
            initiated_by=payload.initiated_by,
            started_at=now_utc,
            completed_at=now_utc,
            job_metadata={
                "variables_registered": len(created_variables),
                "array_assets_registered": len(created_assets),
                "dataset_type": payload.dataset_type,
            },
        )
        db.add(job)

        # 7. Create Provenance entry
        provenance = Provenance(
            dataset_id=dataset.id,
            action="DATASET_INGESTION",
            source=payload.source_uri or payload.source,
            actor=payload.initiated_by,
            timestamp=now_utc,
            details={
                "manifest_variables_count": len(created_variables),
                "manifest_assets_count": len(created_assets),
                **payload.provenance_details,
            },
        )
        db.add(provenance)

        db.commit()
        db.refresh(dataset)
        db.refresh(job)
        db.refresh(provenance)
        for v in created_variables:
            db.refresh(v)
        for a in created_assets:
            db.refresh(a)

        return DatasetIngestionResponse(
            dataset=DatasetRead.model_validate(dataset),
            variables=[VariableRead.model_validate(v) for v in created_variables],
            array_assets=[ArrayAssetRead.model_validate(a) for a in created_assets],
            processing_job=ProcessingJobRead.model_validate(job),
            provenance_record=ProvenanceRead.model_validate(provenance),
        )

    def ingest_single_array_asset(
        self, db: Session, payload: SingleArrayAssetIngestionRequest
    ) -> ArrayAssetRead:
        """Register a scientific array asset file reference with automatic provenance logging."""
        dataset = self.dataset_repo.get_by_id(db, payload.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target dataset with ID '{payload.dataset_id}' was not found.",
            )

        allowed_formats = {"NETCDF4", "ZARR", "HDF5", "CSV_INSITU", "CLOUD_ZARR"}
        if payload.storage_format.upper() not in allowed_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Storage format '{payload.storage_format}' is not among allowed formats: {sorted(allowed_formats)}.",
            )

        asset = ArrayAsset(
            dataset_id=dataset.id,
            storage_format=payload.storage_format,
            uri=payload.uri,
            variable_info=payload.variable_info,
            dimensions=payload.dimensions,
            checksum=payload.checksum,
        )
        db.add(asset)

        now_utc = get_utc_now()
        provenance = Provenance(
            dataset_id=dataset.id,
            action="ARRAY_ASSET_REGISTRATION",
            source=payload.uri,
            actor=payload.initiated_by,
            timestamp=now_utc,
            details={
                "storage_format": payload.storage_format,
                "dimensions": payload.dimensions,
                "variable_info_keys": list(payload.variable_info.keys()),
                **payload.provenance_details,
            },
        )
        db.add(provenance)

        db.commit()
        db.refresh(asset)
        db.refresh(provenance)
        return ArrayAssetRead.model_validate(asset)

    def ingest_insitu_batch(self, db: Session, payload: InSituBatchIngestionRequest) -> InSituBatchIngestionResponse:

        """Bulk ingest discrete in-situ ocean observation points with foreign-key validation and audit logging."""
        # 1. Validate dataset existence
        dataset = self.dataset_repo.get_by_id(db, payload.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target dataset with ID '{payload.dataset_id}' was not found.",
            )

        # 2. Validate variable existence and ownership
        variable = self.variable_repo.get_by_id(db, payload.variable_id)
        if not variable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target variable with ID '{payload.variable_id}' was not found.",
            )
        if variable.dataset_id != dataset.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variable '{variable.name}' does not belong to dataset '{dataset.name}'.",
            )

        # 3. Validate platforms
        platform_ids = {obs.platform_id for obs in payload.observations if obs.platform_id}
        if payload.default_platform_id:
            platform_ids.add(payload.default_platform_id)

        for plat_id in platform_ids:
            if not self.platform_repo.get_by_id(db, plat_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Referenced platform with ID '{plat_id}' was not found.",
                )

        # 4. Construct observation rows
        obs_records: list[Observation] = []
        qc_counts: Counter[str] = Counter()

        for obs in payload.observations:
            plat_id = obs.platform_id or payload.default_platform_id
            shape_geom = geometry_to_shape(obs.geometry)
            geom_wkb = shape_to_wkb(shape_geom)

            # Validate coordinate bounds
            lon, lat = obs.geometry.coordinates
            if not (-180.0 <= lon <= 180.0) or not (-90.0 <= lat <= 90.0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Coordinates ({lon}, {lat}) are outside valid WGS84 bounding range.",
                )

            qc_counts[str(obs.quality_flag)] += 1
            obs_obj = Observation(
                dataset_id=dataset.id,
                variable_id=variable.id,
                platform_id=plat_id,
                observed_at=obs.observed_at,
                depth_m=obs.depth_m,
                value=obs.value,
                geometry=geom_wkb,
                quality_flag=obs.quality_flag,
                metadata_json=obs.metadata_json,
            )
            obs_records.append(obs_obj)

        db.add_all(obs_records)
        db.flush()

        now_utc = get_utc_now()

        # 5. Create ProcessingJob entry
        job = ProcessingJob(
            dataset_id=dataset.id,
            job_type="DATASET_INGESTION",
            status="COMPLETED",
            initiated_by=payload.initiated_by,
            started_at=now_utc,
            completed_at=now_utc,
            job_metadata={
                "observations_ingested": len(obs_records),
                "variable_name": variable.name,
                "quality_flags_summary": dict(qc_counts),
            },
        )
        db.add(job)

        # 6. Create Provenance entry
        provenance = Provenance(
            dataset_id=dataset.id,
            action="INSITU_BATCH_INGESTION",
            source=f"batch-payload:{len(obs_records)}-records",
            actor=payload.initiated_by,
            timestamp=now_utc,
            details={
                "variable_id": str(variable.id),
                "variable_name": variable.name,
                "records_count": len(obs_records),
                "quality_flags_summary": dict(qc_counts),
                **payload.provenance_details,
            },
        )
        db.add(provenance)

        db.commit()
        db.refresh(job)
        db.refresh(provenance)

        return InSituBatchIngestionResponse(
            dataset_id=dataset.id,
            variable_id=variable.id,
            records_ingested=len(obs_records),
            quality_flags_summary=dict(qc_counts),
            processing_job=ProcessingJobRead.model_validate(job),
            provenance_record=ProvenanceRead.model_validate(provenance),
        )
