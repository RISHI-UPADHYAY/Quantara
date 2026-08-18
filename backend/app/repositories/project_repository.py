from uuid import UUID

from sqlalchemy.orm import Session

from app.models.project import Project

class ProjectRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: UUID) ->Project | None:
        return (
            self.db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

    def get_by_slug(self, organization_id: UUID, slug: str) -> Project | None:
        return (
            self.db.query(Project)
            .filter(
                Project.organization_id == organization_id,
                Project.slug == slug,
            )
            .first()
        )

    def create(self, organization_id: UUID, name: str, slug: str, description: str | None, created_by: UUID) -> Project:

        project = Project(
            organization_id = organization_id,
            name = name,
            slug = slug,
            description = description,
            created_by = created_by,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project