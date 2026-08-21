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

    def get_by_organization(self, organization_id: UUID) -> list[Project]:

        return (
            self.db.query(Project)
            .filter(
                Project.organization_id == organization_id
            )
            .order_by(Project.created_at.desc())
            .all()
        )

    def get_by_id_in_organization(self, project_id: UUID, organization_id: UUID) -> Project | None:

        return (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
            .first()
        )

    def update(self, project: Project, name: str | None, description: str | None) -> Project:

        if name is not None:
            project.name = name

        if description is not None:
            project.description = description

        self.db.commit()
        self.db.refresh(project)

        return project

    def delete(self, project: Project) -> None:

        self.db.delete(project)
        self.db.commit()