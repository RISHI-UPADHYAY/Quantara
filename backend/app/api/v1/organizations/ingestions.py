from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.repositories.ingestion_repository import IngestionRepository
from app.schemas.ingestion import IngestionCreate, IngestionResponse, IngestionFailRequest
from app.services.ingestion_service import IngestionService

router = APIRouter()

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ingestion(organization_id: UUID, project_id: UUID, dataset_id: UUID, data: IngestionCreate, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
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

    if dataset.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot create ingestion for archived dataset",
        )

    dataset_version_repository = DatasetVersionRepository(db)

    dataset_version = dataset_version_repository.get_by_id_for_dataset(
        dataset_version_id=data.dataset_version_id,
        dataset_id=dataset_id,
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset version not found",
        )

    ingestion_service = IngestionService(db)

    return ingestion_service.create_ingestion(
        dataset_id=dataset_id,
        dataset_version_id=data.dataset_version_id,
        source_filename=data.source_filename,
        storage_key=data.storage_key,
        file_size_bytes=data.file_size_bytes,
        checksum=data.checksum,
        created_by=membership.user_id,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions",
    response_model=list[IngestionResponse],
)
def list_ingestion(organization_id: UUID, project_id: UUID, dataset_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
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

    ingestion_repository = IngestionRepository(db)

    return ingestion_repository.list_by_dataset(
        dataset_id=dataset_id,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions/{ingestion_id}",
    response_model=IngestionResponse,
)
def get_ingestion(organization_id: UUID, project_id: UUID, dataset_id: UUID, ingestion_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
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

    ingestion_repository = IngestionRepository(db)

    ingestion = ingestion_repository.get_by_id_for_dataset(
        ingestion_id=ingestion_id,
        dataset_id=dataset_id,
    )

    if ingestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return ingestion    


@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions/{ingestion_id}/start",
    response_model=IngestionResponse,
)
def start_ingestion(organization_id: UUID, project_id: UUID, dataset_id: UUID, ingestion_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
    ingestion_repository = IngestionRepository(db)

    ingestion = ingestion_repository.get_by_id_for_dataset(
        ingestion_id=ingestion_id,
        dataset_id=dataset_id,
    )

    if ingestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion not found",
        )

    service = IngestionService(db)

    try:
        return service.start_ingestion(ingestion)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        )


@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions/{ingestion_id}/complete",
    response_model=IngestionResponse,
)
def complete_ingestion(organization_id: UUID, project_id: UUID, dataset_id: UUID, ingestion_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
    ingestion_repository = IngestionRepository(db)

    ingestion = ingestion_repository.get_by_id_for_dataset(
        ingestion_id=ingestion_id,
        dataset_id=dataset_id,
    )

    if ingestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion not found",
        )

    service = IngestionService(db)

    try:
        return service.start_ingestion(ingestion)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        )


@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions/{ingestion_id}/fail",
    response_model=IngestionResponse,
)
def fail_ingestion(organization_id: UUID, project_id: UUID, dataset_id: UUID, ingestion_id: UUID, data: IngestionFailRequest, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):
    ingestion_repository = IngestionRepository(db)

    ingestion = ingestion_repository.get_by_id_for_dataset(
        ingestion_id=ingestion_id,
        dataset_id=dataset_id,
    )

    if ingestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingestion not found",
        )

    service = IngestionService(db)

    try:
        return service.fail_ingestion(
            ingestion=ingestion,
            error_message=data.error_message,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )