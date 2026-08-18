from uuid import UUID

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

class OrganizationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return (
            self.db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )

    def get_by_slug(self, slug: str) -> Organization | None:
        return (
            self.db.query(Organization)
            .filter(Organization.slug == slug)
            .first()
        )

    def create(self, name: str, slug: str, user_id: UUID) -> Organization:
        organization = Organization(
            name = name,
            slug = slug,
        )

        self.db.add(organization)
        self.db.flush()

        membership = OrganizationMember(
            organization_id=organization.id,
            user_id=user_id,
            role="admin",
        )

        self.db.add(membership)

        self.db.commit()
        self.db.refresh(organization)

        return organization