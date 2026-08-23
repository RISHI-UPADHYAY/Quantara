import csv
import hashlib
from pathlib import Path

class IngestionProcessingError(Exception):
    """
    Raised when an ingestion cannot be processed successfully.
    """

class IngestionProcessor:

    def process_csv(self, file_path: str, expected_checksum: str | None = None) -> dict:
        path = Path(file_path)

        if not path.exists():
            raise IngestionProcessingError(
                f"Source file not found: {file_path}"
            )

        if not path.is_file():
            raise IngestionProcessingError(
                f"Source path is not a file: {file_path}"
            )

        file_size_bytes = path.stat().st_size

        if file_size_bytes == 0:
            raise IngestionProcessingError(
                "Source file is empty"
            )

        checksum = self._calculate_checksum(path)

        if expected_checksum and checksum != expected_checksum:
            raise IngestionProcessingError(
                "Checksum validation failed"
            )

        row_count, columns = self._inspect_csv(path)

        return {
            "file_size_bytes": file_size_bytes,
            "checksum": checksum,
            "row_count": row_count,
            "columns": columns,
        }

    @staticmethod
    def _calculate_checksum(path: Path) -> str:
        sha256 = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        return sha256.hexdigest()


    @staticmethod
    def _inspect_csv(path: Path) -> tuple[int, list[str]]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file)

                try:
                    columns = next(reader)

                except StopIteration:
                    raise IngestionProcessingError(
                        "CSV file contains no header"
                    )

                if not columns:
                    raise IngestionProcessingError(
                        "CSV file contains an empty header"
                    )

                columns = [column.strip() for column in columns]

                if any(not column for column in columns):
                    raise IngestionProcessingError(
                        "CSV contains an column name"
                    )

                if len(set(columns)) != len(columns):
                    raise IngestionProcessingError(
                        "CSV contains duplicate column names"
                    )

                row_count = 0

                for row in reader:
                    if len(row) != len(columns):
                        raise IngestionProcessingError(
                            f"CSV row {row_count + 2} has "
                            f"{len(row)} columns; expected "
                            f"{len(columns)}"
                        )

                    row_count += 1

                return row_count, columns

        except UnicodeDecodeError as exc:
            raise IngestionProcessingError(
                "CSV file is not valid UTF-*"
            )from exc