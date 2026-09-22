"""Temporal analysis service for scientific ocean datasets.

Extracts time coverage, step counts, interval delta analysis, and regularity checks.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID
import numpy as np
import pandas as pd
import xarray as xr

from app.schemas.analysis import (
    TemporalAnalysisResponse,
    TemporalRangeSummary,
)


class TemporalAnalyzer:
    """Performs temporal coordinate and resolution analysis on ocean datasets."""

    @staticmethod
    def analyze_temporal_extent(
        ds: xr.Dataset,
        dataset_id: UUID,
        dataset_name: str,
        asset_id: UUID | None = None,
    ) -> TemporalAnalysisResponse:
        """Analyze temporal coverage, timesteps, and regularity.

        Args:
            ds: xarray.Dataset
            dataset_id: Canonical dataset identifier
            dataset_name: Dataset name
            asset_id: Optional array asset identifier

        Returns:
            TemporalAnalysisResponse with time range and regularity metadata.
        """
        from app.services.scientific_array import ScientificArrayReader

        coords_map = ScientificArrayReader.identify_standard_coords(ds)
        time_coord_name = coords_map.get("time")

        if not time_coord_name or time_coord_name not in ds:
            raise ValueError(
                f"Dataset '{dataset_name}' does not contain a recognizable temporal coordinate (e.g. time, date)."
            )

        time_var = ds[time_coord_name]
        time_values = time_var.values
        total_steps = int(time_values.size)

        if total_steps == 0:
            raise ValueError(f"Temporal coordinate '{time_coord_name}' is empty.")

        # Convert to pandas datetime / string representation
        iso_times: list[str] = []
        try:
            pd_times = pd.to_datetime(time_values)
            start_iso = pd_times[0].isoformat()
            end_iso = pd_times[-1].isoformat()
            # Calculate step intervals in seconds if > 1 step
            if total_steps > 1:
                deltas = pd.Series(pd_times).diff().dropna()
                delta_seconds = deltas.dt.total_seconds().values
                median_interval = float(np.median(delta_seconds))
                # Check regularity (std dev < 5% of median)
                std_interval = float(np.std(delta_seconds))
                is_regular = std_interval < (0.05 * median_interval) if median_interval > 0 else False
            else:
                median_interval = None
                is_regular = True

            # Sample first 3 and last 3
            if total_steps <= 6:
                iso_times = [t.isoformat() for t in pd_times]
            else:
                iso_times = [t.isoformat() for t in pd_times[:3]] + ["..."] + [t.isoformat() for t in pd_times[-3:]]

        except Exception:
            # Fallback for cftime or non-standard calendars
            start_iso = str(time_values[0])
            end_iso = str(time_values[-1])
            median_interval = None
            is_regular = False
            if total_steps <= 6:
                iso_times = [str(t) for t in time_values]
            else:
                iso_times = [str(t) for t in time_values[:3]] + ["..."] + [str(t) for t in time_values[-3:]]

        temporal_range = TemporalRangeSummary(
            start_time=start_iso,
            end_time=end_iso,
            total_timesteps=total_steps,
            timestep_interval_seconds=round(median_interval, 2) if median_interval is not None else None,
            is_regular_interval=is_regular,
        )

        return TemporalAnalysisResponse(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            asset_id=asset_id,
            temporal_range=temporal_range,
            timesteps_sample=iso_times,
            analyzed_at=datetime.now(timezone.utc),
        )
