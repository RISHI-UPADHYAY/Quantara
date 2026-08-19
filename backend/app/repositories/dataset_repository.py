from uuid import UUID

from sqlalchemy.orm import Session

from app.models.dataset import Dataset

class DatasetRepository:  

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, dataset_id: UUID) -> Dataset:

        return (
            self.db.query(Dataset)
            .filter(
                Dataset.id == dataset_id
            )
            .first()
        )

    def get_by_id_in_project(self, dataset_id: UUID, organization_id: UUID, project_id: UUID) -> Dataset | None:

        return (
            self.db.query(Dataset)
            .filter(
                Dataset.id == dataset_id,
                Dataset.organization_id == organization_id,
                Dataset.project_id == project_id,   
            )
            .first()
        )

    def get_by_project(self, organization_id: UUID, project_id: UUID) -> list[Dataset]:

        return (
            self.db.query(Dataset)
            .filter(
                Dataset.organization_id == organization_id,
                Dataset.project_id == project_id,
                Dataset.is_archived.is_(False),
            )
            .order_by(
                Dataset.created_at.desc()
            )
            .all()
        )

    def create(self, organization_id: UUID, project_id: UUID, name: str, description: str | None, asset_class: str, market: str, frequency: str, source: str, storage_uri: str | None, created_by: UUID) -> Dataset:

        dataset = Dataset(
            organization_id=organization_id,
            project_id=project_id,
            name=name,
            description=description,
            asset_class=asset_class,
            market=market,
            frequency=frequency,
            source=source,
            storage_uri=storage_uri,
            created_by=created_by,
        )

        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)

        return dataset