import csv
import hashlib
from pathlib import Path
from typing import Any


class IngestionProcessingError(Exception):
    """
    Raised when an ingestion cannot be processed successfully.
    """


class IngestionProcessor:

    REQUIRED_COLUMNS = {
        "symbol",
        "side",
        "quantity",
        "order_type",
        "submitted_at",
    }

    COLUMN_ALIASES = {
        "symbol": {
            "symbol",
            "ticker",
            "instrument",
        },
        "side": {
            "side",
            "direction",
        },
        "quantity": {
            "quantity",
            "qty",
            "order_quantity",
        },
        "order_type": {
            "order_type",
            "ordertype",
            "type",
        },
        "submitted_at": {
            "submitted_at",
            "submission_time",
            "submission_timestamp",
            "order_time",
            "order_timestamp",
            "timestamp",
            "datetime",
        },
        "completed_at": {
            "completed_at",
            "completion_time",
            "completion_timestamp",
        },
        "strategy": {
            "strategy",
        },
        "algorithm": {
            "algorithm",
            "algo",
        },
        "venue": {
            "venue",
            "exchange",
            "market",
        },
        "status": {
            "status",
            "order_status",
        },
        "limit_price": {
            "limit_price",
            "limit",
        },
        "external_order_id": {
            "external_order_id",
            "order_id",
            "external_id",
        },
    }

    VALID_SIDES = {"buy", "sell"}


    VALID_ORDER_TYPES = {
        "market",
        "limit",
        "stop",
        "stop_limit",
    }

    VALID_STATUSES = {
        "pending",
        "open",
        "partially_filled",
        "filled",
        "cancelled",
        "rejected",
    }

    def process_csv(
        self,
        file_path: str,
        expected_checksum: str | None = None,
    ) -> dict[str, Any]:

        path = Path(file_path)

        self._validate_file(path)

        file_size_bytes = path.stat().st_size

        checksum = self._calculate_checksum(path)

        if expected_checksum and checksum != expected_checksum:
            raise IngestionProcessingError(
                "Checksum validation failed"
            )

        (
            row_count,
            columns,
            column_mapping,
            warnings,
        ) = self._inspect_csv(path)

        canonical_columns = sorted(
            set(column_mapping.values())
        )

        missing_columns = sorted(
            self.REQUIRED_COLUMNS
            - set(canonical_columns)
        )

        if missing_columns:
            raise IngestionProcessingError(
                "Missing required columns: "
                + ", ".join(missing_columns)
            )

        schema_hash = self._calculate_schema_hash(
            canonical_columns
        )

        return {
            "file_size_bytes": file_size_bytes,
            "checksum": checksum,
            "row_count": row_count,
            "columns": columns,
            "canonical_columns": canonical_columns,
            "column_mapping": column_mapping,
            "schema_hash": schema_hash,
            "warnings": warnings,
        }


    @staticmethod
    def _validate_file(
        path: Path
    ) -> None:

        if not path.exists():
            raise IngestionProcessingError(
                f"Source file not found: {path}"
            )

        if not path.is_file():
            raise IngestionProcessingError(
                f"Source path is not a file: {path}"
            )

        if path.stat().st_size == 0:
            raise IngestionProcessingError(
                "Source file is empty"
            )


    @classmethod
    def _inspect_csv(
        cls,
        path: Path,
    ) -> tuple[
        int,
        list[str],
        dict[str, str],
        list[str],
    ]:

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise IngestionProcessingError(
                        "CSV file contains no header"
                    )

                columns = [
                    column.strip()
                    for column in reader.fieldnames
                    if column is not None
                ]

                if not columns:
                    raise IngestionProcessingError(
                        "CSV file contains an empty header"
                    )

                if any(not column for column in columns):
                    raise IngestionProcessingError(
                        "CSV contains an empty column name"
                    )

                if len(set(columns)) != len(columns):
                    raise IngestionProcessingError(
                        "CSV contains duplicate column names"
                    )

                column_mapping = cls._build_column_mapping(
                    columns
                )

                recognized_columns = set(
                    column_mapping.keys()
                )

                warnings: list[str] = []

                unknown_columns = sorted(
                    set(columns) - recognized_columns
                )

                for column in unknown_columns:
                    warnings.append(
                        f"Unknown column '{column}' will be preserved but ignored"
                    )

                row_count = 0

                for row_number, row in enumerate(
                    reader,
                    start=2,
                ):

                    row_count += 1

                    cls._validate_row(
                        row=row,
                        column_mapping=column_mapping,
                        row_number=row_number,
                    )

                if row_count == 0:
                    raise IngestionProcessingError(
                        "CSV file contains no data rows"
                    ) 

                return (
                    row_count,
                    columns,
                    column_mapping,
                    warnings,
                )

        except UnicodeDecodeError as exc:
            raise IngestionProcessingError(
                "CSV file is not valid UTF-8"
            ) from exc


    @classmethod
    def _build_column_mapping(
        cls,
        columns: list[str],
    ) -> dict[str, str]:

        mapping: dict[str, str] = {}
        used_canonical_columns: set[str] = set()

        for original_column in columns:

            normalized = (
                original_column
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )

            canonical = None

            for (
                canonical_name,
                aliases,
            ) in cls.COLUMN_ALIASES.items():

                if normalized in aliases:
                    canonical = canonical_name
                    break

            if canonical is None:
                continue

            if canonical in used_canonical_columns:
                raise IngestionProcessingError(
                    f"Multiple columns map to "
                    f"canonical column '{canonical}'"
                )

            mapping[original_column] = canonical
            used_canonical_columns.add(canonical)

        return mapping


    @classmethod
    def _validate_row(
        cls,
        row: dict[str, str | None],
        column_mapping: dict[str, str],
        row_number: int,
    ) -> None:

        canonical = {
            canonical_name: row.get(original_name)
            for original_name, canonical_name
            in column_mapping.items()
        }

        symbol = canonical.get("symbol")

        if symbol is None or not str(symbol).strip():
            raise IngestionProcessingError(
                f"Row {row_number}: symbol is required"
            )

        side = str(
            canonical.get("side", "")
        ).strip().lower()

        if side not in cls.VALID_SIDES:
            raise IngestionProcessingError(
                f"Row {row_number}: invalid side '{side}'"
            )

        quantity = canonical.get("quantity")

        try:
            quantity_value = float(quantity)

        except (TypeError, ValueError):
            raise IngestionProcessingError(
                f"Row {row_number}: quantity must be numeric"
            )

        if quantity_value <= 0:
            raise IngestionProcessingError(
                f"Row {row_number}: quantity must be greater than zero"
            )

        order_type = str(
            canonical.get("order_type", "")
        ).strip().lower()

        if order_type not in cls.VALID_ORDER_TYPES:
            raise IngestionProcessingError(
                f"Row {row_number}: invalid order_type "
                f"'{order_type}'"
            )

        submitted_at = canonical.get("submitted_at")

        if (
            submitted_at is None
            or not str(submitted_at).strip()
        ):
            raise IngestionProcessingError(
                f"Row {row_number}: submitted_at is required"
            )

        if order_type == "limit":

            limit_price = canonical.get(
                "limit_price"
            )

            if limit_price in (None, ""):
                raise IngestionProcessingError(
                    f"Row {row_number}: limit order requires limit_price"
                )

            else:

                try:
                    limit_price_value = float(
                        limit_price
                    )

                except (TypeError, ValueError):

                    raise IngestionProcessingError(
                        f"Row {row_number}: "
                        "limit_price must numeric"
                    )

                if limit_price_value <= 0:
                    raise IngestionProcessingError(
                        f"Row {row_number}: "
                        "limit_price must be greater than zero"
                    )

        status = canonical.get("status")

        if status not in (None, ""):

            normalized_status = (
                str(status)
                .strip()
                .lower()
            )

            if normalized_status not in cls.VALID_STATUSES:
                raise IngestionProcessingError(
                    f"Row {row_number}: "
                    f"invalid status '{normalized_status}'"
                )
            


    @staticmethod
    def _calculate_checksum(
        path: Path,
    ) -> str:

        sha256 = hashlib.sha256()

        with path.open("rb") as file:

            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):

                sha256.update(chunk)

        return sha256.hexdigest()


    @staticmethod
    def _calculate_schema_hash(
        canonical_columns: list[str],
    ) -> str:

        payload = "|".join(
            sorted(canonical_columns)
        )

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()