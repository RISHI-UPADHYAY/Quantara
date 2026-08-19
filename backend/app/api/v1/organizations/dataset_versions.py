import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
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
def create_dataset_version(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, payload: DatasetVersionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    dataset_version_repository = DatasetVersionRepository(db)

    return dataset_version_repository.create_version(
        dataset_id=dataset_id,
        created_by=current_user.id,
        storage_uri=payload.storage_uri,
        row_count=payload.row_count,
        checksum=payload.checksum,
        schema_hash=payload.schema_hash,
    )


@router.get(
    "/{dataset_id}/versions",
    response_model=list[DatasetVersionResponse],
)
def list_dataset_versions(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    dataset_version_repository = DatasetVersionRepository(db)

    return dataset_version_repository.list_versions(
        dataset_id=dataset_id,
    )


@router.get(
    "{dataset_id}/versions/latest",
    response_model=DatasetVersionResponse,
)
def get_latest_dataset_version(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dataset_version_repository = DatasetVersionRepository(db)

    dataset_version = dataset_version_repository.get_latest_version(
        dataset_id=dataset_id,
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
def get_dataset_version(organization_id: uuid.UUID, project_id: uuid.UUID, dataset_id: uuid.UUID, version: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dataset_version_repository = DatasetVersionRepository(db)

    dataset_verison = dataset_version_repository.get_version(
        dataset_id=dataset_id,
        version=version,
    )

    if dataset_verison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dateset version not found",
        )

    return dataset_verison