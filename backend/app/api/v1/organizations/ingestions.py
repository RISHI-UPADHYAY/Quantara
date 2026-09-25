import tempfile
import uuid
from uuid import UUID
from pathlib import Path

from datetime import datetime, timezone

from fastapi import (
    APIRouter, 
    Depends, 
    File,
    HTTPException,
    UploadFile, 
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.repositories.ingestion_repository import IngestionRepository
from app.schemas.ingestion import ( 
    IngestionCreate, 
    IngestionResponse, 
    IngestionFailRequest,
    IngestionUploadResponse,
    IngestionValidationResponse, 
)
from app.services.ingestion_processor import (
    IngestionProcessor,
    IngestionProcessingError,
)
from app.services.ingestion_service import IngestionService
from app.services.storage.local import LocalStorageService


router = APIRouter()


STORAGE_ROOT = (
    Path(__file__).resolve().parents[4] / "storage"
).resolve()

TEMP_UPLOAD_ROOT = STORAGE_ROOT / ".tmp"

MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/ingestions/upload",
    response_model=IngestionUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_ingestion(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    file: UploadFile = File(...),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
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
            detail="Dataset not found.",
        )

    if dataset.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot ingest into an archive dataset.",
        )

    filename = Path(
        file.filename or ""
    ).name

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    if Path(filename).suffix.lower() != ".csv":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are supported in ingestion v1",
        )

    TEMP_UPLOAD_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = (
        TEMP_UPLOAD_ROOT
        / f"{uuid.uuid4().hex}.csv"
    )

    storage_key: str | None = None

    try:
        total_bytes = 0

        with temporary_path.open("wb") as destination:
            while True:

                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Uploaded file exceeds the 100 MB ingestion limit",
                    )

                destination.write(chunk)

        if  total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload file is empty",
            )

        processor = IngestionProcessor()

        try: 
            validation = processor.process_csv(
                str(temporary_path)
            )

        except IngestionProcessingError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

        dataset_version_repository = DatasetVersionRepository(db)

        latest_version = (
            dataset_version_repository
            .get_latest_version(dataset_id)
        )

        next_version = (
            1
            if latest_version is None
            else latest_version.version + 1
        )

        safe_filename = (
            filename
            .replace(" ", "_")
            .replace("\\", "_")
            .replace("/", "_")
        )

        storage_key = (
            f"datasets/"
            f"{dataset_id}/"
            f"versions/"
            f"{next_version}/"
            f"{uuid.uuid4().hex}_{safe_filename}"
        )

        storage = LocalStorageService(
            base_path=STORAGE_ROOT
        )

        storage.save(
            source_path=temporary_path,
            storage_key=storage_key,
        )

        ingestion_repository = IngestionRepository(db)

        dataset_version = (
            dataset_version_repository.create_version(
                dataset_id=dataset_id,
                created_by=membership.user_id,
                storage_uri=storage_key,
                row_count=validation["row_count"],
                checksum=validation["checksum"],
                schema_hash=validation["schema_hash"],
                commit=False,
            )
        )

        ingestion = ingestion_repository.create(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version.id,
            source_filename=filename,
            storage_key=storage_key,
            file_size_bytes=validation["file_size_bytes"],
            checksum=validation["checksum"],
            created_by=membership.user_id,
            commit=False,
        )

        ingestion.status = "completed"
        ingestion.completed_at = datetime.now(timezone.utc)

        db.commit()

        db.refresh(dataset_version)
        db.refresh(ingestion)

        return IngestionUploadResponse(
            ingestion=ingestion,
            dataset_version=dataset_version,
            validation=IngestionValidationResponse(
                **validation
            ),
        )

    except HTTPException:
        db.rollback()

        if storage_key is not None:
            try:
                LocalStorageService(
                    base_path=STORAGE_ROOT
                ).delete(storage_key)

            except Exception:
                pass

        raise

    except IntegrityError as exc:
        db.rollback()

        if storage_key is not None:
            try:
                LocalStorageService(
                    base_path=STORAGE_ROOT
                ).delete(storage_key)

            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create the dataset version. The dataset may have been updated concurrently.",
        ) from exc

    except Exception as exc:
        db.rollback()

        if storage_key is not None:
            try:
                LocalStorageService(
                    base_path=STORAGE_ROOT
                ).delete(storage_key)

            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded ingestion",
        ) from exc

    finally:

        try:
            temporary_path.unlink(
                missing_ok=True
            )

        except Exception:
            pass

        file.file.close()


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
        return service.complete_ingestion(ingestion)
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