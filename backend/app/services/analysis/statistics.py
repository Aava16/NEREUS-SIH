"""Statistical calculation service for scientific ocean variables.

Provides numerically robust, NaN-safe descriptive statistics and percentile
distributions for multi-dimensional scientific arrays.
"""

from typing import Any
import numpy as np
import xarray as xr

from app.schemas.analysis import VariableStatistics


class StatisticsAnalyzer:
    """Computes robust statistical metrics on scientific array data."""

    @staticmethod
    def compute_variable_statistics(
        data: xr.DataArray | np.ndarray,
        variable_name: str,
        units: str | None = None,
        standard_name: str | None = None,
    ) -> VariableStatistics:
        """Compute comprehensive statistics on an array, safely handling NaNs/masks.

        Args:
            data: xarray.DataArray or numpy.ndarray
            variable_name: Name of the variable
            units: Physical units if available
            standard_name: CF standard name if available

        Returns:
            VariableStatistics schema with all metrics.
        """
        # Extract numpy array values
        if isinstance(data, xr.DataArray):
            shape = list(data.shape)
            attrs = data.attrs or {}
            units = units or str(attrs.get("units", "")) or None
            standard_name = standard_name or str(attrs.get("standard_name", "")) or None
            values = data.values
        else:
            shape = list(data.shape)
            values = data

        # Total elements
        total_elements = int(values.size)
        if total_elements == 0:
            return VariableStatistics(
                variable_name=variable_name,
                units=units,
                standard_name=standard_name,
                min=None,
                max=None,
                mean=None,
                median=None,
                std=None,
                p25=None,
                p50=None,
                p75=None,
                p90=None,
                p95=None,
                valid_count=0,
                missing_count=0,
                shape=shape,
            )

        # Flatten and filter NaNs / infinite values / masked elements
        if isinstance(values, np.ma.MaskedArray):
            flat = values.compressed()
        else:
            flat = values.ravel()

        # Filter out NaN and inf
        finite_mask = np.isfinite(flat)
        valid_values = flat[finite_mask]

        valid_count = int(valid_values.size)
        missing_count = total_elements - valid_count

        if valid_count == 0:
            return VariableStatistics(
                variable_name=variable_name,
                units=units,
                standard_name=standard_name,
                min=None,
                max=None,
                mean=None,
                median=None,
                std=None,
                p25=None,
                p50=None,
                p75=None,
                p90=None,
                p95=None,
                valid_count=0,
                missing_count=missing_count,
                shape=shape,
            )

        # Compute metrics on valid numbers
        # Cast to float64 for numeric stability
        float_vals = valid_values.astype(np.float64)

        val_min = float(np.min(float_vals))
        val_max = float(np.max(float_vals))
        val_mean = float(np.mean(float_vals))
        val_median = float(np.median(float_vals))
        val_std = float(np.std(float_vals))

        # Percentiles
        p25, p50, p75, p90, p95 = np.percentile(float_vals, [25, 50, 75, 90, 95])

        return VariableStatistics(
            variable_name=variable_name,
            units=units,
            standard_name=standard_name,
            min=round(val_min, 6),
            max=round(val_max, 6),
            mean=round(val_mean, 6),
            median=round(val_median, 6),
            std=round(val_std, 6),
            p25=round(float(p25), 6),
            p50=round(float(p50), 6),
            p75=round(float(p75), 6),
            p90=round(float(p90), 6),
            p95=round(float(p95), 6),
            valid_count=valid_count,
            missing_count=missing_count,
            shape=shape,
        )
