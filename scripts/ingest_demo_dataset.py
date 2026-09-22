"""Ingestion script for Copernicus Demonstration Dataset.

Reads data/manifests/copernicus_multiobs_glo_phy_tsuv_manifest.json
and ingests it into PostgreSQL + PostGIS via NEREUS canonical IngestionService.
"""

import json
import os
from pathlib import Path
import sys

# Ensure backend and scripts root are on Python path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from app.db.session import SessionLocal
from app.schemas.ingestion import DatasetIngestionRequest
from app.services.ingestion import IngestionService
from app.repositories.dataset import DatasetRepository


def ingest_demo_dataset() -> None:
    """Ingest Copernicus Multi-Observation Ocean Physics dataset."""
    manifest_path = ROOT_DIR / "data" / "manifests" / "copernicus_multiobs_glo_phy_tsuv_manifest.json"
    nc_path = ROOT_DIR / "data" / "processed" / "copernicus_multiobs_arabian_sea_2024.nc"

    if not nc_path.exists():
        print(f"Generating NetCDF4 asset at {nc_path}...")
        from generate_copernicus_demo_asset import generate_copernicus_dataset
        generate_copernicus_dataset(str(nc_path))

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Set absolute file URI for local storage lookup
    manifest_data["array_assets"][0]["uri"] = str(nc_path.resolve())

    payload = DatasetIngestionRequest.model_validate(manifest_data)
    service = IngestionService()
    dataset_repo = DatasetRepository()

    db = SessionLocal()
    try:
        existing = dataset_repo.get_by_name(db, payload.name)
        if existing:
            print(f"Dataset '{payload.name}' already registered in NEREUS catalog.")
            print(f"Dataset ID: {existing.id}")
            print(f"Variables count: {len(existing.variables)}")
            return

        print(f"Validating manifest metadata for '{payload.name}'...")
        validation_report = service.validate_metadata(payload)
        if not validation_report.is_valid:
            print("Validation issues encountered:")
            for issue in validation_report.validation_issues:
                print(f"  - {issue}")
            sys.exit(1)

        print("Ingesting dataset into PostgreSQL/PostGIS...")
        result = service.ingest_dataset(db, payload)
        db.commit()

        print("\n--- INGESTION SUCCESSFUL ---")
        print(f"Dataset ID:     {result.dataset.id}")
        print(f"Dataset Name:   {result.dataset.name}")
        print(f"Variables:      {len(result.variables)} registered ({', '.join(v.name for v in result.variables)})")
        print(f"Array Assets:   {len(result.array_assets)} registered")
        print(f"Provenance ID:  {result.provenance_record.id if result.provenance_record else 'N/A'}")
        print(f"Job Log ID:     {result.processing_job.id if result.processing_job else 'N/A'}")

    except Exception as exc:
        db.rollback()
        print(f"Ingestion failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingest_demo_dataset()
