from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.array_asset import ArrayAsset
    from app.models.observation import Observation
    from app.models.processing_job import ProcessingJob
    from app.models.provenance import Provenance
    from app.models.validation_run import ValidationRun
    from app.models.variable import Variable


class Dataset(Base):
    """Canonical representation of an oceanographic dataset, numerical model run, or data collection."""

    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    source_uri: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    dataset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    temporal_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    temporal_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    spatial_extent: Mapped[Optional[Geometry]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    variables: Mapped[List["Variable"]] = relationship(
        "Variable",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    provenance_records: Mapped[List["Provenance"]] = relationship(
        "Provenance",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    array_assets: Mapped[List["ArrayAsset"]] = relationship(
        "ArrayAsset",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    validation_runs: Mapped[List["ValidationRun"]] = relationship(
        "ValidationRun",
        foreign_keys="[ValidationRun.model_dataset_id]",
        back_populates="model_dataset",
        cascade="all, delete-orphan",
    )

