"""Ocean currents analysis service for velocity fields.

Computes 2D horizontal and 3D current speed magnitude, flow direction,
and component-level statistics from U/V/W velocity fields.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID
import numpy as np
import xarray as xr

from app.schemas.analysis import (
    CurrentsAnalysisResponse,
    VariableStatistics,
)
from app.services.analysis.statistics import StatisticsAnalyzer


class CurrentsAnalyzer:
    """Performs ocean current velocity, magnitude, and directional analysis."""

    @staticmethod
    def analyze_currents(
        ds: xr.Dataset,
        dataset_id: UUID,
        dataset_name: str,
        asset_id: UUID | None = None,
        u_name: str | None = None,
        v_name: str | None = None,
        w_name: str | None = None,
    ) -> CurrentsAnalysisResponse:
        """Analyze velocity fields, computing speed magnitude, direction, and stats.

        Args:
            ds: xarray.Dataset containing velocity variables
            dataset_id: Canonical dataset identifier
            dataset_name: Dataset name
            asset_id: Optional array asset identifier
            u_name: Optional explicit name for eastward/u velocity variable
            v_name: Optional explicit name for northward/v velocity variable
            w_name: Optional explicit name for vertical/w velocity variable

        Returns:
            CurrentsAnalysisResponse with speed, direction, and component statistics.
        """
        # Auto-detect U and V if not specified
        var_names_lower = {name.lower(): name for name in ds.data_vars.keys()}
        explicit_2d = bool(u_name and v_name and not w_name)

        if not u_name:
            for candidate in ["u", "uo", "u_current", "u_velocity", "eastward_sea_water_velocity", "water_u"]:
                if candidate in var_names_lower:
                    u_name = var_names_lower[candidate]
                    break

        if not v_name:
            for candidate in ["v", "vo", "v_current", "v_velocity", "northward_sea_water_velocity", "water_v"]:
                if candidate in var_names_lower:
                    v_name = var_names_lower[candidate]
                    break

        if not explicit_2d and not w_name:
            for candidate in ["w", "wo", "w_current", "w_velocity", "upward_sea_water_velocity", "water_w"]:
                if candidate in var_names_lower:
                    w_name = var_names_lower[candidate]
                    break

        if not u_name or u_name not in ds:
            raise ValueError(
                f"Eastward velocity variable (u) not found in dataset '{dataset_name}'. "
                f"Available variables: {list(ds.data_vars.keys())}"
            )

        if not v_name or v_name not in ds:
            raise ValueError(
                f"Northward velocity variable (v) not found in dataset '{dataset_name}'. "
                f"Available variables: {list(ds.data_vars.keys())}"
            )

        u_data = ds[u_name]
        v_data = ds[v_name]

        # Check shape compatibility between u and v
        if u_data.shape != v_data.shape:
            raise ValueError(
                f"Velocity components '{u_name}' {u_data.shape} and '{v_name}' {v_data.shape} have incompatible shapes."
            )

        has_w = w_name is not None and w_name in ds
        if has_w:
            w_data = ds[w_name]
            if w_data.shape != u_data.shape:
                has_w = False
                w_name = None

        # Extract numeric arrays (as float64 for stability)
        u_arr = np.asarray(u_data.values, dtype=np.float64)
        v_arr = np.asarray(v_data.values, dtype=np.float64)

        # Compute speed magnitude: sqrt(u^2 + v^2 (+ w^2))
        if has_w and w_name:
            w_arr = np.asarray(ds[w_name].values, dtype=np.float64)
            speed_arr = np.sqrt(u_arr**2 + v_arr**2 + w_arr**2)
            velocity_dims = "3D (total: u, v, w)"
            variables_used = {"u": u_name, "v": v_name, "w": w_name}
        else:
            speed_arr = np.sqrt(u_arr**2 + v_arr**2)
            velocity_dims = "2D (horizontal: u, v)"
            variables_used = {"u": u_name, "v": v_name}

        # Flow direction (oceanographic direction in degrees [0, 360)):
        # Direction to which the current is flowing: atan2(u, v) in degrees
        with np.errstate(invalid="ignore", divide="ignore"):
            # rad2deg(arctan2(u, v)) gives degrees from North clockwise: East=90, South=180, West=270, North=0
            dir_rad = np.arctan2(u_arr, v_arr)
            dir_deg = (np.rad2deg(dir_rad) + 360.0) % 360.0

        # Component statistics
        component_stats: dict[str, VariableStatistics] = {
            "u": StatisticsAnalyzer.compute_variable_statistics(u_data, u_name, units="m/s"),
            "v": StatisticsAnalyzer.compute_variable_statistics(v_data, v_name, units="m/s"),
        }
        if has_w and w_name:
            component_stats["w"] = StatisticsAnalyzer.compute_variable_statistics(
                ds[w_name], w_name, units="m/s"
            )

        # Speed statistics
        speed_stats = StatisticsAnalyzer.compute_variable_statistics(
            speed_arr,
            variable_name="current_speed_magnitude",
            units="m/s",
            standard_name="sea_water_speed",
        )

        # Direction statistics (vector mean direction and summary)
        valid_u = u_arr[np.isfinite(u_arr) & np.isfinite(v_arr)]
        valid_v = v_arr[np.isfinite(u_arr) & np.isfinite(v_arr)]
        valid_dir = dir_deg[np.isfinite(dir_deg)]

        if valid_u.size > 0:
            mean_u = float(np.mean(valid_u))
            mean_v = float(np.mean(valid_v))
            vector_mean_dir = float((np.rad2deg(np.arctan2(mean_u, mean_v)) + 360.0) % 360.0)
            vector_mean_speed = float(np.sqrt(mean_u**2 + mean_v**2))
            dir_min = float(np.min(valid_dir))
            dir_max = float(np.max(valid_dir))
            dir_mean = float(np.mean(valid_dir))
        else:
            vector_mean_dir = None
            vector_mean_speed = None
            dir_min = None
            dir_max = None
            dir_mean = None

        direction_stats: dict[str, Any] = {
            "unit": "degrees_clockwise_from_true_north",
            "vector_mean_direction_degrees": round(vector_mean_dir, 2) if vector_mean_dir is not None else None,
            "vector_mean_speed_m_s": round(vector_mean_speed, 4) if vector_mean_speed is not None else None,
            "min_direction_degrees": round(dir_min, 2) if dir_min is not None else None,
            "max_direction_degrees": round(dir_max, 2) if dir_max is not None else None,
            "scalar_mean_direction_degrees": round(dir_mean, 2) if dir_mean is not None else None,
        }

        return CurrentsAnalysisResponse(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            asset_id=asset_id,
            velocity_dimensions=velocity_dims,
            variables_used=variables_used,
            speed_statistics=speed_stats,
            direction_statistics=direction_stats,
            component_statistics=component_stats,
            analyzed_at=datetime.now(timezone.utc),
        )
