"""Unified scientific data delivery orchestration service.

Bridges canonical PostgreSQL datasets and scientific array assets with
frontend visualization APIs.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.data_delivery import (
    CurrentsDeliveryResponse,
    FrontendDatasetMetadata,
    GridDeliveryResponse,
    ProfileDeliveryResponse,
    SliceDeliveryResponse,
    TimeSeriesDeliveryResponse,
    TransectDeliveryResponse,
    VariableDiscoveryResponse,
)
from app.services.data_delivery.currents_service import DeliveryCurrentsService
from app.services.data_delivery.dataset_service import DeliveryDatasetService
from app.services.data_delivery.grid_service import DeliveryGridService
from app.services.data_delivery.profile_service import DeliveryProfileService
from app.services.data_delivery.slice_service import DeliverySliceService
from app.services.data_delivery.timeseries_service import DeliveryTimeSeriesService
from app.services.data_delivery.variable_service import DeliveryVariableService
from app.services.scientific_array import ScientificArrayReader


class DataDeliveryService:
    """Orchestrator for all scientific data delivery and visualization services."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

        self.dataset_service = DeliveryDatasetService(
            self.dataset_repo, self.array_repo, self.reader
        )
        self.variable_service = DeliveryVariableService(
            self.dataset_repo, self.array_repo, self.reader
        )
        self.grid_service = DeliveryGridService(
            self.dataset_repo, self.array_repo, self.reader
        )
        self.profile_service = DeliveryProfileService(
            self.dataset_repo, self.array_repo, self.reader
        )
        self.timeseries_service = DeliveryTimeSeriesService(
            self.dataset_repo, self.array_repo, self.reader
        )
        self.currents_service = DeliveryCurrentsService(
            self.dataset_repo, self.array_repo, self.reader
        )
        self.slice_service = DeliverySliceService(
            self.dataset_repo, self.array_repo, self.reader
        )

    def get_dataset_metadata(self, db: Session, dataset_id: UUID) -> FrontendDatasetMetadata:
        """Fetch frontend-ready dataset description with coordinates and extents."""
        return self.dataset_service.get_dataset_metadata(db, dataset_id)

    def discover_variables(
        self, db: Session, dataset_id: UUID, asset_id: Optional[UUID] = None
    ) -> VariableDiscoveryResponse:
        """Discover and describe variables within a dataset."""
        return self.variable_service.discover_variables(db, dataset_id, asset_id)

    def get_grid(
        self,
        db: Session,
        dataset_id: UUID,
        variable_name: str,
        time_index: int = 0,
        depth_index: int = 0,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        decimation: int = 1,
        asset_id: Optional[UUID] = None,
    ) -> GridDeliveryResponse:
        """Extract a bounded 2D map/grid slice with LOD decimation."""
        return self.grid_service.get_grid(
            db=db,
            dataset_id=dataset_id,
            variable_name=variable_name,
            time_index=time_index,
            depth_index=depth_index,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            decimation=decimation,
            asset_id=asset_id,
        )

    def get_profile(
        self,
        db: Session,
        dataset_id: UUID,
        variable_name: str,
        latitude: float,
        longitude: float,
        time_index: int = 0,
        asset_id: Optional[UUID] = None,
    ) -> ProfileDeliveryResponse:
        """Extract a vertical depth profile at the nearest grid point to requested coordinates."""
        return self.profile_service.get_profile(
            db=db,
            dataset_id=dataset_id,
            variable_name=variable_name,
            latitude=latitude,
            longitude=longitude,
            time_index=time_index,
            asset_id=asset_id,
        )

    def get_timeseries(
        self,
        db: Session,
        dataset_id: UUID,
        variable_name: str,
        latitude: float,
        longitude: float,
        depth: Optional[float] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        decimation: int = 1,
        asset_id: Optional[UUID] = None,
    ) -> TimeSeriesDeliveryResponse:
        """Extract a point time series sequence across bounded temporal ranges."""
        return self.timeseries_service.get_timeseries(
            db=db,
            dataset_id=dataset_id,
            variable_name=variable_name,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            start_time=start_time,
            end_time=end_time,
            decimation=decimation,
            asset_id=asset_id,
        )

    def get_current_vectors(
        self,
        db: Session,
        dataset_id: UUID,
        u_var: Optional[str] = None,
        v_var: Optional[str] = None,
        w_var: Optional[str] = None,
        time_index: int = 0,
        depth_index: int = 0,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        decimation: int = 1,
        asset_id: Optional[UUID] = None,
    ) -> CurrentsDeliveryResponse:
        """Extract spatial current velocity vectors for visualization."""
        return self.currents_service.get_vectors(
            db=db,
            dataset_id=dataset_id,
            u_var=u_var,
            v_var=v_var,
            w_var=w_var,
            time_index=time_index,
            depth_index=depth_index,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            decimation=decimation,
            asset_id=asset_id,
        )

    def get_slice(
        self,
        db: Session,
        dataset_id: UUID,
        variable_name: str,
        time_index: Optional[int] = None,
        depth_index: Optional[int] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        decimation: int = 1,
        asset_id: Optional[UUID] = None,
    ) -> SliceDeliveryResponse:
        """Extract a bounded slice for any scientific variable."""
        return self.slice_service.get_slice(
            db=db,
            dataset_id=dataset_id,
            variable_name=variable_name,
            time_index=time_index,
            depth_index=depth_index,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            decimation=decimation,
            asset_id=asset_id,
        )

    def get_transect(
        self,
        db: Session,
        dataset_id: UUID,
        variable_name: str,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        num_points: int = 50,
        time_index: int = 0,
        depth_index: int = 0,
        asset_id: Optional[UUID] = None,
    ) -> TransectDeliveryResponse:
        """Extract a 1D scientific transect between two coordinates."""
        return self.grid_service.get_transect(
            db=db,
            dataset_id=dataset_id,
            variable_name=variable_name,
            lat1=lat1,
            lon1=lon1,
            lat2=lat2,
            lon2=lon2,
            num_points=num_points,
            time_index=time_index,
            depth_index=depth_index,
            asset_id=asset_id,
        )

