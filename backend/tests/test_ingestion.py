import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_atomic_dataset_ingestion_manifest() -> None:
    """Test full atomic dataset catalog registration with variables, array assets, job log, and provenance."""
    ds_code = f"incois_iom_{uuid.uuid4().hex[:8]}"
    payload = {
        "name": ds_code,
        "title": "INCOIS Indian Ocean Model Forecast 1/12 deg",
        "description": "Daily 3D ocean state forecast produced by INCOIS operational suite.",
        "source": "INCOIS Hyderabad",
        "source_uri": "https://incois.gov.in/portal/datainfo/iom_forecast.jsp",
        "dataset_type": "MODEL_FORECAST",
        "temporal_start": "2026-01-01T00:00:00Z",
        "temporal_end": "2026-12-31T23:59:59Z",
        "spatial_extent": {
            "type": "Polygon",
            "coordinates": [
                [
                    [40.0, -20.0],
                    [110.0, -20.0],
                    [110.0, 30.0],
                    [40.0, 30.0],
                    [40.0, -20.0],
                ]
            ],
        },
        "metadata_json": {
            "grid_type": "curvilinear",
            "vertical_coordinate": "z-level",
            "vertical_levels_count": 50,
        },
        "variables": [
            {
                "name": "temp",
                "standard_name": "sea_water_potential_temperature",
                "long_name": "Potential Temperature",
                "units": "degC",
                "data_type": "float32",
                "description": "Potential temperature referenced to sea surface.",
                "metadata_json": {"valid_min": -2.0, "valid_max": 38.0, "colormap": "thermal"},
            },
            {
                "name": "salt",
                "standard_name": "sea_water_practical_salinity",
                "long_name": "Practical Salinity",
                "units": "PSU",
                "data_type": "float32",
                "description": "Practical salinity on the PSS-78 scale.",
                "metadata_json": {"valid_min": 0.0, "valid_max": 45.0, "colormap": "haline"},
            },
            {
                "name": "u",
                "standard_name": "eastward_sea_water_velocity",
                "long_name": "Zonal Velocity",
                "units": "m/s",
                "data_type": "float32",
                "metadata_json": {"is_vector_component": True, "vector_partner": "v"},
            },
        ],
        "array_assets": [
            {
                "storage_format": "NETCDF4",
                "uri": "s3://nereus-ocean-archive/incois/iom_2026_daily.nc",
                "variable_info": {"temp": "water_temp", "salt": "salinity", "u": "u_current"},
                "dimensions": {"time": 365, "depth": 50, "lat": 600, "lon": 840},
                "checksum": "sha256:d41d8cd98f00b204e9800998ecf8427e",
            }
        ],
        "initiated_by": "incois-sync-worker-01",
        "provenance_details": {"ingestion_pipeline_version": "2.1.0"},
    }

    res = client.post("/api/v1/ingestion/dataset", json=payload)
    assert res.status_code == 201
    data = res.json()

    # 1. Verify Dataset
    assert data["dataset"]["name"] == ds_code
    assert data["dataset"]["spatial_extent"]["type"] == "Polygon"
    dataset_id = data["dataset"]["id"]

    # 2. Verify Variables
    assert len(data["variables"]) == 3
    var_names = {v["name"] for v in data["variables"]}
    assert var_names == {"temp", "salt", "u"}

    # 3. Verify Array Assets
    assert len(data["array_assets"]) == 1
    assert data["array_assets"][0]["storage_format"] == "NETCDF4"

    # 4. Verify Processing Job Log
    assert data["processing_job"]["status"] == "COMPLETED"
    assert data["processing_job"]["job_type"] == "DATASET_INGESTION"
    assert data["processing_job"]["job_metadata"]["variables_registered"] == 3

    # 5. Verify Provenance Record
    assert data["provenance_record"]["action"] == "DATASET_INGESTION"
    assert data["provenance_record"]["actor"] == "incois-sync-worker-01"

    # 6. Test duplicate dataset rejection
    dup_res = client.post("/api/v1/ingestion/dataset", json=payload)
    assert dup_res.status_code == 409

    # Cleanup dataset
    client.delete(f"/api/v1/datasets/{dataset_id}")


def test_metadata_validation_dry_run_and_rejection_cases() -> None:
    """Test metadata validation endpoint for valid and invalid manifests."""
    valid_payload = {
        "name": f"valid_test_{uuid.uuid4().hex[:8]}",
        "title": "Validation Dry Run Test",
        "dataset_type": "MODEL_FORECAST",
        "temporal_start": "2026-01-01T00:00:00Z",
        "temporal_end": "2026-06-30T00:00:00Z",
        "spatial_extent": {
            "type": "Polygon",
            "coordinates": [[[60.0, 0.0], [90.0, 0.0], [90.0, 30.0], [60.0, 30.0], [60.0, 0.0]]],
        },
        "variables": [{"name": "temperature", "units": "degC"}],
        "array_assets": [{"storage_format": "ZARR", "uri": "s3://nereus/test.zarr"}],
    }

    val_res = client.post("/api/v1/ingestion/validate-metadata", json=valid_payload)
    assert val_res.status_code == 200
    report = val_res.json()
    assert report["is_valid"] is True
    assert report["temporal_coverage_valid"] is True
    assert report["spatial_coverage_valid"] is True
    assert len(report["validation_issues"]) == 0

    # Test Invalid Temporal Coverage (start > end)
    invalid_temporal = dict(valid_payload)
    invalid_temporal["temporal_start"] = "2026-12-31T00:00:00Z"
    invalid_temporal["temporal_end"] = "2026-01-01T00:00:00Z"

    val_temporal_res = client.post("/api/v1/ingestion/validate-metadata", json=invalid_temporal)
    assert val_temporal_res.status_code == 200
    assert val_temporal_res.json()["is_valid"] is False
    assert val_temporal_res.json()["temporal_coverage_valid"] is False

    # Attempting to ingest this invalid dataset should return 400 Bad Request
    ingest_bad_temp = client.post("/api/v1/ingestion/dataset", json=invalid_temporal)
    assert ingest_bad_temp.status_code == 400

    # Test Invalid Spatial Coverage (Unclosed ring)
    invalid_spatial = dict(valid_payload)
    invalid_spatial["spatial_extent"] = {
        "type": "Polygon",
        "coordinates": [[[60.0, 0.0], [90.0, 0.0], [90.0, 30.0], [60.0, 30.0]]],  # Not closed
    }
    val_spatial_res = client.post("/api/v1/ingestion/validate-metadata", json=invalid_spatial)
    assert val_spatial_res.status_code == 200
    assert val_spatial_res.json()["is_valid"] is False
    assert val_spatial_res.json()["spatial_coverage_valid"] is False

    # Test Invalid Variable Range (valid_min > valid_max)
    invalid_var = dict(valid_payload)
    invalid_var["variables"] = [
        {"name": "temp", "units": "degC", "metadata_json": {"valid_min": 50.0, "valid_max": 10.0}}
    ]
    val_var_res = client.post("/api/v1/ingestion/validate-metadata", json=invalid_var)
    assert val_var_res.status_code == 200
    assert val_var_res.json()["is_valid"] is False


def test_scientific_array_asset_registration_and_lookup() -> None:
    """Test standalone scientific array asset registration with provenance linkage and lookup."""
    # 1. Create parent dataset
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"standalone_asset_ds_{uuid.uuid4().hex[:8]}",
            "title": "Standalone Asset Parent Dataset",
            "dataset_type": "REANALYSIS",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 2. Register array asset via ingestion endpoint
    asset_payload = {
        "dataset_id": dataset_id,
        "storage_format": "ZARR",
        "uri": "s3://nereus-ocean-data/cmems/reanalysis_v2.zarr",
        "variable_info": {"thetao": "temperature", "so": "salinity"},
        "dimensions": {"time": 365, "depth": 50, "lat": 1440, "lon": 2880},
        "checksum": "sha256:abcd1234efgh5678",
        "initiated_by": "zarr-converter-pipeline",
        "provenance_details": {"chunk_shape": [1, 10, 100, 100]},
    }

    create_res = client.post("/api/v1/ingestion/array-asset", json=asset_payload)
    assert create_res.status_code == 201
    asset = create_res.json()
    assert asset["storage_format"] == "ZARR"
    assert asset["uri"] == asset_payload["uri"]
    asset_id = asset["id"]

    # 3. Lookup array asset via canonical asset lookup
    get_res = client.get(f"/api/v1/array-assets/{asset_id}")
    assert get_res.status_code == 200
    assert get_res.json()["dimensions"]["depth"] == 50

    # 4. Verify Provenance Record was created
    prov_res = client.get(
        "/api/v1/provenance",
        params={"dataset_id": dataset_id, "action": "ARRAY_ASSET_REGISTRATION"},
    )
    assert prov_res.status_code == 200
    prov_records = prov_res.json()
    assert len(prov_records) == 1
    assert prov_records[0]["actor"] == "zarr-converter-pipeline"

    # Cleanup dataset
    client.delete(f"/api/v1/datasets/{dataset_id}")


def test_insitu_observation_batch_ingestion() -> None:
    """Test batch in-situ observation point ingestion with platform resolution and validation."""
    # 1. Prerequisite dataset, platform, and variable
    ds_res = client.post(
        "/api/v1/datasets",
        json={
            "name": f"argo_network_{uuid.uuid4().hex[:8]}",
            "title": "Indian Ocean Argo Profiling Array",
            "dataset_type": "IN_SITU_NETWORK",
        },
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    plat_res = client.post(
        "/api/v1/platforms",
        json={
            "name": f"WMO_290{uuid.uuid4().hex[:4]}",
            "platform_type": "ARGO_FLOAT",
            "operator": "INCOIS",
        },
    )
    assert plat_res.status_code == 201
    platform_id = plat_res.json()["id"]

    var_res = client.post(
        "/api/v1/variables",
        json={
            "dataset_id": dataset_id,
            "name": "dissolved_oxygen",
            "units": "micromol/kg",
        },
    )
    assert var_res.status_code == 201
    variable_id = var_res.json()["id"]

    # 2. Ingest batch
    batch_payload = {
        "dataset_id": dataset_id,
        "variable_id": variable_id,
        "default_platform_id": platform_id,
        "observations": [
            {
                "observed_at": "2026-05-10T06:00:00Z",
                "depth_m": 5.0,
                "value": 210.4,
                "geometry": {"type": "Point", "coordinates": [85.2, 12.4]},
                "quality_flag": 1,
            },
            {
                "observed_at": "2026-05-10T06:05:00Z",
                "depth_m": 25.0,
                "value": 208.1,
                "geometry": {"type": "Point", "coordinates": [85.2, 12.4]},
                "quality_flag": 1,
            },
            {
                "observed_at": "2026-05-10T06:10:00Z",
                "depth_m": 100.0,
                "value": 145.6,
                "geometry": {"type": "Point", "coordinates": [85.2, 12.4]},
                "quality_flag": 2,
            },
        ],
        "initiated_by": "argo-gdac-sync",
    }

    ingest_res = client.post("/api/v1/ingestion/observations", json=batch_payload)
    assert ingest_res.status_code == 201
    summary = ingest_res.json()

    assert summary["records_ingested"] == 3
    assert summary["quality_flags_summary"]["1"] == 2
    assert summary["quality_flags_summary"]["2"] == 1
    assert summary["processing_job"]["status"] == "COMPLETED"
    assert summary["provenance_record"]["action"] == "INSITU_BATCH_INGESTION"

    # 3. Test coordinate bounds validation
    bad_coords_payload = dict(batch_payload)
    bad_coords_payload["observations"] = [
        {
            "observed_at": "2026-05-10T06:00:00Z",
            "depth_m": 5.0,
            "value": 210.4,
            "geometry": {"type": "Point", "coordinates": [195.0, 12.4]},  # Invalid longitude > 180
            "quality_flag": 1,
        }
    ]
    bad_res = client.post("/api/v1/ingestion/observations", json=bad_coords_payload)
    assert bad_res.status_code == 400

    # Cleanup
    client.delete(f"/api/v1/datasets/{dataset_id}")
    client.delete(f"/api/v1/platforms/{platform_id}")
