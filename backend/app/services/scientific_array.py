from contextlib import contextmanager
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
from fastapi import HTTPException, status
import numpy as np
import xarray as xr

from app.schemas.scientific_processing import (
    DimensionMetadata,
    GridSliceRequest,
    GridSliceResponse,
    GridSliceStatistics,
    ScientificAssetInspectionResponse,
    VariableArrayMetadata,
)

logger = logging.getLogger(__name__)

# Standard coordinate name aliases in CF oceanographic datasets
LAT_NAMES = {"lat", "latitude", "nav_lat", "y"}
LON_NAMES = {"lon", "longitude", "nav_lon", "x"}
DEPTH_NAMES = {"depth", "depth_m", "lev", "level", "z"}
TIME_NAMES = {"time", "t", "temporal"}


class ScientificArrayReader:
    """Low-level adapter for opening and safely inspecting NetCDF4 and Zarr scientific grid assets."""

    @contextmanager
    def open_dataset(self, uri: str, storage_format: str) -> Generator[xr.Dataset, None, None]:
        """Context manager opening a scientific dataset lazily with xarray."""
        # Check local file existence if URI is a local path
        if uri.startswith("file://"):
            filepath = uri[7:]
        else:
            filepath = uri

        if not uri.startswith(("s3://", "gs://", "http://", "https://")) and not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scientific array asset file at '{uri}' is not accessible on storage.",
            )

        try:
            format_upper = storage_format.upper()
            if format_upper == "ZARR":
                ds = xr.open_zarr(filepath, consolidated=None)
            else:
                ds = xr.open_dataset(filepath, decode_times=True)
        except Exception as exc:
            logger.error("Failed to open scientific asset at '%s': %s", uri, str(exc))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to read scientific array file at '{uri}': {type(exc).__name__} - {str(exc)}",
            ) from None

        try:
            yield ds
        finally:
            ds.close()

    @staticmethod
    def identify_standard_coords(ds: xr.Dataset) -> Dict[str, Optional[str]]:
        """Identify canonical coordinate names (lat, lon, depth, time) from dataset coordinates."""
        identified: Dict[str, Optional[str]] = {
            "lat": None,
            "lon": None,
            "depth": None,
            "time": None,
        }
        coord_names = set(ds.coords.keys()).union(ds.sizes.keys())

        for name in coord_names:
            name_lower = name.lower()
            if not identified["lat"] and name_lower in LAT_NAMES:
                identified["lat"] = name
            elif not identified["lon"] and name_lower in LON_NAMES:
                identified["lon"] = name
            elif not identified["depth"] and name_lower in DEPTH_NAMES:
                identified["depth"] = name
            elif not identified["time"] and name_lower in TIME_NAMES:
                identified["time"] = name

        return identified

    def validate_and_inspect_asset(
        self, ds: xr.Dataset, asset_id: Any, dataset_id: Any, storage_format: str, uri: str
    ) -> ScientificAssetInspectionResponse:
        """Extract complete dimension, variable, coordinate, and attribute metadata from an open xarray Dataset."""
        warnings: List[str] = []
        std_coords = self.identify_standard_coords(ds)

        # 1. Dimensions extraction & validation
        dimensions: Dict[str, DimensionMetadata] = {}
        for dim_name, dim_size in ds.sizes.items():
            min_v: Optional[float] = None
            max_v: Optional[float] = None
            step_v: Optional[float] = None
            units_v: Optional[str] = None

            if dim_name in ds.coords:
                coord = ds.coords[dim_name]
                units_v = coord.attrs.get("units", None)
                if np.issubdtype(coord.dtype, np.number):
                    vals = coord.values
                    if len(vals) > 0:
                        min_v = float(np.nanmin(vals))
                        max_v = float(np.nanmax(vals))
                        if len(vals) > 1:
                            diffs = np.diff(vals)
                            # Check monotonic ordering
                            if not (np.all(diffs > 0) or np.all(diffs < 0)):
                                warnings.append(f"Dimension '{dim_name}' coordinates are not strictly monotonic.")
                            step_v = float(round(np.mean(np.abs(diffs)), 6))

            dimensions[str(dim_name)] = DimensionMetadata(
                name=str(dim_name),
                size=int(dim_size),
                min_value=min_v,
                max_value=max_v,
                step=step_v,
                units=units_v,
            )

        # 2. Variables extraction
        variables: Dict[str, VariableArrayMetadata] = {}
        for var_name, data_array in ds.data_vars.items():
            vmin = data_array.attrs.get("valid_min")
            vmax = data_array.attrs.get("valid_max")
            fill_v = data_array.attrs.get("_FillValue", data_array.attrs.get("missing_value", None))

            variables[str(var_name)] = VariableArrayMetadata(
                name=str(var_name),
                dimensions=[str(d) for d in data_array.dims],
                shape=[int(s) for s in data_array.shape],
                dtype=str(data_array.dtype),
                units=data_array.attrs.get("units", None),
                standard_name=data_array.attrs.get("standard_name", None),
                long_name=data_array.attrs.get("long_name", None),
                valid_min=float(vmin) if vmin is not None else None,
                valid_max=float(vmax) if vmax is not None else None,
                fill_value=float(fill_v) if fill_v is not None and not math.isnan(float(fill_v)) else None,
            )

        # 3. Spatial Extent
        spatial_extent: Optional[Dict[str, float]] = None
        if std_coords["lat"] and std_coords["lon"]:
            lat_arr = ds.coords[std_coords["lat"]].values
            lon_arr = ds.coords[std_coords["lon"]].values
            spatial_extent = {
                "min_lon": float(np.nanmin(lon_arr)),
                "min_lat": float(np.nanmin(lat_arr)),
                "max_lon": float(np.nanmax(lon_arr)),
                "max_lat": float(np.nanmax(lat_arr)),
            }

        # 4. Temporal Coverage
        temporal_coverage: Optional[Dict[str, Optional[str]]] = None
        if std_coords["time"]:
            time_arr = ds.coords[std_coords["time"]].values
            if len(time_arr) > 0:
                temporal_coverage = {
                    "start": str(np.min(time_arr))[:19] if time_arr is not None else None,
                    "end": str(np.max(time_arr))[:19] if time_arr is not None else None,
                }

        # 5. Depth Coverage
        depth_coverage: Optional[Dict[str, Optional[float]]] = None
        if std_coords["depth"]:
            depth_arr = ds.coords[std_coords["depth"]].values
            if len(depth_arr) > 0:
                depth_coverage = {
                    "min_m": float(np.nanmin(depth_arr)),
                    "max_m": float(np.nanmax(depth_arr)),
                }

        # Global attributes
        global_attrs = {str(k): str(v) for k, v in ds.attrs.items()}

        return ScientificAssetInspectionResponse(
            asset_id=asset_id,
            dataset_id=dataset_id,
            storage_format=storage_format,
            uri=uri,
            dimensions=dimensions,
            variables=variables,
            spatial_extent=spatial_extent,
            temporal_coverage=temporal_coverage,
            depth_coverage=depth_coverage,
            global_attributes=global_attrs,
            is_valid_ocean_grid=len(warnings) == 0,
            validation_warnings=warnings,
        )

    def slice_grid_2d(
        self, ds: xr.Dataset, req: GridSliceRequest
    ) -> Tuple[List[float], List[float], List[List[Optional[float]]], GridSliceStatistics, Optional[float], Optional[str]]:
        """Extract a bounded 2D lat-lon slice at specified time and depth indices with decimation."""
        if req.variable_name not in ds:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable '{req.variable_name}' is not present in this scientific asset.",
            )

        da = ds[req.variable_name]
        std_coords = self.identify_standard_coords(ds)

        time_key = std_coords["time"]
        depth_key = std_coords["depth"]
        lat_key = std_coords["lat"]
        lon_key = std_coords["lon"]

        if not lat_key or not lon_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Asset lacks standard latitude/longitude spatial coordinates.",
            )

        # Indexing time
        timestamp_str: Optional[str] = None
        if time_key and time_key in da.dims:
            time_size = da.sizes[time_key]
            t_idx = min(req.time_index or 0, time_size - 1)
            da = da.isel({time_key: t_idx})
            if time_key in ds.coords:
                timestamp_str = str(ds.coords[time_key].values[t_idx])[:19]

        # Indexing depth
        depth_val: Optional[float] = None
        if depth_key and depth_key in da.dims:
            depth_size = da.sizes[depth_key]
            d_idx = min(req.depth_index or 0, depth_size - 1)
            da = da.isel({depth_key: d_idx})
            if depth_key in ds.coords:
                depth_val = float(ds.coords[depth_key].values[d_idx])

        # Bounding box spatial subsetting
        if req.bbox_min_lon is not None and req.bbox_max_lon is not None:
            da = da.where((da[lon_key] >= req.bbox_min_lon) & (da[lon_key] <= req.bbox_max_lon), drop=True)
        if req.bbox_min_lat is not None and req.bbox_max_lat is not None:
            da = da.where((da[lat_key] >= req.bbox_min_lat) & (da[lat_key] <= req.bbox_max_lat), drop=True)

        # Decimation downsampling
        step = max(1, req.decimation_step)
        da = da.isel({lat_key: slice(None, None, step), lon_key: slice(None, None, step)})

        # Extract values matrix
        raw_vals = da.values
        lats = [float(y) for y in da[lat_key].values]
        lons = [float(x) for x in da[lon_key].values]

        # Handle 2D grid matrix
        grid_matrix: List[List[Optional[float]]] = []
        flat_valid_vals: List[float] = []
        null_count = 0

        for row in raw_vals:
            row_list: List[Optional[float]] = []
            for item in row:
                if item is None or math.isnan(item):
                    row_list.append(None)
                    null_count += 1
                else:
                    val_f = round(float(item), 4)
                    row_list.append(val_f)
                    flat_valid_vals.append(val_f)
            grid_matrix.append(row_list)

        # Statistics
        if flat_valid_vals:
            arr_np = np.array(flat_valid_vals, dtype=np.float64)
            stats = GridSliceStatistics(
                min_value=round(float(np.min(arr_np)), 4),
                max_value=round(float(np.max(arr_np)), 4),
                mean_value=round(float(np.mean(arr_np)), 4),
                std_value=round(float(np.std(arr_np)), 4),
                sample_count=len(flat_valid_vals),
                null_count=null_count,
            )
        else:
            stats = GridSliceStatistics(
                min_value=None,
                max_value=None,
                mean_value=None,
                std_value=None,
                sample_count=0,
                null_count=null_count,
            )

        return lons, lats, grid_matrix, stats, depth_val, timestamp_str
