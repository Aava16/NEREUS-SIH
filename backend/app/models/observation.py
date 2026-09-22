from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, SmallInteger, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.platform import Platform
    from app.models.variable import Variable


class Observation(Base):
    """Canonical in-situ or sampled oceanographic observation point."""

    __tablename__ = "observations"
    __table_args__ = (
        Index("idx_observations_dataset_time", "dataset_id", "observed_at"),
        Index("idx_observations_variable_time", "variable_id", "observed_at"),
        Index("idx_observations_platform_time", "platform_id", "observed_at"),
        Index("idx_observations_depth", "depth_m"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platforms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    depth_m: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    geometry: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )
    quality_flag: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
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

    # Relationships
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="observations",
    )
    variable: Mapped["Variable"] = relationship(
        "Variable",
        back_populates="observations",
    )
    platform: Mapped[Optional["Platform"]] = relationship(
        "Platform",
        back_populates="observations",
    )
