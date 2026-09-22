from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.observation import Observation


class Variable(Base):
    """Canonical representation of a scientific parameter contained in an ocean dataset."""

    __tablename__ = "variables"
    __table_args__ = (
        UniqueConstraint("dataset_id", "name", name="uq_variables_dataset_name"),
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
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    standard_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )
    long_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    units: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    data_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="float32",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
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

    # Relationships
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="variables",
    )
    observations: Mapped[List["Observation"]] = relationship(
        "Observation",
        back_populates="variable",
        cascade="all, delete-orphan",
    )
