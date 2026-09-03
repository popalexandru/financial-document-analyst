"""Deterministic financial analytics endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from financial_document_analyst.core.config import Settings, get_settings
from financial_document_analyst.domain.transactions import (
    CategoryTotal,
    MerchantTotal,
    MonthlyComparison,
    RecurringPayment,
    SpendingSummary,
)
from financial_document_analyst.persistence.transactions import TransactionRepository
from financial_document_analyst.tools.financial import FinancialAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> FinancialAnalyticsService:
    """Create deterministic tools backed by the configured SQLite database."""

    return FinancialAnalyticsService(TransactionRepository(settings.database_path))


@router.get("/summary", response_model=SpendingSummary)
def spending_summary(
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    service: Annotated[FinancialAnalyticsService, Depends(get_analytics_service)],
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "RON",
) -> SpendingSummary:
    """Return exact monthly expense and income totals in integer cents."""

    return service.spending_summary(month, currency)


@router.get("/categories", response_model=list[CategoryTotal])
def category_breakdown(
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    service: Annotated[FinancialAnalyticsService, Depends(get_analytics_service)],
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "RON",
) -> list[CategoryTotal]:
    """Return exact monthly expense totals grouped by category."""

    return service.category_breakdown(month, currency)


@router.get("/merchants/{merchant}", response_model=MerchantTotal)
def merchant_total(
    merchant: str,
    service: Annotated[FinancialAnalyticsService, Depends(get_analytics_service)],
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "RON",
) -> MerchantTotal:
    """Return exact total outgoing payments for one merchant."""

    return service.merchant_total(merchant, currency)


@router.get("/comparison", response_model=MonthlyComparison)
def compare_months(
    first_month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    second_month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")],
    service: Annotated[FinancialAnalyticsService, Depends(get_analytics_service)],
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "RON",
) -> MonthlyComparison:
    """Return the deterministic change in expenses between two months."""

    return service.compare_months(first_month, second_month, currency)


@router.get("/recurring", response_model=list[RecurringPayment])
def recurring_payments(
    service: Annotated[FinancialAnalyticsService, Depends(get_analytics_service)],
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "RON",
    min_occurrences: Annotated[int, Query(ge=2, le=12)] = 2,
) -> list[RecurringPayment]:
    """Return repeated outgoing payment candidates across at least two months."""

    return service.recurring_payments(currency, min_occurrences=min_occurrences)
