from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.organization import require_organization_role
from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.models.organization_member import OrganizationMember
from app.schemas.market_data_explorer import MarketDataExplorerResponse
from app.services.market_data.market_data_explorer_service import MarketDataExplorerService


router = APIRouter()

@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/explorer",
    response_model=MarketDataExplorerResponse,
    status_code=status.HTTP_200_OK,
)
def explore_market_data(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    version: int | None = Query(
        default=None,
        ge=1,
        description="Dataset version. Defaults to the latest version.",
    ),
    symbol: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Filter by instrument or symbol.",
    ),
    start_date: datetime | None = Query(
        default=None,
        description="Return data from this timestamp onward.",
    ),
    end_date: datetime | None = Query(
        default=None,
        description="Return data upto this timestamp",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="1-based page number.",
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Number of rows returned per page.",
    ),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    service = MarketDataExplorerService(db)

    try: 

        return service.explore(
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=dataset_id,
            version=version,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

    except ValueError as exc:

        message = str(exc)

        if message in {
            "Dataset not found",
            "Dataset version not found",
        }:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc