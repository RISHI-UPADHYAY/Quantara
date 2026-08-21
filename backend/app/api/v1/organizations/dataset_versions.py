import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.dependencies.dataset_access import get_accessible_dataset
from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.models.dataset import Dataset
from app.models.organization_member import OrganizationMember
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.schemas.dataset_version import (
    DatasetVersionCreate,
    DatasetVersionResponse,
)

router = APIRouter()


@router.post(
    "/{dataset_id}/versions",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_version(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, payload: DatasetVersionCreate, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), dataset: Dataset = Depends(get_accessible_dataset), db: Session = Depends(get_db)):

    if dataset.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot create a version of an archived dataset",
        )

    dataset_version_repository = DatasetVersionRepository(db)

    return dataset_version_repository.create_version(
        dataset_id=dataset_id,
        created_by=membership.user_id,
        storage_uri=payload.storage_uri,
        row_count=payload.row_count,
        checksum=payload.checksum,
        schema_hash=payload.schema_hash,
    )


@router.get(
    "/{dataset_id}/versions",
    response_model=list[DatasetVersionResponse],
)
def list_dataset_versions(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, dataset: Dataset = Depends(get_accessible_dataset), db: Session = Depends(get_db)):

    dataset_version_repository = DatasetVersionRepository(db)

    return dataset_version_repository.list_versions(
        dataset_id=dataset.id,
    )


@router.get(
    "{dataset_id}/versions/latest",
    response_model=DatasetVersionResponse,
)
def get_latest_dataset_version(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, dataset: Dataset = Depends(get_accessible_dataset), db: Session = Depends(get_db)):
    dataset_version_repository = DatasetVersionRepository(db)

    dataset_version = dataset_version_repository.get_latest_version(
        dataset_id=dataset.id,
    )

    if dataset_version is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No version found for this dataset",
        )

    return dataset_version


@router.get(
    "/{dataset_id}/versions/{version}",
    response_model=DatasetVersionResponse,
)
def get_dataset_version(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, version: int, dataset: Dataset = Depends(get_accessible_dataset), db: Session = Depends(get_db)):
    dataset_version_repository = DatasetVersionRepository(db)

    dataset_verison = dataset_version_repository.get_version(
        dataset_id=dataset.id,
        version=version,
    )

    if dataset_verison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dateset version not found",
        )

    return dataset_verison