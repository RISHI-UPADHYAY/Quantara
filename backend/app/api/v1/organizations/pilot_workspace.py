from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.auth import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.schemas.pilot_workspace import PilotWorkspaceOverviewResponse
from app.services.pilot.pilot_workspace_service import PilotWorkspaceService


router = APIRouter()


@router.get(
    "/{organization_id}/projects/{project_id}/pilot/overview",
    response_model=PilotWorkspaceOverviewResponse,
    status_code=status.HTTP_200_OK,
)
def get_pilot_workspace_overview(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    start_time: datetime | None = Query(
        default=None,
        description="Optional inclusive start of the workspace reporting period.",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="Optional inclusive end of the workspace reporting period.",
    ),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    service = PilotWorkspaceService(db=db)

    return service.get_overview(
        organization_id=organization_id,
        project_id=project_id,
        start_time=start_time,
        end_time=end_time,
    )