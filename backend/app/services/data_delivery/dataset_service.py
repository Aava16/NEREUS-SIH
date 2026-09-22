"""Dataset metadata delivery service for frontend consumption.

Combines PostgreSQL canonical dataset metadata, PostGIS spatial extents,
and underlying scientific array coordinate/dimension metadata into
a frontend-safe JSON representation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import xarray as xr

from app.models.array_asset import ArrayAsset
from app.models.dataset import Dataset
from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.analysis import (
    DepthRangeSummary,
    SpatialExtentSummary,
    TemporalRangeSummary,
)
from app.schemas.data_delivery import FrontendDatasetMetadata
from app.services.analysis.spatial import SpatialAnalyzer
from app.services.analysis.temporal import TemporalAnalyzer
from app.services.scientific_array import ScientificArrayReader


class DeliveryDatasetService:
    """Delivers rich dataset description for frontend catalogs and viewers."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

    def get_dataset_metadata(self, db: Session, dataset_id: UUID) -> FrontendDatasetMetadata:
        """Fetch complete, frontend-safe dataset metadata."""
        dataset = self.dataset_repo.get_by_id(db, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{dataset_id}' not found.",
            )

        # Locate primary array asset
        assets = self.array_repo.list_assets(db, dataset_id=dataset_id)
        primary_asset: Optional[ArrayAsset] = assets[0] if assets else None

        uri_or_path = (
            primary_asset.uri if primary_asset and primary_asset.uri else dataset.source_uri
        )
        storage_format = (
            str(primary_asset.storage_format)
            if primary_asset
            else ("ZARR" if str(uri_or_path or "").endswith(".zarr") else "NETCDF4")
        )

        variables: list[str] = []
        dimensions: dict[str, int] = {}
        spatial_extent: Optional[SpatialExtentSummary] = None
        depth_extent: Optional[DepthRangeSummary] = None
        temporal_extent: Optional[TemporalRangeSummary] = None

        if uri_or_path:
            try:
                with self.reader.open_dataset(uri_or_path, storage_format) as ds:
                    variables = list(ds.data_vars.keys())
                    dimensions = {str(k): int(v) for k, v in ds.sizes.items()}

                    # Spatial and depth analysis
                    spatial_resp = SpatialAnalyzer.analyze_spatial_extent(
                        ds=ds,
                        dataset_id=dataset.id,
                        dataset_name=dataset.name,
                        asset_id=primary_asset.id if primary_asset else None,
                    )
                    spatial_extent = spatial_resp.spatial_extent
                    depth_extent = spatial_resp.depth_range

                    # Temporal analysis
                    try:
                        temp_resp = TemporalAnalyzer.analyze_temporal_extent(
                            ds=ds,
                            dataset_id=dataset.id,
                            dataset_name=dataset.name,
                            asset_id=primary_asset.id if primary_asset else None,
                        )
                        temporal_extent = temp_resp.temporal_range
                    except Exception:
                        temporal_extent = None
            except Exception:
                pass

        if not spatial_extent:
            spatial_extent = SpatialExtentSummary(
                latitude_min=-90.0,
                latitude_max=90.0,
                longitude_min=-180.0,
                longitude_max=180.0,
                latitude_points=0,
                longitude_points=0,
            )

        if not depth_extent:
            depth_extent = DepthRangeSummary(
                depth_min=None,
                depth_max=None,
                depth_levels_count=0,
                levels=[],
            )

        return FrontendDatasetMetadata(
            dataset_id=dataset.id,
            name=dataset.name,
            title=dataset.title,
            description=dataset.description,
            source=dataset.source,
            source_uri=dataset.source_uri,
            dataset_type=str(dataset.dataset_type),
            variables=variables,
            dimensions=dimensions,
            spatial_extent=spatial_extent,
            depth_extent=depth_extent,
            temporal_extent=temporal_extent,
            primary_asset_id=primary_asset.id if primary_asset else None,
            primary_asset_format=str(primary_asset.storage_format) if primary_asset else None,
            metadata_json=dataset.metadata_json or {},
            created_at=dataset.created_at or datetime.utcnow(),
            updated_at=dataset.updated_at or datetime.utcnow(),
        )
