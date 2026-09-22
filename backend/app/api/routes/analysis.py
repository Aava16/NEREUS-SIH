"""API endpoints for scientific data analysis in NEREUS.

Provides routes for dataset statistics, spatial bounds, temporal ranges,
ocean currents, and comprehensive analysis summaries.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import (
    CurrentsAnalysisResponse,
    DatasetAnalysisSummaryResponse,
    DatasetStatisticsResponse,
    SpatialAnalysisResponse,
    TemporalAnalysisResponse,
)
from app.services.analysis.service import ScientificAnalysisService

router = APIRouter(prefix="/analysis", tags=["Scientific Analysis"])
analysis_service = ScientificAnalysisService()


@router.get(
    "/datasets/{dataset_id}/statistics",
    response_model=DatasetStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute dataset variable statistics",
    description=(
        "Computes descriptive statistics (min, max, mean, median, std, percentiles p25-p95, valid/missing counts) "
        "for one or all variables in a registered ocean dataset without loading dense arrays into PostgreSQL."
    ),
)
def get_dataset_statistics(
    dataset_id: UUID,
    variable: str | None = Query(
        None, description="Optional specific variable name to analyze. If omitted, computes for all variables."
    ),
    asset_id: UUID | None = Query(
        None, description="Optional specific array asset ID to analyze if dataset has multiple assets."
    ),
    db: Session = Depends(get_db),
) -> DatasetStatisticsResponse:
    """Compute dataset variable statistics."""
    return analysis_service.get_dataset_statistics(
        db=db, dataset_id=dataset_id, variable=variable, asset_id=asset_id
    )


@router.get(
    "/datasets/{dataset_id}/spatial",
    response_model=SpatialAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze dataset spatial extent and depth",
    description="Extracts 2D bounding coordinates (latitude/longitude ranges and grid resolution) and vertical depth levels.",
)
def get_dataset_spatial_analysis(
    dataset_id: UUID,
    asset_id: UUID | None = Query(
        None, description="Optional specific array asset ID to analyze."
    ),
    db: Session = Depends(get_db),
) -> SpatialAnalysisResponse:
    """Analyze dataset spatial extent and depth."""
    return analysis_service.get_spatial_analysis(
        db=db, dataset_id=dataset_id, asset_id=asset_id
    )


@router.get(
    "/datasets/{dataset_id}/temporal",
    response_model=TemporalAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze dataset temporal range and resolution",
    description="Extracts temporal start/end dates, total timesteps, sampling interval deltas, and regularity metrics.",
)
def get_dataset_temporal_analysis(
    dataset_id: UUID,
    asset_id: UUID | None = Query(
        None, description="Optional specific array asset ID to analyze."
    ),
    db: Session = Depends(get_db),
) -> TemporalAnalysisResponse:
    """Analyze dataset temporal range and resolution."""
    return analysis_service.get_temporal_analysis(
        db=db, dataset_id=dataset_id, asset_id=asset_id
    )


@router.get(
    "/datasets/{dataset_id}/currents",
    response_model=CurrentsAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze ocean current velocity fields",
    description=(
        "Computes current speed magnitude (sqrt(u^2 + v^2 (+ w^2))), flow direction [0, 360 deg), "
        "and velocity component distributions from U/V/W vector fields."
    ),
)
def get_dataset_currents_analysis(
    dataset_id: UUID,
    u_var: str | None = Query(
        None, description="Optional eastward velocity variable name (defaults to auto-detection: u, uo, water_u)"
    ),
    v_var: str | None = Query(
        None, description="Optional northward velocity variable name (defaults to auto-detection: v, vo, water_v)"
    ),
    w_var: str | None = Query(
        None, description="Optional vertical velocity variable name (defaults to auto-detection: w, wo, water_w)"
    ),
    asset_id: UUID | None = Query(
        None, description="Optional specific array asset ID to analyze."
    ),
    db: Session = Depends(get_db),
) -> CurrentsAnalysisResponse:
    """Analyze ocean current velocity fields."""
    return analysis_service.get_currents_analysis(
        db=db,
        dataset_id=dataset_id,
        u_var=u_var,
        v_var=v_var,
        w_var=w_var,
        asset_id=asset_id,
    )


@router.get(
    "/datasets/{dataset_id}/summary",
    response_model=DatasetAnalysisSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive dataset analysis summary",
    description="Aggregates spatial bounding extent, depth range, temporal coverage, and key variable distributions.",
)
def get_dataset_analysis_summary(
    dataset_id: UUID,
    asset_id: UUID | None = Query(
        None, description="Optional specific array asset ID to analyze."
    ),
    db: Session = Depends(get_db),
) -> DatasetAnalysisSummaryResponse:
    """Generate comprehensive dataset analysis summary."""
    return analysis_service.get_dataset_summary(
        db=db, dataset_id=dataset_id, asset_id=asset_id
    )
