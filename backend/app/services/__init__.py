"""Domain services for NEREUS."""

from app.services.analysis import (
    CurrentsAnalyzer,
    DerivedAnalyzer,
    ScientificAnalysisService,
    SpatialAnalyzer,
    StatisticsAnalyzer,
    TemporalAnalyzer,
)
from app.services.array_asset import ArrayAssetService
from app.services.data_delivery import (
    DataDeliveryService,
    DeliveryCurrentsService,
    DeliveryDatasetService,
    DeliveryGridService,
    DeliveryProfileService,
    DeliverySliceService,
    DeliveryTimeSeriesService,
    DeliveryVariableService,
)
from app.services.dataset import DatasetService
from app.services.health import HealthService
from app.services.ingestion import IngestionService
from app.services.observation import ObservationService
from app.services.platform import PlatformService
from app.services.processing_job import ProcessingJobService
from app.services.provenance import ProvenanceService
from app.services.scientific_array import ScientificArrayReader
from app.services.scientific_processing import ScientificProcessingService
from app.services.validation_run import ValidationRunService
from app.services.variable import VariableService

__all__ = [
    "ArrayAssetService",
    "CurrentsAnalyzer",
    "DataDeliveryService",
    "DatasetService",
    "DeliveryCurrentsService",
    "DeliveryDatasetService",
    "DeliveryGridService",
    "DeliveryProfileService",
    "DeliverySliceService",
    "DeliveryTimeSeriesService",
    "DeliveryVariableService",
    "DerivedAnalyzer",
    "HealthService",
    "IngestionService",
    "ObservationService",
    "PlatformService",
    "ProcessingJobService",
    "ProvenanceService",
    "ScientificAnalysisService",
    "ScientificArrayReader",
    "ScientificProcessingService",
    "SpatialAnalyzer",
    "StatisticsAnalyzer",
    "TemporalAnalyzer",
    "ValidationRunService",
    "VariableService",
]



