"""Spatial analysis service for scientific ocean datasets.

Extracts coordinate extents, resolutions, depth levels, and bounding structures.
"""

from typing import Any
from uuid import UUID
import numpy as np
import xarray as xr

from app.schemas.analysis import (
    DepthRangeSummary,
    SpatialAnalysisResponse,
    SpatialExtentSummary,
)


class SpatialAnalyzer:
    """Performs spatial and vertical coordinate analysis on ocean datasets."""

    @staticmethod
    def analyze_spatial_extent(
        ds: xr.Dataset,
        dataset_id: UUID,
        dataset_name: str,
        asset_id: UUID | None = None,
    ) -> SpatialAnalysisResponse:
        """Extract spatial bounding box, grid resolution, and depth levels.

        Args:
            ds: xarray.Dataset
            dataset_id: Canonical dataset identifier
            dataset_name: Dataset name
            asset_id: Optional array asset identifier

        Returns:
            SpatialAnalysisResponse with spatial extent and vertical depth range.
        """
        from datetime import datetime, timezone
        from app.services.scientific_array import ScientificArrayReader

        # Identify standard coordinates
        coords_map = ScientificArrayReader.identify_standard_coords(ds)
        lat_coord_name = coords_map.get("lat")
        lon_coord_name = coords_map.get("lon")
        depth_coord_name = coords_map.get("depth")

        # Latitude extent
        if lat_coord_name and lat_coord_name in ds:
            lat_arr = np.asarray(ds[lat_coord_name].values, dtype=np.float64)
            lat_min = float(np.nanmin(lat_arr))
            lat_max = float(np.nanmax(lat_arr))
            lat_points = int(lat_arr.size)
            if lat_points > 1:
                lat_step = float(abs(lat_arr[1] - lat_arr[0])) if lat_arr.ndim == 1 else float((lat_max - lat_min) / (lat_points - 1))
            else:
                lat_step = None
        else:
            lat_min, lat_max, lat_points, lat_step = -90.0, 90.0, 0, None

        # Longitude extent
        if lon_coord_name and lon_coord_name in ds:
            lon_arr = np.asarray(ds[lon_coord_name].values, dtype=np.float64)
            lon_min = float(np.nanmin(lon_arr))
            lon_max = float(np.nanmax(lon_arr))
            lon_points = int(lon_arr.size)
            if lon_points > 1:
                lon_step = float(abs(lon_arr[1] - lon_arr[0])) if lon_arr.ndim == 1 else float((lon_max - lon_min) / (lon_points - 1))
            else:
                lon_step = None
        else:
            lon_min, lon_max, lon_points, lon_step = -180.0, 180.0, 0, None

        # Depth extent
        depth_min = None
        depth_max = None
        depth_levels_count = 0
        depth_levels: list[float] = []

        if depth_coord_name and depth_coord_name in ds:
            depth_arr = np.asarray(ds[depth_coord_name].values, dtype=np.float64)
            depth_arr = depth_arr[np.isfinite(depth_arr)]
            if depth_arr.size > 0:
                depth_min = float(np.nanmin(depth_arr))
                depth_max = float(np.nanmax(depth_arr))
                depth_levels_count = int(depth_arr.size)
                # Sample up to first 50 levels for JSON safety
                depth_levels = [round(float(d), 4) for d in depth_arr[:50]]

        spatial_extent = SpatialExtentSummary(
            latitude_min=round(lat_min, 6),
            latitude_max=round(lat_max, 6),
            longitude_min=round(lon_min, 6),
            longitude_max=round(lon_max, 6),
            latitude_points=lat_points,
            longitude_points=lon_points,
            latitude_step=round(lat_step, 6) if lat_step is not None else None,
            longitude_step=round(lon_step, 6) if lon_step is not None else None,
        )

        depth_range = DepthRangeSummary(
            depth_min=round(depth_min, 4) if depth_min is not None else None,
            depth_max=round(depth_max, 4) if depth_max is not None else None,
            depth_levels_count=depth_levels_count,
            levels=depth_levels,
        )

        coord_names = list(ds.coords.keys())

        return SpatialAnalysisResponse(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            asset_id=asset_id,
            spatial_extent=spatial_extent,
            depth_range=depth_range,
            coordinate_names=coord_names,
            analyzed_at=datetime.now(timezone.utc),
        )
