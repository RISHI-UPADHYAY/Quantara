from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.repositories.execution_order_repository import ExecutionOrderRepository
from app.schemas.execution import (
    ExecutionFillCreateRequest,
    ExecutionOrderCreateRequest,
)
from app.services.ingestion_processor import IngestionProcessor


class ExecutionDataBridgeService:
    """
    Bridges a validated ingestion dataset into the execution domain.

    Dataset model:
        - one row contains order-level data
        - fill columns are optional
        - repeated external_order_id values represent multiple fills
          for the same execution order

    Guarantees:
        - tenant/project scoped lookup
        - idempotent order import
        - idempotent fill import
        - no synthetic fills
        - one transaction for the complete import
        - rollback on any import failure
    """

    REQUIRED_FIELDS = {
        "external_order_id",
        "symbol",
        "side",
        "quantity",
        "order_type",
        "submitted_at",
    }

    FILL_FIELDS = {
        "external_fill_id",
        "fill_price",
        "fill_quantity",
        "executed_at",
        "fill_venue",
        "commission",
        "fees",
    }

    def __init__(self, db: Session):
        self.db = db
        self.order_repository = ExecutionOrderRepository(db)
        self.fill_repository = ExecutionFillRepository(db)

    def import_csv(
        self,
        *,
        file_path: str | Path,
        organization_id: UUID,
        project_id: UUID,
        created_by: UUID,
    ) -> dict[str, Any]:
        path = Path(file_path)

        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution dataset file not found.",
            )

        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Execution dataset path is not a file.",
            )

        rows = self._read_csv(path)

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Execution dataset contains no rows.",
            )

        rows = self._canonicalize_rows(rows)

        summary = {
            "requested_rows": len(rows),
            "orders_created": 0,
            "orders_skipped": 0,
            "fills_created": 0,
            "fills_skipped": 0,
            "errors": [],
            "warnings": [],
        }

        order_cache: dict[str, Any] = {}

        try:
            for row_number, raw_row in enumerate(rows, start=2):
                row = self._normalize_row(raw_row)

                try:
                    external_order_id = self._required_value(
                        row,
                        "external_order_id",
                    )

                    order = order_cache.get(external_order_id)

                    if order is None:
                        order = (
                            self.order_repository.get_by_external_order_id(
                                organization_id=organization_id,
                                project_id=project_id,
                                external_order_id=external_order_id,
                            )
                        )

                    order_was_created = False

                    if order is None:
                        order_request = self._build_order_request(row)

                        order = self.order_repository.create(
                            organization_id=organization_id,
                            project_id=project_id,
                            created_by=created_by,
                            external_order_id=order_request.external_order_id,
                            client_order_id=order_request.client_order_id,
                            symbol=order_request.symbol,
                            side=order_request.side,
                            quantity=order_request.quantity,
                            order_type=order_request.order_type,
                            limit_price=order_request.limit_price,
                            strategy=order_request.strategy,
                            algorithm=order_request.algorithm,
                            venue=order_request.venue,
                            status=order_request.status,
                            submitted_at=order_request.submitted_at,
                            completed_at=order_request.completed_at,
                            commit=False,
                        )

                        summary["orders_created"] += 1
                        order_was_created = True

                    elif external_order_id not in order_cache:
                        summary["orders_skipped"] += 1

                    order_cache[external_order_id] = order

                    if self._has_fill_data(row):
                        fill_result = self._import_fill(
                            row=row,
                            order=order,
                            organization_id=organization_id,
                            project_id=project_id,
                        )

                        if fill_result == "created":
                            summary["fills_created"] += 1
                        elif fill_result == "skipped":
                            summary["fills_skipped"] += 1

                except HTTPException:
                    raise

                except ValidationError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail={
                            "message": (
                                f"Execution import failed at CSV row "
                                f"{row_number}."
                            ),
                            "errors": exc.errors(),
                        },
                    ) from exc

                except Exception as exc:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=(
                            f"Execution import failed at CSV row "
                            f"{row_number}: {exc}"
                        ),
                    ) from exc

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return summary

    def _import_fill(
        self,
        *,
        row: dict[str, str],
        order: Any,
        organization_id: UUID,
        project_id: UUID,
    ) -> str:
        """
        Import one fill.

        Returns:
            "created"
            "skipped"
        """

        external_fill_id = self._optional_value(
            row,
            "external_fill_id",
        )

        if not external_fill_id:
            raise ValueError(
                "external_fill_id is required when fill data is present."
            )

        fill_request = self._build_fill_request(row)

        existing_fill = (
            self.fill_repository.get_by_external_fill_id(
                execution_order_id=order.id,
                external_fill_id=external_fill_id,
            )
        )

        if existing_fill is not None:
            return "skipped"

        existing_fills = self.fill_repository.list_by_order(
            execution_order_id=order.id,
        )

        filled_quantity = sum(
            Decimal(str(fill.quantity))
            for fill in existing_fills
        )

        requested_quantity = Decimal(
            str(fill_request.quantity)
        )

        if (
            filled_quantity + requested_quantity
            > Decimal(str(order.quantity))
        ):
            raise ValueError(
                "Fill quantity exceeds remaining order quantity. "
                f"order_quantity={order.quantity}, "
                f"already_filled={filled_quantity}, "
                f"requested_fill={requested_quantity}"
            )

        if (
            fill_request.executed_at.tzinfo is None
        ) != (
            order.submitted_at.tzinfo is None
        ):
            raise ValueError(
                "executed_at and submitted_at must both be "
                "timezone-aware or both be timezone-naive."
            )

        if fill_request.executed_at < order.submitted_at:
            raise ValueError(
                "executed_at cannot be earlier than submitted_at."
            )

        self.fill_repository.create(
            execution_order_id=order.id,
            external_fill_id=fill_request.external_fill_id,
            price=fill_request.price,
            quantity=fill_request.quantity,
            venue=fill_request.venue,
            executed_at=fill_request.executed_at,
            commission=fill_request.commission,
            fees=fill_request.fees,
            commit=False,
        )

        return "created"

    def _build_order_request(
        self,
        row: dict[str, str],
    ) -> ExecutionOrderCreateRequest:
        return ExecutionOrderCreateRequest(
            external_order_id=self._required_value(
                row,
                "external_order_id",
            ),
            client_order_id=self._optional_value(
                row,
                "client_order_id",
            ),
            symbol=self._required_value(
                row,
                "symbol",
            ).upper(),
            side=self._required_value(
                row,
                "side",
            ).lower(),
            quantity=float(
                self._decimal(
                    row,
                    "quantity",
                )
            ),
            order_type=self._required_value(
                row,
                "order_type",
            ).lower(),
            limit_price=self._optional_float(
                row,
                "limit_price",
            ),
            strategy=self._optional_value(
                row,
                "strategy",
            ),
            algorithm=self._optional_value(
                row,
                "algorithm",
            ),
            venue=self._optional_value(
                row,
                "venue",
            ),
            status=(
                self._optional_value(row, "status")
                or "pending"
            ).lower(),
            submitted_at=self._datetime(
                row,
                "submitted_at",
            ),
            completed_at=self._optional_datetime(
                row,
                "completed_at",
            ),
        )

    def _build_fill_request(
        self,
        row: dict[str, str],
    ) -> ExecutionFillCreateRequest:
        return ExecutionFillCreateRequest(
            external_fill_id=self._required_value(
                row,
                "external_fill_id",
            ),
            price=float(
                self._decimal(
                    row,
                    "fill_price",
                )
            ),
            quantity=float(
                self._decimal(
                    row,
                    "fill_quantity",
                )
            ),
            venue=self._optional_value(
                row,
                "fill_venue",
            ),
            executed_at=self._datetime(
                row,
                "executed_at",
            ),
            commission=self._optional_float(
                row,
                "commission",
            ),
            fees=self._optional_float(
                row,
                "fees",
            ),
        )

    def _canonicalize_rows(
        self,
        rows: list[dict[str, str]],
    ) -> list[dict[str, str]]:

        if not rows:
            return rows

        original_columns = list(rows[0].keys())

        column_mapping = IngestionProcessor._build_column_mapping(
            original_columns
        )

        canonical_rows: list[dict[str, str]] = []

        for row_number, row in enumerate(rows, start=2):
            canonical_row: dict[str, str] = {}

            for original_column, canonical_column in column_mapping.items():
                value = row.get(original_column)

                if isinstance(value, str):
                    value = value.strip()

                canonical_row[canonical_column] = value

            missing = sorted(
                self.REQUIRED_FIELDS
                - set(canonical_row.keys())
            )

            if missing:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail={
                        "message": (
                            f"Execution dataset is missing required "
                            f"columns at row {row_number}."
                        ),
                        "missing_columns": missing,
                    },
                )

            canonical_rows.append(canonical_row)

        return canonical_rows

    @staticmethod
    def _read_csv(
        path: Path,
    ) -> list[dict[str, str]]:
        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                reader = csv.DictReader(handle)

                if not reader.fieldnames:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Execution dataset contains no CSV header.",
                    )

                return list(reader)

        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Execution dataset must be UTF-8 encoded CSV.",
            ) from exc

        except csv.Error as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid CSV format: {exc}",
            ) from exc

    @staticmethod
    def _normalize_row(
        row: dict[str, str],
    ) -> dict[str, str]:
        normalized: dict[str, str] = {}

        for key, value in row.items():
            if key is None:
                continue

            normalized_key = (
                key.strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )

            normalized[normalized_key] = (
                value.strip()
                if isinstance(value, str)
                else value
            )

        return normalized

    @staticmethod
    def _required_value(
        row: dict[str, str],
        field: str,
    ) -> str:
        value = row.get(field)

        if value is None or str(value).strip() == "":
            raise ValueError(
                f"'{field}' is required."
            )

        return str(value).strip()

    @staticmethod
    def _optional_value(
        row: dict[str, str],
        field: str,
    ) -> str | None:
        value = row.get(field)

        if value is None:
            return None

        value = str(value).strip()

        return value or None

    @classmethod
    def _decimal(
        cls,
        row: dict[str, str],
        field: str,
    ) -> Decimal:
        value = cls._required_value(
            row,
            field,
        )

        try:
            return Decimal(value)

        except (InvalidOperation, ValueError) as exc:
            raise ValueError(
                f"'{field}' must be a valid decimal."
            ) from exc

    @classmethod
    def _optional_decimal(
        cls,
        row: dict[str, str],
        field: str,
    ) -> Decimal | None:
        value = cls._optional_value(
            row,
            field,
        )

        if value is None:
            return None

        try:
            return Decimal(value)

        except (InvalidOperation, ValueError) as exc:
            raise ValueError(
                f"'{field}' must be a valid decimal."
            ) from exc

    @classmethod
    def _optional_float(
        cls,
        row: dict[str, str],
        field: str,
    ) -> float | None:
        value = cls._optional_decimal(
            row,
            field,
        )

        if value is None:
            return None

        return float(value)

    @classmethod
    def _datetime(
        cls,
        row: dict[str, str],
        field: str,
    ) -> datetime:
        value = cls._required_value(
            row,
            field,
        )

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        except ValueError as exc:
            raise ValueError(
                f"'{field}' must be a valid ISO-8601 datetime."
            ) from exc

    @classmethod
    def _optional_datetime(
        cls,
        row: dict[str, str],
        field: str,
    ) -> datetime | None:
        value = cls._optional_value(
            row,
            field,
        )

        if value is None:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        except ValueError as exc:
            raise ValueError(
                f"'{field}' must be a valid ISO-8601 datetime."
            ) from exc

    @classmethod
    def _has_fill_data(
        cls,
        row: dict[str, str],
    ) -> bool:
        return any(
            cls._optional_value(
                row,
                column,
            ) is not None
            for column in cls.FILL_FIELDS
        )