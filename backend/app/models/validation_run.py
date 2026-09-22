from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.variable import Variable


class ValidationRun(Base):
    """Canonical model verification record comparing numerical model predictions against ground-truth in-situ observations."""

    __tablename__ = "validation_runs"
    __table_args__ = (
        Index("idx_validation_runs_model_var", "model_dataset_id", "variable_id"),
        Index("idx_validation_runs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    model_dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    variable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    spatial_scope_geom: Mapped[Optional[Geometry]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
        nullable=True,
    )
    time_range_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    time_range_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    depth_level_min: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    depth_level_max: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    metric_mae: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    metric_rmse: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    metric_bias: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    metric_correlation: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    result_payload: Mapped[dict] = mapped_column(
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
    model_dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        foreign_keys=[model_dataset_id],
        back_populates="validation_runs",
    )
    variable: Mapped["Variable"] = relationship(
        "Variable",
        foreign_keys=[variable_id],
    )
