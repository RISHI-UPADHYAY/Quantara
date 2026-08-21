import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ingestion import Ingestion
from app.repositories.ingestion_repository import IngestionRepository


class IngestionService:

    def __init__(self, db: Session):
        self.repository = IngestionRepository(db)

    def create_ingestion(self, dataset_id: uuid.UUID, dataset_version_id: uuid.UUID, source_filename: str, storage_key: str, file_size_bytes: int, created_by: uuid.UUID, checksum: str | None = None) -> Ingestion:

        return self.repository.create(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_filename=source_filename,
            storage_key=storage_key,
            file_size_bytes=file_size_bytes,
            checksum=checksum,
            created_by=created_by,
        )

    def start_ingestion(self, ingestion: Ingestion) -> Ingestion:

        if ingestion.status != "pending":
            raise ValueError(
                f"Cannot start ingestion from status '{ingestion.status}'"
            )

        return self.repository.update(
            ingestion,
            status="processing",
            started_at=datetime.now(timezone.utc),
            error_message=None,
        )

    def complete_ingestion(self, ingestion: Ingestion) -> Ingestion:

        if ingestion.status != "processing":
            raise ValueError(
                f"Cannot complete ingestion from status '{ingestion.status}'"
            )

        return self.repository.update(
            ingestion,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            error_message=None,
        )

    def fail_ingestion(self, ingestion: Ingestion, error_message: str) -> Ingestion:

        if ingestion.status != "processing":
            raise ValueError(
                f"Ingestion fail from status '{ingestion.status}'"
            )

        return self.repository.update(
            ingestion,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            error_message=error_message,
        )