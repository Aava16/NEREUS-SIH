"""Scientific array multidimensional slicing delivery service.

Extracts bounded multi-dimensional or sub-volume slices with safe cell limits
and coordinate alignment.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import xarray as xr

from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.data_delivery import DownsampleMetadata, SliceDeliveryResponse
from app.services.scientific_array import ScientificArrayReader

MAX_SLICE_CELLS_LIMIT = 250_000


class DeliverySliceService:
    """Extracts bounded slices from multidimensional scientific variables."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

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
        """Extract a bounded slice for the requested variable."""
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

            selector: dict[str, Any] = {}

            if time_index is not None and time_coord and time_coord in da.dims:
                t_size = int(ds.sizes[time_coord])
                if time_index < 0 or time_index >= t_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Time index {time_index} out of range [0, {t_size - 1}].",
                    )
                selector[time_coord] = time_index

            if depth_index is not None and depth_coord and depth_coord in da.dims:
                d_size = int(ds.sizes[depth_coord])
                if depth_index < 0 or depth_index >= d_size:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Depth index {depth_index} out of range [0, {d_size - 1}].",
                    )
                selector[depth_coord] = depth_index

            da_sliced = da.isel(selector) if selector else da

            # Spatial subsetting if lat/lon bounding requested
            if lat_coord and lat_coord in ds and (min_lat is not None or max_lat is not None):
                lat_vals = np.asarray(ds[lat_coord].values, dtype=np.float64)
                lat_mask = np.ones(len(lat_vals), dtype=bool)
                if min_lat is not None:
                    lat_mask &= lat_vals >= min_lat
                if max_lat is not None:
                    lat_mask &= lat_vals <= max_lat
                lat_indices = np.where(lat_mask)[0]
                if len(lat_indices) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Latitude bounding range does not intersect dataset coordinates.",
                    )
                da_sliced = da_sliced.isel({lat_coord: lat_indices})

            if lon_coord and lon_coord in ds and (min_lon is not None or max_lon is not None):
                lon_vals = np.asarray(ds[lon_coord].values, dtype=np.float64)
                lon_mask = np.ones(len(lon_vals), dtype=bool)
                if min_lon is not None:
                    lon_mask &= lon_vals >= min_lon
                if max_lon is not None:
                    lon_mask &= lon_vals <= max_lon
                lon_indices = np.where(lon_mask)[0]
                if len(lon_indices) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Longitude bounding range does not intersect dataset coordinates.",
                    )
                da_sliced = da_sliced.isel({lon_coord: lon_indices})

            # Check total slice cells
            total_raw_cells = int(da_sliced.size)
            decimation_factor = max(1, decimation)

            if (total_raw_cells / decimation_factor) > MAX_SLICE_CELLS_LIMIT:
                required_factor = int(math.ceil(total_raw_cells / MAX_SLICE_CELLS_LIMIT))
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Requested slice contains {total_raw_cells} cells, exceeding safety limit of {MAX_SLICE_CELLS_LIMIT}. "
                        f"Please narrow your selection or specify a decimation factor of at least {required_factor}."
                    ),
                )

            # Apply decimation across all remaining dimensions
            if decimation_factor > 1:
                dec_slices = {str(dim): slice(None, None, decimation_factor) for dim in da_sliced.dims}
                da_final = da_sliced.isel(dec_slices)
            else:
                da_final = da_sliced

            # Build dimension coordinates mapping
            dim_coords: Dict[str, List[Any]] = {}
            for dim_name in da_final.dims:
                dim_str = str(dim_name)
                if dim_str in ds.coords:
                    vals = ds.coords[dim_str].values
                    if decimation_factor > 1 and dim_str in da_sliced.dims:
                        vals = vals[slice(None, None, decimation_factor)]
                    # Clean coordinates for JSON
                    if np.issubdtype(vals.dtype, np.number):
                        dim_coords[dim_str] = [round(float(x), 6) if np.isfinite(x) else None for x in vals]
                    else:
                        dim_coords[dim_str] = [str(x) for x in vals]

            # Convert numpy values to nested list with None for NaNs
            np_vals = np.asarray(da_final.values, dtype=np.float64)

            def sanitize_nested(arr: Any) -> Any:
                if isinstance(arr, np.ndarray):
                    if arr.ndim == 0:
                        return float(arr) if np.isfinite(arr) else None
                    return [sanitize_nested(sub) for sub in arr]
                elif isinstance(arr, (float, np.floating)):
                    return round(float(arr), 6) if np.isfinite(arr) else None
                elif isinstance(arr, (int, np.integer)):
                    return int(arr)
                return arr

            values_cleaned = sanitize_nested(np_vals)
            units = str(da.attrs.get("units", "")) or None

            return SliceDeliveryResponse(
                dataset_id=dataset.id,
                variable_name=variable_name,
                units=units,
                dimensions=[str(d) for d in da_final.dims],
                shape=[int(s) for s in da_final.shape],
                dimension_coordinates=dim_coords,
                values=values_cleaned,
                downsample=DownsampleMetadata(
                    downsampled=(decimation_factor > 1),
                    original_points=total_raw_cells,
                    returned_points=int(da_final.size),
                    decimation_factor=decimation_factor,
                ),
                delivered_at=datetime.now(timezone.utc),
            )
