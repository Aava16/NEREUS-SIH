from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset


class ProcessingJob(Base):
    """Canonical tracking of asynchronous ingestion, QC validation, coordinate normalization, or indexing jobs."""

    __tablename__ = "processing_jobs"
    __table_args__ = (
        Index("idx_processing_jobs_dataset_status", "dataset_id", "status"),
        Index("idx_processing_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="QUEUED",
        server_default="QUEUED",
        index=True,
    )
    initiated_by: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    logs_uri: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )
    job_metadata: Mapped[dict] = mapped_column(
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

    # Relationships
    dataset: Mapped[Optional["Dataset"]] = relationship(
        "Dataset",
        back_populates="processing_jobs",
    )
