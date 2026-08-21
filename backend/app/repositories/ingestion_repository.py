import uuid 

from sqlalchemy.orm import Session

from app.models.ingestion import Ingestion

class IngestionRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, dataset_id: uuid.UUID, dataset_version_id: uuid.UUID, source_filename: str, storage_key: str, file_size_bytes: int, created_by: uuid.UUID, checksum: str | None = None) -> Ingestion:
        ingestion = Ingestion(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            status="pending",
            source_filename=source_filename,
            storage_key=storage_key,
            file_size_bytes=file_size_bytes,
            checksum=checksum,
            created_by=created_by,
        )

        self.db.add(ingestion)
        self.db.commit()
        self.db.refresh(ingestion)

        return ingestion

    def get_by_id(self, ingestion_id: uuid.UUID) -> Ingestion | None:
        return (
            self.db.query(Ingestion)
            .filter(
                Ingestion.id == ingestion_id,
            )
            .first()
        )

    def get_by_id_for_dataset(self, ingestion_id: uuid.UUID, dataset_id: uuid.UUID) -> Ingestion | None:
        return (
            self.db.query(Ingestion)
            .filter(
                Ingestion.id == ingestion_id,
                Ingestion.dataset_id == dataset_id,
            )
            .first()
        )

    def list_by_dataset(self, dataset_id: uuid.UUID) -> list[Ingestion]:
        return(
            self.db.query(Ingestion)
            .filter(
                Ingestion.dataset_id == dataset_id,
            )
            .order_by(Ingestion.created_at.desc())
            .all()
        )

    def update(self, ingestion: Ingestion, **fields) -> Ingestion:

        for field, value in fields.items():
            setattr(ingestion, field, value)

        self.db.commit()
        self.db.refresh(ingestion)

        return ingestion 

    def save(self, ingestion: Ingestion) -> Ingestion:
        self.db.commit()
        self.db.refresh(ingestion)

        return ingestion