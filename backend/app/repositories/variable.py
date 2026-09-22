from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.variable import Variable


class VariableRepository:
    """Repository handling persistence and lookup for oceanographic variables."""

    def get_by_id(self, db: Session, variable_id: uuid.UUID) -> Optional[Variable]:
        """Fetch a variable by its unique primary key UUID."""
        stmt = select(Variable).where(Variable.id == variable_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_dataset_and_name(self, db: Session, dataset_id: uuid.UUID, name: str) -> Optional[Variable]:
        """Fetch a variable by its dataset reference and canonical parameter name."""
        stmt = select(Variable).where(
            Variable.dataset_id == dataset_id,
            Variable.name == name,
        )
        return db.execute(stmt).scalar_one_or_none()

    def list_variables(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        standard_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Variable]:
        """List variables with optional dataset and standard_name filtering."""
        stmt = select(Variable)

        if dataset_id:
            stmt = stmt.where(Variable.dataset_id == dataset_id)
        if standard_name:
            stmt = stmt.where(Variable.standard_name.ilike(f"%{standard_name}%"))

        stmt = stmt.order_by(Variable.created_at.asc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def create(self, db: Session, variable_data: Dict[str, Any]) -> Variable:
        """Create and persist a new variable record."""
        variable = Variable(**variable_data)
        db.add(variable)
        db.commit()
        db.refresh(variable)
        return variable

    def update(self, db: Session, variable: Variable, update_data: Dict[str, Any]) -> Variable:
        """Update existing variable attributes."""
        for field, value in update_data.items():
            setattr(variable, field, value)
        db.commit()
        db.refresh(variable)
        return variable

    def delete(self, db: Session, variable: Variable) -> None:
        """Delete a variable entity."""
        db.delete(variable)
        db.commit()
