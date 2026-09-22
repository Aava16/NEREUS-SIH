"""Ocean current vector field data delivery service.

Extracts sampled velocity vectors (latitude, longitude, u, v, w, speed, direction)
for particle stream animations and vector arrow visualizers.
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
    CurrentVectorItem,
    CurrentsDeliveryResponse,
    DownsampleMetadata,
)
from app.services.scientific_array import ScientificArrayReader

MAX_VECTORS_LIMIT = 50_000


class DeliveryCurrentsService:
    """Delivers velocity vector fields optimized for vector arrow and particle animation layers."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

    def get_vectors(
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
        """Extract spatial grid of current velocity vectors."""
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
            # Auto-detect U and V if omitted
            var_names_lower = {name.lower(): name for name in ds.data_vars.keys()}
            explicit_2d = bool(u_var and v_var and not w_var)

            if not u_var:
                for candidate in ["u", "uo", "u_current", "u_velocity", "eastward_sea_water_velocity", "water_u"]:
                    if candidate in var_names_lower:
                        u_var = var_names_lower[candidate]
                        break

            if not v_var:
                for candidate in ["v", "vo", "v_current", "v_velocity", "northward_sea_water_velocity", "water_v"]:
                    if candidate in var_names_lower:
                        v_var = var_names_lower[candidate]
                        break

            if not explicit_2d and not w_var:
                for candidate in ["w", "wo", "w_current", "w_velocity", "upward_sea_water_velocity", "water_w"]:
                    if candidate in var_names_lower:
                        w_var = var_names_lower[candidate]
                        break

            if not u_var or u_var not in ds or not v_var or v_var not in ds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Velocity components (u, v) not found in dataset '{dataset.name}'.",
                )

            da_u = ds[u_var]
            da_v = ds[v_var]
            has_w = bool(w_var and w_var in ds)
            da_w = ds[w_var] if has_w else None

            coords_map = ScientificArrayReader.identify_standard_coords(ds)
            lat_coord = coords_map.get("lat")
            lon_coord = coords_map.get("lon")
            time_coord = coords_map.get("time")
            depth_coord = coords_map.get("depth")

            if not lat_coord or not lon_coord or lat_coord not in ds or lon_coord not in ds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset '{dataset.name}' lacks standard spatial coordinates (lat, lon).",
                )

            # Reduce time and depth dimensions
            selector: dict[str, Any] = {}
            time_str: Optional[str] = None
            depth_val: Optional[float] = None

            if time_coord and time_coord in da_u.dims:
                t_size = int(ds.sizes[time_coord])
                selector[time_coord] = max(0, min(time_index, t_size - 1))
                try:
                    time_str = str(ds[time_coord].values[selector[time_coord]])
                except Exception:
                    time_str = None

            if depth_coord and depth_coord in da_u.dims:
                d_size = int(ds.sizes[depth_coord])
                selector[depth_coord] = max(0, min(depth_index, d_size - 1))
                try:
                    depth_val = float(ds[depth_coord].values[selector[depth_coord]])
                except Exception:
                    depth_val = None

            u_2d = da_u.isel(selector) if selector else da_u
            v_2d = da_v.isel(selector) if selector else da_v
            w_2d = (da_w.isel(selector) if selector else da_w) if has_w else None

            lat_vals = np.asarray(ds[lat_coord].values, dtype=np.float64)
            lon_vals = np.asarray(ds[lon_coord].values, dtype=np.float64)

            # Spatial bounding
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

            lat_indices = np.where(lat_mask)[0]
            lon_indices = np.where(lon_mask)[0]

            if len(lat_indices) == 0 or len(lon_indices) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Requested spatial bounding box does not intersect dataset coordinates.",
                )

            sub_lats = lat_vals[lat_indices]
            sub_lons = lon_vals[lon_indices]
            total_raw_points = int(len(sub_lats) * len(sub_lons))

            decimation_factor = max(1, decimation)
            if (total_raw_points / (decimation_factor**2)) > MAX_VECTORS_LIMIT:
                required_factor = int(math.ceil(math.sqrt(total_raw_points / MAX_VECTORS_LIMIT)))
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Requested current vectors grid contains {total_raw_points} points, exceeding safety limit of {MAX_VECTORS_LIMIT}. "
                        f"Please narrow your spatial bounding box or set decimation factor to at least {required_factor}."
                    ),
                )

            if decimation_factor > 1:
                lat_indices = lat_indices[::decimation_factor]
                lon_indices = lon_indices[::decimation_factor]
                sub_lats = lat_vals[lat_indices]
                sub_lons = lon_vals[lon_indices]

            u_sub = np.asarray(u_2d.isel({lat_coord: lat_indices, lon_coord: lon_indices}).values, dtype=np.float64)
            v_sub = np.asarray(v_2d.isel({lat_coord: lat_indices, lon_coord: lon_indices}).values, dtype=np.float64)
            w_sub = (
                np.asarray(w_2d.isel({lat_coord: lat_indices, lon_coord: lon_indices}).values, dtype=np.float64)
                if has_w and w_2d is not None
                else None
            )

            # Ensure 2D shape
            if u_sub.ndim > 2:
                u_sub = np.squeeze(u_sub)
                v_sub = np.squeeze(v_sub)
                if w_sub is not None:
                    w_sub = np.squeeze(w_sub)

            # Compute speed and direction vectors
            vectors: List[CurrentVectorItem] = []
            speed_all: List[float] = []

            for i, lat in enumerate(sub_lats):
                for j, lon in enumerate(sub_lons):
                    u_val = float(u_sub[i, j]) if np.isfinite(u_sub[i, j]) else None
                    v_val = float(v_sub[i, j]) if np.isfinite(v_sub[i, j]) else None
                    w_val = float(w_sub[i, j]) if w_sub is not None and np.isfinite(w_sub[i, j]) else None

                    if u_val is not None and v_val is not None:
                        if w_val is not None:
                            spd = float(np.sqrt(u_val**2 + v_val**2 + w_val**2))
                        else:
                            spd = float(np.sqrt(u_val**2 + v_val**2))

                        dir_deg = float((np.rad2deg(np.arctan2(u_val, v_val)) + 360.0) % 360.0)
                        speed_all.append(spd)
                    else:
                        spd = None
                        dir_deg = None

                    vectors.append(
                        CurrentVectorItem(
                            latitude=round(float(lat), 6),
                            longitude=round(float(lon), 6),
                            u=round(u_val, 4) if u_val is not None else None,
                            v=round(v_val, 4) if v_val is not None else None,
                            w=round(w_val, 4) if w_val is not None else None,
                            speed=round(spd, 4) if spd is not None else None,
                            direction=round(dir_deg, 2) if dir_deg is not None else None,
                        )
                    )

            spd_min = float(np.min(speed_all)) if speed_all else None
            spd_max = float(np.max(speed_all)) if speed_all else None

            vel_dim_str = "3D (total: u, v, w)" if (has_w and w_sub is not None) else "2D (horizontal: u, v)"

            return CurrentsDeliveryResponse(
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                velocity_dimensions=vel_dim_str,
                time=time_str,
                depth=depth_val,
                vectors=vectors,
                total_vectors=len(vectors),
                speed_min=round(spd_min, 4) if spd_min is not None else None,
                speed_max=round(spd_max, 4) if spd_max is not None else None,
                downsample=DownsampleMetadata(
                    downsampled=(decimation_factor > 1),
                    original_points=total_raw_points,
                    returned_points=len(vectors),
                    decimation_factor=decimation_factor,
                ),
                delivered_at=datetime.now(timezone.utc),
            )
