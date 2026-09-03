"""Structured extraction and deterministic financial tools tests."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from financial_document_analyst.domain.documents import DocumentType, IngestedDocument
from financial_document_analyst.extraction.transactions import (
    CsvTransactionExtractor,
    TransactionExtractionError,
)
from financial_document_analyst.persistence.transactions import TransactionRepository
from financial_document_analyst.tools.financial import FinancialAnalyticsService


def _document() -> IngestedDocument:
    return IngestedDocument(
        id="doc-1",
        original_filename="statement.csv",
        document_type=DocumentType.CSV,
        content_type="text/csv",
        size_bytes=100,
        sha256="a" * 64,
        segment_count=4,
        stored_filename="doc-1.csv",
        created_at=datetime.now(UTC),
    )


def _content() -> bytes:
    return (
        b"date,description,amount,currency,category\n"
        b"2026-07-02,Acme Telecom,-49.00,RON,utilities\n"
        b"2026-08-02,Acme Telecom,-49.00,RON,utilities\n"
        b"2026-08-03,Green Garden,-86.50,RON,restaurants\n"
        b"2026-08-08,Salary,7500.00,RON,income\n"
    )


def test_csv_extractor_normalizes_transactions_exactly() -> None:
    transactions = CsvTransactionExtractor().extract(_document(), _content())

    assert len(transactions) == 4
    assert transactions[0].amount_cents == -4900
    assert transactions[2].amount_cents == -8650
    assert transactions[3].amount_cents == 750000
    assert transactions[0].transaction_date.isoformat() == "2026-07-02"


def test_csv_extractor_rejects_missing_required_columns() -> None:
    with pytest.raises(TransactionExtractionError, match="missing required columns"):
        CsvTransactionExtractor().extract(_document(), b"date,description\n2026-08-01,Coffee\n")


def test_financial_tools_use_exact_integer_calculations(tmp_path: Path) -> None:
    repository = TransactionRepository(tmp_path / "financial.db")
    repository.replace_for_document(
        "doc-1", CsvTransactionExtractor().extract(_document(), _content())
    )
    tools = FinancialAnalyticsService(repository)

    summary = tools.spending_summary("2026-08", "ron")
    categories = tools.category_breakdown("2026-08", "RON")
    merchant = tools.merchant_total("acme telecom", "RON")
    comparison = tools.compare_months("2026-07", "2026-08", "RON")
    recurring = tools.recurring_payments("RON")

    assert summary.expense_cents == 13_550
    assert summary.income_cents == 750_000
    assert summary.transaction_count == 3
    assert [(item.category, item.amount_cents) for item in categories] == [
        ("restaurants", 8650),
        ("utilities", 4900),
    ]
    assert merchant.amount_cents == 9800
    assert merchant.transaction_count == 2
    assert comparison.expense_delta_cents == 8650
    assert recurring[0].counterparty == "Acme Telecom"
    assert recurring[0].months == ["2026-07", "2026-08"]
