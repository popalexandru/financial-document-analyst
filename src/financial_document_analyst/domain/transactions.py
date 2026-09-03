"""Structured financial transaction and analytics models."""

from datetime import date

from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    """A normalized transaction ready for exact persistence and calculation."""

    document_id: str
    transaction_date: date
    description: str = Field(min_length=1)
    counterparty: str = Field(min_length=1)
    amount_cents: int
    currency: str = Field(min_length=3, max_length=3)
    category: str = Field(min_length=1)


class CategoryTotal(BaseModel):
    """One deterministic expense subtotal by category."""

    category: str
    amount_cents: int = Field(ge=0)
    currency: str


class SpendingSummary(BaseModel):
    """Exact expense and income totals for a calendar month."""

    month: str
    currency: str
    expense_cents: int = Field(ge=0)
    income_cents: int = Field(ge=0)
    transaction_count: int = Field(ge=0)


class MerchantTotal(BaseModel):
    """Exact total paid to one counterparty."""

    merchant: str
    amount_cents: int = Field(ge=0)
    currency: str
    transaction_count: int = Field(ge=0)


class MonthlyComparison(BaseModel):
    """Deterministic comparison of spending between two months."""

    first_month: SpendingSummary
    second_month: SpendingSummary
    expense_delta_cents: int


class RecurringPayment(BaseModel):
    """A repeated outgoing payment candidate derived from transaction records."""

    counterparty: str
    currency: str
    occurrence_count: int = Field(ge=2)
    total_cents: int = Field(ge=0)
    months: list[str] = Field(min_length=2)
