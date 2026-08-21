import uuid

from sqlalchemy.orm import Session

from app.models.dataset_version import DatasetVersion


class DatasetVersionRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_version(self, dataset_id: uuid.UUID, created_by: uuid.UUID, storage_uri: str | None = None, row_count: int | None = None, checksum: str | None = None, schema_hash: str | None = None) -> DatasetVersion:

        latest_version = (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version.desc())
            .first()
        )

        next_version = 1 if latest_version is None else latest_version.version + 1

        dataset_version = DatasetVersion(
            dataset_id=dataset_id,
            version=next_version,
            status="active",
            storage_uri=storage_uri,
            row_count=row_count,
            checksum=checksum,
            schema_hash=schema_hash,
            created_by=created_by,
        )

        self.db.add(dataset_version)
        self.db.commit()
        self.db.refresh(dataset_version)

        return dataset_version


    def get_version(self, dataset_id: uuid.UUID, version: int) -> DatasetVersion | None:

        return (
            self.db.query(DatasetVersion)
            .filter(
                DatasetVersion.dataset_id == dataset_id,
                DatasetVersion.version == version,
            )
            .first()
        )


    def list_versions(self, dataset_id: uuid.UUID) -> list[DatasetVersion]:

        return (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version.desc())
            .all()
        )


    def get_latest_version(self, dataset_id: uuid.UUID) -> DatasetVersion | None:

        return (
            self.db.query(DatasetVersion)
            .filter(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version.desc())
            .first()
        )


    def get_by_id_for_dataset(self, dataset_version_id: uuid.UUID, dataset_id: uuid.UUID) -> DatasetVersion | None:

        return (
            self.db.query(DatasetVersion)
            .filter(
                DatasetVersion.id == dataset_version_id,
                DatasetVersion.dataset_id == dataset_id,
            )
            .first()
        )