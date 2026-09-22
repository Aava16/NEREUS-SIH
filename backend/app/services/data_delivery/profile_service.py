"""Vertical depth profile delivery service.

Extracts vertical profiles across depth levels for specified or nearest-neighbor
ocean coordinates with missing-value safety.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import xarray as xr

from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.data_delivery import ProfileDeliveryResponse
from app.services.scientific_array import ScientificArrayReader


class DeliveryProfileService:
    """Delivers vertical water column depth profiles for oceanographic stations and grid points."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

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
        """Extract vertical profile for the nearest grid point to requested coordinates."""
        dataset = self.dataset_repo.get_by_id(db, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with ID '{dataset_id}' not found.",
            )

        asset = None
        if asset_id:
            asset = self.array_repo.get_by_id(db, asset_id)
        else:
            assets = self.array_repo.list_assets(db, dataset_id=dataset_id)
            if assets:
                asset = assets[0]

        uri_or_path = asset.uri if asset and asset.uri else dataset.source_uri
        storage_format = str(asset.storage_format) if asset else "NETCDF4"

        if not uri_or_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dataset '{dataset_id}' has no registered scientific asset.",
            )

        with self.reader.open_dataset(uri_or_path, storage_format) as ds:
            if variable_name not in ds:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variable '{variable_name}' not found in dataset '{dataset.name}'. Available: {list(ds.data_vars.keys())}",
                )

            da = ds[variable_name]
            coords_map = ScientificArrayReader.identify_standard_coords(ds)
            lat_coord = coords_map.get("lat")
            lon_coord = coords_map.get("lon")
            depth_coord = coords_map.get("depth")
            time_coord = coords_map.get("time")

            if not depth_coord or depth_coord not in ds or depth_coord not in da.dims:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Variable '{variable_name}' in dataset '{dataset.name}' does not have a depth dimension for vertical profiling.",
                )

            if not lat_coord or not lon_coord or lat_coord not in ds or lon_coord not in ds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset '{dataset.name}' lacks standard spatial coordinates (latitude/longitude).",
                )

            # Nearest-neighbor lookup for lat/lon
            lat_vals = np.asarray(ds[lat_coord].values, dtype=np.float64)
            lon_vals = np.asarray(ds[lon_coord].values, dtype=np.float64)

            lat_idx = int(np.argmin(np.abs(lat_vals - latitude)))
            lon_idx = int(np.argmin(np.abs(lon_vals - longitude)))

            actual_lat = float(lat_vals[lat_idx])
            actual_lon = float(lon_vals[lon_idx])

            # Time index selection
            selector: dict[str, Any] = {
                lat_coord: lat_idx,
                lon_coord: lon_idx,
            }
            time_str: Optional[str] = None

            if time_coord and time_coord in da.dims:
                t_size = int(ds.sizes[time_coord])
                if time_index < 0 or time_index >= t_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Time index {time_index} out of range [0, {t_size - 1}].",
                    )
                selector[time_coord] = time_index
                try:
                    time_str = str(ds[time_coord].values[time_index])
                except Exception:
                    time_str = None

            # Extract 1D depth profile array
            da_profile = da.isel(selector)
            depth_vals = np.asarray(ds[depth_coord].values, dtype=np.float64)
            profile_vals = np.asarray(da_profile.values, dtype=np.float64)

            # Format values with None for NaNs
            clean_depths: List[float] = []
            clean_values: List[Optional[float]] = []
            valid_count = 0

            for d, v in zip(depth_vals, profile_vals):
                clean_depths.append(round(float(d), 4))
                if np.isfinite(v):
                    clean_values.append(round(float(v), 6))
                    valid_count += 1
                else:
                    clean_values.append(None)

            units = str(da.attrs.get("units", "")) or None

            return ProfileDeliveryResponse(
                dataset_id=dataset.id,
                variable_name=variable_name,
                units=units,
                requested_latitude=round(latitude, 6),
                requested_longitude=round(longitude, 6),
                actual_latitude=round(actual_lat, 6),
                actual_longitude=round(actual_lon, 6),
                time=time_str,
                depths=clean_depths,
                values=clean_values,
                valid_levels=valid_count,
                delivered_at=datetime.now(timezone.utc),
            )
