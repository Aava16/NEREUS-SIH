from datetime import datetime, timezone
import logging
import math
from typing import Optional
import uuid
from fastapi import HTTPException, status
import numpy as np
from sqlalchemy.orm import Session

from app.models.array_asset import ArrayAsset
from app.models.provenance import Provenance
from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.provenance import ProvenanceRepository
from app.schemas.scientific_processing import (
    DerivedFieldRequest,
    DerivedFieldResponse,
    GridSliceRequest,
    GridSliceResponse,
    GridSliceStatistics,
    ScientificAssetInspectionResponse,
)
from app.services.scientific_array import ScientificArrayReader

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class ScientificProcessingService:
    """Service layer managing scientific array inspection, bounded spatial slicing, derived calculations, and provenance."""

    def __init__(
        self,
        asset_repo: Optional[ArrayAssetRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
        provenance_repo: Optional[ProvenanceRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.asset_repo = asset_repo or ArrayAssetRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.provenance_repo = provenance_repo or ProvenanceRepository()
        self.reader = reader or ScientificArrayReader()

    def _get_asset(self, db: Session, asset_id: uuid.UUID) -> ArrayAsset:
        """Fetch array asset by UUID or raise 404."""
        asset = self.asset_repo.get_by_id(db, asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scientific array asset with ID '{asset_id}' was not found in catalog.",
            )
        return asset

    def inspect_asset(self, db: Session, asset_id: uuid.UUID) -> ScientificAssetInspectionResponse:
        """Open registered scientific array file and extract full dimension, variable, and coordinate metadata."""
        asset = self._get_asset(db, asset_id)
        with self.reader.open_dataset(asset.uri, asset.storage_format) as ds:
            return self.reader.validate_and_inspect_asset(
                ds, asset.id, asset.dataset_id, asset.storage_format, asset.uri
            )

    def slice_grid(self, db: Session, asset_id: uuid.UUID, req: GridSliceRequest) -> GridSliceResponse:
        """Extract a decimated 2D array slice and record an audit provenance trace."""
        asset = self._get_asset(db, asset_id)

        with self.reader.open_dataset(asset.uri, asset.storage_format) as ds:
            if req.variable_name not in ds:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variable '{req.variable_name}' was not found in asset '{asset.uri}'.",
                )

            da = ds[req.variable_name]
            units = da.attrs.get("units", None)
            dims = [str(d) for d in da.dims]

            lons, lats, grid_matrix, stats, depth_val, time_str = self.reader.slice_grid_2d(ds, req)

        # Record Provenance Event
        now_utc = get_utc_now()
        provenance = Provenance(
            dataset_id=asset.dataset_id,
            action="SCIENTIFIC_SLICING",
            source=f"array-asset:{asset.id}",
            actor="scientific-processing-service",
            timestamp=now_utc,
            details={
                "asset_id": str(asset.id),
                "variable_name": req.variable_name,
                "time_index": req.time_index,
                "depth_index": req.depth_index,
                "decimation_step": req.decimation_step,
                "sample_count": stats.sample_count,
            },
        )
        db.add(provenance)
        db.commit()
        db.refresh(provenance)

        return GridSliceResponse(
            variable_name=req.variable_name,
            units=units,
            dimensions=dims,
            shape=[len(lats), len(lons)],
            lons=lons,
            lats=lats,
            depth_m=depth_val,
            timestamp=time_str,
            data_grid=grid_matrix,
            statistics=stats,
            provenance_id=provenance.id,
        )

    def compute_derived_field(
        self, db: Session, asset_id: uuid.UUID, req: DerivedFieldRequest
    ) -> DerivedFieldResponse:
        """Compute an on-the-fly scientific derived parameter (e.g. Current Velocity Speed Magnitude)."""
        asset = self._get_asset(db, asset_id)

        with self.reader.open_dataset(asset.uri, asset.storage_format) as ds:
            if req.derived_type == "CURRENT_SPEED_MAGNITUDE":
                var_u_key = req.variable_u or "u"
                var_v_key = req.variable_v or "v"

                if var_u_key not in ds or var_v_key not in ds:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Both '{var_u_key}' and '{var_v_key}' components must exist in the array asset for speed magnitude calculation.",
                    )

                # Slice u and v
                slice_u_req = GridSliceRequest(
                    variable_name=var_u_key,
                    time_index=req.time_index,
                    depth_index=req.depth_index,
                    decimation_step=req.decimation_step,
                )
                lons_u, lats_u, grid_u, _, _, _ = self.reader.slice_grid_2d(ds, slice_u_req)

                slice_v_req = GridSliceRequest(
                    variable_name=var_v_key,
                    time_index=req.time_index,
                    depth_index=req.depth_index,
                    decimation_step=req.decimation_step,
                )
                _, _, grid_v, _, _, _ = self.reader.slice_grid_2d(ds, slice_v_req)

                # Compute magnitude matrix: sqrt(u^2 + v^2)
                mag_grid: list[list[Optional[float]]] = []
                valid_mags: list[float] = []
                nulls = 0

                for r_idx in range(len(grid_u)):
                    row: list[Optional[float]] = []
                    for c_idx in range(len(grid_u[r_idx])):
                        val_u = grid_u[r_idx][c_idx]
                        val_v = grid_v[r_idx][c_idx]
                        if val_u is not None and val_v is not None:
                            speed = float(round(math.sqrt(val_u**2 + val_v**2), 4))
                            row.append(speed)
                            valid_mags.append(speed)
                        else:
                            row.append(None)
                            nulls += 1
                    mag_grid.append(row)

                if valid_mags:
                    arr_m = np.array(valid_mags, dtype=np.float64)
                    stats = GridSliceStatistics(
                        min_value=round(float(np.min(arr_m)), 4),
                        max_value=round(float(np.max(arr_m)), 4),
                        mean_value=round(float(np.mean(arr_m)), 4),
                        std_value=round(float(np.std(arr_m)), 4),
                        sample_count=len(valid_mags),
                        null_count=nulls,
                    )
                else:
                    stats = GridSliceStatistics(sample_count=0, null_count=nulls)

                units_out = "m/s"
                lons_out = lons_u
                lats_out = lats_u

            elif req.derived_type == "CELSIUS_FROM_KELVIN":
                src_key = req.variable_source or "temperature"
                if src_key not in ds:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Source variable '{src_key}' was not found in asset for Kelvin conversion.",
                    )
                slice_req = GridSliceRequest(
                    variable_name=src_key,
                    time_index=req.time_index,
                    depth_index=req.depth_index,
                    decimation_step=req.decimation_step,
                )
                lons_out, lats_out, raw_grid, _, _, _ = self.reader.slice_grid_2d(ds, slice_req)

                mag_grid = []
                valid_mags = []
                nulls = 0
                for row_raw in raw_grid:
                    row_c: list[Optional[float]] = []
                    for val in row_raw:
                        if val is not None:
                            c_val = float(round(val - 273.15, 4))
                            row_c.append(c_val)
                            valid_mags.append(c_val)
                        else:
                            row_c.append(None)
                            nulls += 1
                    mag_grid.append(row_c)

                if valid_mags:
                    arr_m = np.array(valid_mags, dtype=np.float64)
                    stats = GridSliceStatistics(
                        min_value=round(float(np.min(arr_m)), 4),
                        max_value=round(float(np.max(arr_m)), 4),
                        mean_value=round(float(np.mean(arr_m)), 4),
                        std_value=round(float(np.std(arr_m)), 4),
                        sample_count=len(valid_mags),
                        null_count=nulls,
                    )
                else:
                    stats = GridSliceStatistics(sample_count=0, null_count=nulls)

                units_out = "degC"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported derived field computation type: '{req.derived_type}'.",
                )

        # Record Provenance Event
        now_utc = get_utc_now()
        provenance = Provenance(
            dataset_id=asset.dataset_id,
            action="SCIENTIFIC_DERIVATION",
            source=f"array-asset:{asset.id}",
            actor="scientific-processing-service",
            timestamp=now_utc,
            details={
                "derived_type": req.derived_type,
                "asset_id": str(asset.id),
                "sample_count": stats.sample_count,
            },
        )
        db.add(provenance)
        db.commit()
        db.refresh(provenance)

        return DerivedFieldResponse(
            derived_type=req.derived_type,
            units=units_out,
            shape=[len(lats_out), len(lons_out)],
            lons=lons_out,
            lats=lats_out,
            data_grid=mag_grid,
            statistics=stats,
            provenance_id=provenance.id,
        )
