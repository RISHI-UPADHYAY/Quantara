from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.data_profiling import(
    DataProfilingRequest,
    DataProfilingResponse,
)
from app.services.profiling.data_profiling_service import DataProfilingService

PROFILING_ROOT = (
    Path(__file__).resolve().parents[4] / "storage" / "profiling"
).resolve()


router = APIRouter()

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/profile",
    response_model=DataProfilingResponse,
    status_code=status.HTTP_200_OK,
)
def profile_dataset(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: DataProfilingRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db)
):
    dataset_repository = DatasetRepository(db)

    dataset = dataset_repository.get_by_id_in_project(
        dataset_id=dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    file_path = (PROFILING_ROOT / data.file_path).resolve()

    if(
        file_path != PROFILING_ROOT
        and PROFILING_ROOT not in file_path.parents
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid profiling file path",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profiling file not found",
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profiling path is not a file",
        )

    service = DataProfilingService()

    try:
        return service.profile(file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profiling file not found",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )