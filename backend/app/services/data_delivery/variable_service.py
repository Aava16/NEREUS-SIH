"""Variable discovery service for scientific ocean datasets.

Inspects array variables, data types, dimensions, physical units,
valid numeric ranges, and fill values.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import numpy as np
import xarray as xr

from app.repositories.array_asset import ArrayAssetRepository
from app.repositories.dataset import DatasetRepository
from app.schemas.data_delivery import (
    VariableDiscoveryResponse,
    VariableMetadataItem,
)
from app.services.scientific_array import ScientificArrayReader


class DeliveryVariableService:
    """Discovers and describes variables within registered scientific datasets."""

    def __init__(
        self,
        dataset_repo: Optional[DatasetRepository] = None,
        array_repo: Optional[ArrayAssetRepository] = None,
        reader: Optional[ScientificArrayReader] = None,
    ) -> None:
        self.dataset_repo = dataset_repo or DatasetRepository()
        self.array_repo = array_repo or ArrayAssetRepository()
        self.reader = reader or ScientificArrayReader()

    def discover_variables(
        self, db: Session, dataset_id: UUID, asset_id: Optional[UUID] = None
    ) -> VariableDiscoveryResponse:
        """Extract variable discovery items for all data variables in a dataset."""
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
            var_items: List[VariableMetadataItem] = []

            for var_name in ds.data_vars:
                da = ds[var_name]
                attrs = da.attrs or {}

                # Safe extraction of valid_min / valid_max
                valid_min = attrs.get("valid_min")
                valid_max = attrs.get("valid_max")
                if valid_min is not None:
                    try:
                        valid_min = float(valid_min)
                    except (ValueError, TypeError):
                        valid_min = None
                if valid_max is not None:
                    try:
                        valid_max = float(valid_max)
                    except (ValueError, TypeError):
                        valid_max = None

                # Safe fill_value
                fill_val = attrs.get("_FillValue") or attrs.get("missing_value")
                if fill_val is not None:
                    try:
                        fill_val = float(fill_val)
                    except (ValueError, TypeError):
                        fill_val = None

                # Clean attributes dict (convert non-serializable objects to string)
                clean_attrs: Dict[str, Any] = {}
                for k, v in attrs.items():
                    if isinstance(v, (int, float, str, bool, list)):
                        clean_attrs[str(k)] = v
                    else:
                        clean_attrs[str(k)] = str(v)

                var_items.append(
                    VariableMetadataItem(
                        variable_name=str(var_name),
                        standard_name=str(attrs.get("standard_name")) if "standard_name" in attrs else None,
                        long_name=str(attrs.get("long_name")) if "long_name" in attrs else None,
                        units=str(attrs.get("units")) if "units" in attrs else None,
                        dtype=str(da.dtype),
                        dimensions=[str(d) for d in da.dims],
                        shape=[int(s) for s in da.shape],
                        valid_min=valid_min,
                        valid_max=valid_max,
                        fill_value=fill_val,
                        attributes=clean_attrs,
                    )
                )

            return VariableDiscoveryResponse(
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                asset_id=asset.id if asset else None,
                variables=var_items,
                total_variables=len(var_items),
            )
