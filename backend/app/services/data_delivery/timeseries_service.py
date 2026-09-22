"""Point time-series data delivery service.

Extracts temporal sequences at specific geographical locations and depths
with bounded time ranges and LOD sampling.
"""

from datetime import datetime, timezone
import math
from typing import Any, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
import xarray as xr

from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.data_delivery import (
    DownsampleMetadata,
    TimeSeriesDeliveryResponse,
    TimeSeriesPoint,
)
from app.services.scientific_array import ScientificArrayReader

MAX_TIMESERIES_LIMIT = 10_000


class DeliveryTimeSeriesService:
    """Delivers temporal sequences for specific ocean locations and stations."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

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
        """Extract time series sequence for a given coordinate point."""
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
            time_coord = coords_map.get("time")
            depth_coord = coords_map.get("depth")

            if not time_coord or time_coord not in ds or time_coord not in da.dims:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Variable '{variable_name}' in dataset '{dataset.name}' does not have a temporal dimension for time-series extraction.",
                )

            # Nearest spatial point
            selector: dict[str, Any] = {}
            actual_lat = latitude
            actual_lon = longitude

            if lat_coord and lat_coord in ds and lat_coord in da.dims:
                lat_vals = np.asarray(ds[lat_coord].values, dtype=np.float64)
                lat_idx = int(np.argmin(np.abs(lat_vals - latitude)))
                selector[lat_coord] = lat_idx
                actual_lat = float(lat_vals[lat_idx])

            if lon_coord and lon_coord in ds and lon_coord in da.dims:
                lon_vals = np.asarray(ds[lon_coord].values, dtype=np.float64)
                lon_idx = int(np.argmin(np.abs(lon_vals - longitude)))
                selector[lon_coord] = lon_idx
                actual_lon = float(lon_vals[lon_idx])

            # Depth selection
            actual_depth = depth
            if depth_coord and depth_coord in ds and depth_coord in da.dims:
                depth_vals = np.asarray(ds[depth_coord].values, dtype=np.float64)
                if depth is not None:
                    depth_idx = int(np.argmin(np.abs(depth_vals - depth)))
                else:
                    depth_idx = 0
                selector[depth_coord] = depth_idx
                actual_depth = float(depth_vals[depth_idx])

            # Select 1D time series
            da_ts = da.isel(selector)

            # Filter temporal bounds if provided
            time_var = ds[time_coord]
            raw_times = time_var.values

            # Convert times to string ISO representations
            try:
                pd_times = pd.to_datetime(raw_times)
                iso_times = [t.isoformat() for t in pd_times]
            except Exception:
                iso_times = [str(t) for t in raw_times]

            # Range filtering
            indices = np.arange(len(iso_times))
            if start_time:
                indices = indices[[i for i, t in enumerate(iso_times) if t >= start_time]]
            if end_time:
                indices = indices[[i for i, t in enumerate(iso_times) if t <= end_time]]

            if len(indices) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Requested temporal range does not intersect dataset timesteps.",
                )

            total_raw_points = len(indices)
            decimation_factor = max(1, decimation)

            if (total_raw_points / decimation_factor) > MAX_TIMESERIES_LIMIT:
                required_factor = int(math.ceil(total_raw_points / MAX_TIMESERIES_LIMIT))
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Requested time series contains {total_raw_points} steps, exceeding safety limit of {MAX_TIMESERIES_LIMIT}. "
                        f"Please narrow your start/end dates or increase decimation factor to at least {required_factor}."
                    ),
                )

            if decimation_factor > 1:
                indices = indices[::decimation_factor]

            ts_values = np.asarray(da_ts.values, dtype=np.float64)[indices]

            points: List[TimeSeriesPoint] = []
            for idx, val in zip(indices, ts_values):
                val_clean = round(float(val), 6) if np.isfinite(val) else None
                points.append(
                    TimeSeriesPoint(
                        timestamp=iso_times[idx],
                        value=val_clean,
                    )
                )

            units = str(da.attrs.get("units", "")) or None

            return TimeSeriesDeliveryResponse(
                dataset_id=dataset.id,
                variable_name=variable_name,
                units=units,
                latitude=round(actual_lat, 6),
                longitude=round(actual_lon, 6),
                depth=round(actual_depth, 4) if actual_depth is not None else None,
                points=points,
                total_points=len(points),
                downsample=DownsampleMetadata(
                    downsampled=(decimation_factor > 1),
                    original_points=total_raw_points,
                    returned_points=len(points),
                    decimation_factor=decimation_factor,
                ),
                delivered_at=datetime.now(timezone.utc),
            )
