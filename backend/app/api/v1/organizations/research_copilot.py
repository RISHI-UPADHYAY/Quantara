from __future__ import annotations

from pathlib import Path
from typing import Any
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.models.user import User
from app.models.organization_member import OrganizationMember
from app.dependencies.organization import require_organization_role
from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.research_copilot import (
    ResearchCopilotRequest,
    ResearchCopilotResponse,
    ResearchEvidence,
)
from app.services.research.ollama_provider import OllamaProvider
from app.services.research.research_context_service import ResearchContextService
from app.services.research.research_copilot_service import ResearchCopilotService


router = APIRouter()

RESEARCH_ROOT = (
    Path(__file__).resolve().parents[4] / "storage"
).resolve()


def _resolve_file(file_path: str) -> Path:
    path = (RESEARCH_ROOT / file_path).resolve()

    if path != RESEARCH_ROOT and RESEARCH_ROOT not in path.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid research file path.",
        )

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research file not found.",
        )

    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research path is not a file.",
        )

    return path


def _load_dataframe(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".csv":
            return pd.read_csv(file_path)

        if suffix in {".parquet", ".pq"}:
            return pd.read_parquet(file_path)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to load research dataset: {exc}",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Unsupported research file format. "
            "Supported formats: CSV and Parquet."
        ),
    )


def _validate_dataset(
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    db: Session,
) -> Any:
    repository = DatasetRepository(db)

    dataset = repository.get_by_id_in_project(
        dataset_id=dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset


def _resolve_dataset_version(
    *,
    dataset: Any,
    dataset_version_id: uuid.UUID | None,
) -> Any:
    if dataset_version_id is not None:
        for version in getattr(dataset, "versions", []) or []:
            if version.id == dataset_version_id:
                return version

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset version not found.",
        )

    versions = list(getattr(dataset, "versions", []) or [])

    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset does not have any versions.",
        )

    return max(
        versions,
        key=lambda version: version.version,
    )


@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/research/copilot",
    response_model=ResearchCopilotResponse,
    status_code=status.HTTP_200_OK,
)
def research_copilot(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    data: ResearchCopilotRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
) -> ResearchCopilotResponse:
    dataset = _validate_dataset(
        organization_id=organization_id,
        project_id=project_id,
        dataset_id=dataset_id,
        db=db,
    )

    dataset_version = _resolve_dataset_version(
        dataset=dataset,
        dataset_version_id=data.dataset_version_id,
    )

    storage_uri = getattr(
        dataset_version,
        "storage_uri",
        None,
    )

    if not storage_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset version does not have a storage URI.",
        )

    requested_file_path = Path(data.file_path)

    if requested_file_path.is_absolute():
        file_path = requested_file_path.resolve()

        if (
            file_path != RESEARCH_ROOT
            and RESEARCH_ROOT not in file_path.parents
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid research file path.",
            )
    else:
        file_path = _resolve_file(data.file_path)

    expected_file_path = _resolve_file(storage_uri)

    if file_path != expected_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The supplied file_path does not match the selected "
                "dataset version."
            ),
        )

    dataframe = _load_dataframe(file_path)

    try:
        service = ResearchCopilotService(
            context_service=ResearchContextService(),
            provider=OllamaProvider(),
        )

        result = service.answer(
            dataframe=dataframe,
            question=data.question,
            file_path=str(file_path),
            symbols=data.symbols,
            periods_per_year=data.periods_per_year,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ResearchCopilotResponse(
        question=data.question,
        answer=result["answer"],
        provider=result["provider"],
        dataset_id=dataset.id,
        dataset_version_id=dataset_version.id,
        symbols=result["context"].get("symbols", []),
        evidence=[
            ResearchEvidence(**item)
            for item in result.get("evidence", [])
        ],
        context=result["context"],
    )