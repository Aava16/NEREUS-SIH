"""High-level scientific data analysis orchestration service.

Bridges canonical PostgreSQL dataset metadata with the scientific array
analysis engines without loading large arrays into PostgreSQL.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import xarray as xr

from app.models.array_asset import ArrayAsset
from app.models.dataset import Dataset
from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.analysis import (
    CurrentsAnalysisResponse,
    DatasetAnalysisSummaryResponse,
    DatasetStatisticsResponse,
    DepthRangeSummary,
    SpatialAnalysisResponse,
    SpatialExtentSummary,
    TemporalAnalysisResponse,
    TemporalRangeSummary,
    VariableStatistics,
)
from app.services.analysis.currents import CurrentsAnalyzer
from app.services.analysis.derived import DerivedAnalyzer
from app.services.analysis.spatial import SpatialAnalyzer
from app.services.analysis.statistics import StatisticsAnalyzer
from app.services.analysis.temporal import TemporalAnalyzer
from app.services.scientific_array import ScientificArrayReader


class ScientificAnalysisService:
    """Orchestrates scientific analysis across registered ocean datasets."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

    def _resolve_dataset_and_asset(
        self, db: Session, dataset_id: UUID, asset_id: UUID | None = None
    ) -> tuple[Dataset, ArrayAsset | None, str, str]:
        """Resolve a dataset and locate its primary scientific array asset URI and format.

        Args:
            db: SQLAlchemy database session
            dataset_id: Canonical dataset identifier
            asset_id: Optional specific array asset identifier

        Returns:
            Tuple of (Dataset record, ArrayAsset record | None, uri_or_path, format_type).
        """
        dataset = self.dataset_repo.get_by_id(db, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{dataset_id}' not found.",
            )

        asset: ArrayAsset | None = None
        if asset_id:
            asset = self.array_repo.get_by_id(db, asset_id)
            if not asset or asset.dataset_id != dataset_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Array asset '{asset_id}' not found for dataset '{dataset_id}'.",
                )
        else:
            # Look up primary or first registered asset for this dataset
            assets = self.array_repo.list_assets(db, dataset_id=dataset_id)
            if assets:
                asset = assets[0]

        # Determine file path to open
        uri_or_path: str | None = None
        format_type = "NETCDF4"

        if asset and asset.uri:
            uri_or_path = asset.uri
            format_type = str(asset.storage_format)
        elif dataset.source_uri:
            uri_or_path = dataset.source_uri
            if uri_or_path.endswith(".zarr") or uri_or_path.endswith(".zarr/"):
                format_type = "ZARR"
            else:
                format_type = "NETCDF4"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset '{dataset_id}' has no registered scientific array asset or storage URI.",
            )

        return dataset, asset, uri_or_path, format_type

    def get_dataset_statistics(
        self,
        db: Session,
        dataset_id: UUID,
        variable: str | None = None,
        asset_id: UUID | None = None,
    ) -> DatasetStatisticsResponse:
        """Compute statistical metrics for dataset variables.

        Args:
            db: SQLAlchemy database session
            dataset_id: Dataset identifier
            variable: Optional specific variable name (if None, calculates for all data vars)
            asset_id: Optional array asset identifier
        """
        dataset, asset, uri, storage_format = self._resolve_dataset_and_asset(
            db, dataset_id, asset_id
        )

        with self.reader.open_dataset(uri, storage_format) as ds:
            variables_stats: dict[str, VariableStatistics] = {}

            if variable:
                if variable not in ds.data_vars and variable not in ds.coords:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Variable '{variable}' not found in dataset '{dataset.name}'. Available: {list(ds.data_vars.keys())}",
                    )
                da = ds[variable]
                variables_stats[variable] = StatisticsAnalyzer.compute_variable_statistics(
                    da, variable
                )
            else:
                # Calculate for all data variables
                for var_name in ds.data_vars:
                    da = ds[var_name]
                    variables_stats[str(var_name)] = StatisticsAnalyzer.compute_variable_statistics(
                        da, str(var_name)
                    )

            return DatasetStatisticsResponse(
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                asset_id=asset.id if asset else None,
                variables=variables_stats,
                analyzed_at=datetime.now(timezone.utc),
            )

    def get_spatial_analysis(
        self, db: Session, dataset_id: UUID, asset_id: UUID | None = None
    ) -> SpatialAnalysisResponse:
        """Analyze spatial extents, coordinates, and depth ranges.

        Args:
            db: SQLAlchemy database session
            dataset_id: Dataset identifier
            asset_id: Optional array asset identifier
        """
        dataset, asset, uri, storage_format = self._resolve_dataset_and_asset(
            db, dataset_id, asset_id
        )
        with self.reader.open_dataset(uri, storage_format) as ds:
            return SpatialAnalyzer.analyze_spatial_extent(
                ds=ds,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                asset_id=asset.id if asset else None,
            )

    def get_temporal_analysis(
        self, db: Session, dataset_id: UUID, asset_id: UUID | None = None
    ) -> TemporalAnalysisResponse:
        """Analyze temporal range, resolution, and step intervals.

        Args:
            db: SQLAlchemy database session
            dataset_id: Dataset identifier
            asset_id: Optional array asset identifier
        """
        dataset, asset, uri, storage_format = self._resolve_dataset_and_asset(
            db, dataset_id, asset_id
        )
        with self.reader.open_dataset(uri, storage_format) as ds:
            try:
                return TemporalAnalyzer.analyze_temporal_extent(
                    ds=ds,
                    dataset_id=dataset.id,
                    dataset_name=dataset.name,
                    asset_id=asset.id if asset else None,
                )
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(err),
                )

    def get_currents_analysis(
        self,
        db: Session,
        dataset_id: UUID,
        u_var: str | None = None,
        v_var: str | None = None,
        w_var: str | None = None,
        asset_id: UUID | None = None,
    ) -> CurrentsAnalysisResponse:
        """Analyze ocean current velocity fields, magnitude, and direction.

        Args:
            db: SQLAlchemy database session
            dataset_id: Dataset identifier
            u_var: Optional eastward velocity variable name
            v_var: Optional northward velocity variable name
            w_var: Optional vertical velocity variable name
            asset_id: Optional array asset identifier
        """
        dataset, asset, uri, storage_format = self._resolve_dataset_and_asset(
            db, dataset_id, asset_id
        )
        with self.reader.open_dataset(uri, storage_format) as ds:
            try:
                return CurrentsAnalyzer.analyze_currents(
                    ds=ds,
                    dataset_id=dataset.id,
                    dataset_name=dataset.name,
                    asset_id=asset.id if asset else None,
                    u_name=u_var,
                    v_name=v_var,
                    w_name=w_var,
                )
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(err),
                )

    def get_dataset_summary(
        self, db: Session, dataset_id: UUID, asset_id: UUID | None = None
    ) -> DatasetAnalysisSummaryResponse:
        """Generate a complete analysis summary combining spatial, temporal, and variable distributions.

        Args:
            db: SQLAlchemy database session
            dataset_id: Dataset identifier
            asset_id: Optional array asset identifier
        """
        dataset, asset, uri, storage_format = self._resolve_dataset_and_asset(
            db, dataset_id, asset_id
        )
        with self.reader.open_dataset(uri, storage_format) as ds:
            # Spatial analysis
            spatial_resp = SpatialAnalyzer.analyze_spatial_extent(
                ds=ds,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                asset_id=asset.id if asset else None,
            )

            # Temporal analysis (safe if missing)
            temporal_summary: TemporalRangeSummary | None = None
            try:
                temp_resp = TemporalAnalyzer.analyze_temporal_extent(
                    ds=ds,
                    dataset_id=dataset.id,
                    dataset_name=dataset.name,
                    asset_id=asset.id if asset else None,
                )
                temporal_summary = temp_resp.temporal_range
            except Exception:
                temporal_summary = None

            # Variable summary (up to first 5 data variables)
            var_summary: dict[str, VariableStatistics] = {}
            for var_name in list(ds.data_vars.keys())[:5]:
                var_summary[str(var_name)] = StatisticsAnalyzer.compute_variable_statistics(
                    ds[var_name], str(var_name)
                )

            data_type_str = str(dataset.dataset_type)
            asset_format_str = str(asset.storage_format) if asset else None

            return DatasetAnalysisSummaryResponse(
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                data_type=data_type_str,
                asset_id=asset.id if asset else None,
                asset_format=asset_format_str,
                spatial_extent=spatial_resp.spatial_extent,
                depth_range=spatial_resp.depth_range,
                temporal_range=temporal_summary,
                available_variables=list(ds.data_vars.keys()),
                variables_summary=var_summary,
                analyzed_at=datetime.now(timezone.utc),
            )
