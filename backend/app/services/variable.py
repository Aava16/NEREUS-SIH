import logging
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.variable import Variable
from app.repositories.dataset import DatasetRepository
from app.repositories.variable import VariableRepository
from app.schemas.variable import VariableCreate, VariableUpdate

logger = logging.getLogger(__name__)


class VariableService:
    """Service layer managing business logic and validation for ocean variables."""

    def __init__(
        self,
        repository: Optional[VariableRepository] = None,
        dataset_repo: Optional[DatasetRepository] = None,
    ) -> None:
        self.repository = repository or VariableRepository()
        self.dataset_repo = dataset_repo or DatasetRepository()

    def get_variable(self, db: Session, variable_id: uuid.UUID) -> Variable:
        """Fetch variable by ID or raise 404."""
        variable = self.repository.get_by_id(db, variable_id)
        if not variable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variable with ID '{variable_id}' was not found.",
            )
        return variable

    def list_variables(
        self,
        db: Session,
        dataset_id: Optional[uuid.UUID] = None,
        standard_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Variable]:
        """List variables with optional dataset and standard_name filter."""
        if dataset_id and not self.dataset_repo.get_by_id(db, dataset_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent dataset with ID '{dataset_id}' was not found.",
            )
        return self.repository.list_variables(
            db,
            dataset_id=dataset_id,
            standard_name=standard_name,
            limit=limit,
            offset=offset,
        )

    def create_variable(self, db: Session, payload: VariableCreate) -> Variable:
        """Validate parent dataset existence and name uniqueness, then create variable."""
        dataset = self.dataset_repo.get_by_id(db, payload.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent dataset with ID '{payload.dataset_id}' was not found.",
            )

        existing = self.repository.get_by_dataset_and_name(db, payload.dataset_id, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Variable '{payload.name}' already exists in dataset '{dataset.name}'.",
            )

        return self.repository.create(db, payload.model_dump())

    def update_variable(self, db: Session, variable_id: uuid.UUID, payload: VariableUpdate) -> Variable:
        """Update existing variable attributes."""
        variable = self.get_variable(db, variable_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != variable.name:
            conflict = self.repository.get_by_dataset_and_name(db, variable.dataset_id, update_data["name"])
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Variable '{update_data['name']}' already exists in this dataset.",
                )

        return self.repository.update(db, variable, update_data)

    def delete_variable(self, db: Session, variable_id: uuid.UUID) -> None:
        """Delete variable by ID."""
        variable = self.get_variable(db, variable_id)
        self.repository.delete(db, variable)
