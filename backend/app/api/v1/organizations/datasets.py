from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.dataset import DatasetCreate, DatasetResponse


router = APIRouter()

@router.post(
    "/{organization_id}/projects/{project_id}/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset(organization_id: UUID, project_id: UUID, data: DatasetCreate, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
    project_repository = ProjectRepository(db)

    project = project_repository.get_by_id_in_organization(
        project_id=project_id,
        organization_id=organization_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    dataset_repository = DatasetRepository(db)

    return dataset_repository.create(
        organization_id=organization_id,
        project_id=project_id,
        name=data.name,
        description=data.description,
        asset_class=data.asset_class,
        market=data.market,
        frequency=data.frequency,
        source=data.source,
        storage_uri=data.storage_uri,
        created_by=membership.user_id,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/datasets",
    response_model=list[DatasetResponse],
)
def list_datasets(organization_id: UUID, project_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):

    project_repository = ProjectRepository(db)

    project = project_repository.get_by_id_in_organization(
        project_id=project_id,
        organization_id=organization_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    dataset_repository = DatasetRepository(db)

    return dataset_repository.get_by_project(
        organization_id=organization_id,
        project_id=project_id,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset(organization_id: UUID, project_id: UUID, dataset_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
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

    return dataset


@router.patch(
    "{organization_id}/projects/{project_id}/datasets/{dataset_id}/archive",
    response_model=DatasetResponse,
)
def archive_dataset(organization_id: UUID, project_id: UUID, dataset_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN)), db: Session = Depends(get_db)):

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

    dataset.is_archived = True

    db.commit()
    db.refresh(dataset)

    return dataset