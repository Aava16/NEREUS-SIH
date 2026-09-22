from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.variable import VariableCreate, VariableRead, VariableUpdate
from app.services.variable import VariableService

router = APIRouter(prefix="/variables", tags=["Variables"])
variable_service = VariableService()


@router.get(
    "",
    response_model=List[VariableRead],
    summary="List Scientific Variables",
    description="Retrieve scientific parameters registered across datasets, filterable by dataset or CF standard name.",
)
def list_variables(
    dataset_id: Optional[uuid.UUID] = Query(None, description="Filter by parent dataset ID"),
    standard_name: Optional[str] = Query(None, description="Filter by CF convention standard name substring"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[VariableRead]:
    """List registered ocean variables."""
    return variable_service.list_variables(  # type: ignore[return-value]
        db,
        dataset_id=dataset_id,
        standard_name=standard_name,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=VariableRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register Variable",
    description="Register a new scientific parameter (e.g. salinity, potential temperature) under a dataset.",
)
def create_variable(
    payload: VariableCreate,
    db: Session = Depends(get_db),
) -> VariableRead:
    """Create a new variable parameter."""
    return variable_service.create_variable(db, payload)  # type: ignore[return-value]


@router.get(
    "/{variable_id}",
    response_model=VariableRead,
    summary="Get Variable Details",
    description="Retrieve details and scientific units for a specific parameter.",
)
def get_variable(
    variable_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> VariableRead:
    """Fetch variable by ID."""
    return variable_service.get_variable(db, variable_id)  # type: ignore[return-value]


@router.patch(
    "/{variable_id}",
    response_model=VariableRead,
    summary="Update Variable",
    description="Update metadata, units, or standard name for a variable.",
)
def update_variable(
    variable_id: uuid.UUID,
    payload: VariableUpdate,
    db: Session = Depends(get_db),
) -> VariableRead:
    """Update variable attributes."""
    return variable_service.update_variable(db, variable_id, payload)  # type: ignore[return-value]


@router.delete(
    "/{variable_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Variable",
    description="Remove a variable definition from the catalog.",
)
def delete_variable(
    variable_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete a variable by ID."""
    variable_service.delete_variable(db, variable_id)
