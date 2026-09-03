"""Deterministic transaction extraction from CSV exports."""

import csv
import io
from collections.abc import Sequence
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from financial_document_analyst.domain.documents import DocumentType, IngestedDocument
from financial_document_analyst.domain.transactions import TransactionInput
from financial_document_analyst.persistence.transactions import TransactionRepository


class TransactionExtractionError(ValueError):
    """Raised when a CSV cannot be normalized into valid financial transactions."""


class CsvTransactionExtractor:
    """Map common CSV columns to exact, normalized transaction records."""

    _COLUMN_ALIASES = {
        "date": {"date", "transaction_date", "booking_date"},
        "description": {"description", "details", "merchant", "counterparty"},
        "amount": {"amount", "value", "sum"},
        "currency": {"currency", "currency_code"},
        "category": {"category", "type"},
    }

    def extract(self, document: IngestedDocument, content: bytes) -> list[TransactionInput]:
        """Extract transactions when the upload is a UTF-8 CSV; skip other document types."""

        if document.document_type is not DocumentType.CSV:
            return []
        try:
            text = content.decode("utf-8-sig")
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        except (UnicodeDecodeError, csv.Error) as exc:
            raise TransactionExtractionError("CSV transaction data could not be decoded.") from exc

        if not reader.fieldnames:
            raise TransactionExtractionError("CSV transaction data needs a header row.")
        fields = self._resolve_fields(reader.fieldnames)
        required = {"date", "description", "amount"}
        missing = required - fields.keys()
        if missing:
            raise TransactionExtractionError(
                f"CSV transaction data is missing required columns: {', '.join(sorted(missing))}."
            )

        transactions: list[TransactionInput] = []
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            try:
                description = self._value(row, fields["description"])
                transactions.append(
                    TransactionInput(
                        document_id=document.id,
                        transaction_date=self._parse_date(self._value(row, fields["date"])),
                        description=description,
                        counterparty=description,
                        amount_cents=self._parse_cents(self._value(row, fields["amount"])),
                        currency=self._value(row, fields.get("currency"), default="RON").upper(),
                        category=self._value(row, fields.get("category"), default="uncategorized"),
                    )
                )
            except (ValueError, KeyError) as exc:
                raise TransactionExtractionError(
                    f"Could not normalize transaction at CSV row {row_number}."
                ) from exc
        return transactions

    def _resolve_fields(self, fieldnames: Sequence[str]) -> dict[str, str]:
        normalized = {field.casefold().strip(): field for field in fieldnames}
        return {
            canonical: normalized[alias]
            for canonical, aliases in self._COLUMN_ALIASES.items()
            for alias in aliases
            if alias in normalized
        }

    @staticmethod
    def _value(row: dict[str, str | None], field: str | None, default: str | None = None) -> str:
        if field is None:
            if default is None:
                raise KeyError("Required field is missing.")
            return default
        value = (row.get(field) or "").strip()
        if not value:
            raise ValueError("Required transaction value is empty.")
        return value

    @staticmethod
    def _parse_date(value: str) -> date:
        for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, pattern).date()
            except ValueError:
                continue
        raise ValueError("Unsupported transaction date format.")

    @staticmethod
    def _parse_cents(value: str) -> int:
        normalized = value.replace(" ", "")
        if "," in normalized and "." in normalized:
            normalized = (
                normalized.replace(".", "").replace(",", ".")
                if normalized.rfind(",") > normalized.rfind(".")
                else normalized.replace(",", "")
            )
        else:
            normalized = normalized.replace(",", ".")
        return int((Decimal(normalized) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class StructuredExtractionService:
    """Extract and persist structured transactions for supported uploads."""

    def __init__(
        self, *, extractor: CsvTransactionExtractor, repository: TransactionRepository
    ) -> None:
        self._extractor = extractor
        self._repository = repository

    def extract_and_store(self, document: IngestedDocument, content: bytes) -> int:
        """Replace one document's transactions and return its extracted row count."""

        transactions = self._extractor.extract(document, content)
        self._repository.replace_for_document(document.id, transactions)
        return len(transactions)
