"""Map and spatial grid data delivery service.

Extracts bounded 2D spatial grid matrices (latitudes x longitudes)
with Level-of-Detail (LOD) decimation and NaN-safe JSON serialization
for web maps, heatmaps, and raster contours.
"""

from datetime import datetime, timezone
import math
from typing import Any, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import xarray as xr

from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.data_delivery import (
    DownsampleMetadata,
    GridDeliveryResponse,
    TransectDeliveryResponse,
    TransectPoint,
)
from app.services.scientific_array import ScientificArrayReader

# Hard safety limit for browser memory / payload size
MAX_GRID_CELLS_LIMIT = 250_000


class DeliveryGridService:
    """Delivers 2D spatial grid slices optimized for web map rendering."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

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
        """Extract a bounded 2D spatial grid (latitudes x longitudes) for map display."""
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

            if not lat_coord or not lon_coord or lat_coord not in ds or lon_coord not in ds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset '{dataset.name}' lacks standard spatial coordinates (latitude/longitude).",
                )

            # Reduce non-spatial dimensions (time, depth)
            selector: dict[str, Any] = {}
            time_str: Optional[str] = None
            depth_val: Optional[float] = None

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

            if depth_coord and depth_coord in da.dims:
                d_size = int(ds.sizes[depth_coord])
                if depth_index < 0 or depth_index >= d_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Depth index {depth_index} out of range [0, {d_size - 1}].",
                    )
                selector[depth_coord] = depth_index
                try:
                    depth_val = float(ds[depth_coord].values[depth_index])
                except Exception:
                    depth_val = None

            # Apply index selections
            if selector:
                da_2d = da.isel(selector)
            else:
                da_2d = da

            # Spatial subsetting via bounding box
            lat_vals = np.asarray(ds[lat_coord].values, dtype=np.float64)
            lon_vals = np.asarray(ds[lon_coord].values, dtype=np.float64)

            # Check for 1D coordinate vectors
            if lat_vals.ndim == 1 and lon_vals.ndim == 1:
                lat_mask = np.ones(len(lat_vals), dtype=bool)
                lon_mask = np.ones(len(lon_vals), dtype=bool)

                if min_lat is not None:
                    lat_mask &= lat_vals >= min_lat
                if max_lat is not None:
                    lat_mask &= lat_vals <= max_lat
                if min_lon is not None:
                    lon_mask &= lon_vals >= min_lon
                if max_lon is not None:
                    lon_mask &= lon_vals <= max_lon

                if not np.any(lat_mask) or not np.any(lon_mask):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Requested spatial bounding box does not intersect dataset coordinates.",
                    )

                lat_indices = np.where(lat_mask)[0]
                lon_indices = np.where(lon_mask)[0]

                da_subset = da_2d.isel({lat_coord: lat_indices, lon_coord: lon_indices})
                sub_lats = lat_vals[lat_indices]
                sub_lons = lon_vals[lon_indices]
            else:
                da_subset = da_2d
                sub_lats = lat_vals
                sub_lons = lon_vals

            # Size safety limit check
            total_raw_cells = int(sub_lats.size * sub_lons.size)
            decimation_factor = max(1, decimation)

            if (total_raw_cells / (decimation_factor**2)) > MAX_GRID_CELLS_LIMIT:
                # Calculate required decimation factor to fit limit
                required_factor = int(math.ceil(math.sqrt(total_raw_cells / MAX_GRID_CELLS_LIMIT)))
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Requested grid contains {total_raw_cells} cells, exceeding safety limit of {MAX_GRID_CELLS_LIMIT}. "
                        f"Please narrow your spatial bounding box or set decimation factor to at least {required_factor}."
                    ),
                )

            # Apply decimation stride if > 1
            if decimation_factor > 1:
                da_final = da_subset.isel(
                    {lat_coord: slice(None, None, decimation_factor), lon_coord: slice(None, None, decimation_factor)}
                )
                final_lats = sub_lats[::decimation_factor]
                final_lons = sub_lons[::decimation_factor]
            else:
                da_final = da_subset
                final_lats = sub_lats
                final_lons = sub_lons

            # Extract 2D numpy matrix
            raw_matrix = np.asarray(da_final.values, dtype=np.float64)
            # Ensure shape is (len(final_lats), len(final_lons))
            if raw_matrix.ndim > 2:
                raw_matrix = np.squeeze(raw_matrix)

            # Replace NaNs/Infs with None for JSON serialization
            finite_mask = np.isfinite(raw_matrix)
            valid_vals = raw_matrix[finite_mask]

            min_val = float(np.min(valid_vals)) if valid_vals.size > 0 else None
            max_val = float(np.max(valid_vals)) if valid_vals.size > 0 else None

            # Build serializable list of lists
            values_matrix: List[List[Optional[float]]] = []
            for row in raw_matrix:
                row_list: List[Optional[float]] = []
                for val in row:
                    if np.isfinite(val):
                        row_list.append(round(float(val), 6))
                    else:
                        row_list.append(None)
                values_matrix.append(row_list)

            units = str(da.attrs.get("units", "")) or None
            returned_points = int(len(final_lats) * len(final_lons))

            return GridDeliveryResponse(
                dataset_id=dataset.id,
                variable_name=variable_name,
                units=units,
                time=time_str,
                depth=depth_val,
                latitudes=[round(float(lat), 6) for lat in final_lats],
                longitudes=[round(float(lon), 6) for lon in final_lons],
                values=values_matrix,
                min_value=round(min_val, 6) if min_val is not None else None,
                max_value=round(max_val, 6) if max_val is not None else None,
                downsample=DownsampleMetadata(
                    downsampled=(decimation_factor > 1),
                    original_points=total_raw_cells,
                    returned_points=returned_points,
                    decimation_factor=decimation_factor,
                ),
                delivered_at=datetime.now(timezone.utc),
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
        """Extract a 1D scientific transect between two geographical coordinates (Point A to Point B)."""
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

        num_points = max(2, min(500, num_points))

        with self.reader.open_dataset(uri_or_path, storage_format) as ds:
            if variable_name not in ds:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variable '{variable_name}' not found in dataset.",
                )

            da = ds[variable_name]
            coords_map = ScientificArrayReader.identify_standard_coords(ds)
            lat_coord = coords_map.get("lat")
            lon_coord = coords_map.get("lon")
            time_coord = coords_map.get("time")
            depth_coord = coords_map.get("depth")

            if not lat_coord or not lon_coord or lat_coord not in ds or lon_coord not in ds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Variable '{variable_name}' lacks standard spatial coordinates (lat/lon).",
                )

            # Slice time and depth if present
            selector: dict[str, Any] = {}
            time_str: Optional[str] = None
            depth_val: Optional[float] = None

            if time_coord and time_coord in da.dims:
                t_size = int(ds.sizes[time_coord])
                t_idx = max(0, min(time_index, t_size - 1))
                selector[time_coord] = t_idx
                try:
                    time_str = str(ds[time_coord].values[t_idx])
                except Exception:
                    time_str = None

            if depth_coord and depth_coord in da.dims:
                d_size = int(ds.sizes[depth_coord])
                d_idx = max(0, min(depth_index, d_size - 1))
                selector[depth_coord] = d_idx
                try:
                    depth_val = float(ds[depth_coord].values[d_idx])
                except Exception:
                    depth_val = None

            da_slice = da.isel(selector) if selector else da

            # Generate interpolated sample coordinates
            sample_lats = np.linspace(lat1, lat2, num_points)
            sample_lons = np.linspace(lon1, lon2, num_points)

            # Haversine distance helper
            r_earth = 6371.0  # km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
            total_dist_km = 2.0 * r_earth * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

            lat_vals = np.asarray(ds[lat_coord].values, dtype=np.float64)
            lon_vals = np.asarray(ds[lon_coord].values, dtype=np.float64)

            # Query data at sample coordinates using nearest grid neighbor
            points: List[TransectPoint] = []
            values_list: List[float] = []

            for i in range(num_points):
                s_lat = float(sample_lats[i])
                s_lon = float(sample_lons[i])
                dist_km = float((i / (num_points - 1)) * total_dist_km)

                lat_idx = int(np.argmin(np.abs(lat_vals - s_lat)))
                lon_idx = int(np.argmin(np.abs(lon_vals - s_lon)))

                try:
                    pt_val = da_slice.isel({lat_coord: lat_idx, lon_coord: lon_idx}).values
                    val_float = float(pt_val)
                    if np.isfinite(val_float):
                        points.append(TransectPoint(
                            latitude=round(s_lat, 6),
                            longitude=round(s_lon, 6),
                            distance_km=round(dist_km, 3),
                            value=round(val_float, 6),
                        ))
                        values_list.append(val_float)
                    else:
                        points.append(TransectPoint(
                            latitude=round(s_lat, 6),
                            longitude=round(s_lon, 6),
                            distance_km=round(dist_km, 3),
                            value=None,
                        ))
                except Exception:
                    points.append(TransectPoint(
                        latitude=round(s_lat, 6),
                        longitude=round(s_lon, 6),
                        distance_km=round(dist_km, 3),
                        value=None,
                    ))


            units = str(da.attrs.get("units", "")) or None
            min_val = float(np.min(values_list)) if values_list else None
            max_val = float(np.max(values_list)) if values_list else None

            return TransectDeliveryResponse(
                dataset_id=dataset.id,
                variable_name=variable_name,
                units=units,
                time=time_str,
                depth=depth_val,
                start_latitude=round(lat1, 6),
                start_longitude=round(lon1, 6),
                end_latitude=round(lat2, 6),
                end_longitude=round(lon2, 6),
                points=points,
                total_points=len(points),
                total_distance_km=round(total_dist_km, 3),
                min_value=round(min_val, 6) if min_val is not None else None,
                max_value=round(max_val, 6) if max_val is not None else None,
                delivered_at=datetime.now(timezone.utc),
            )

