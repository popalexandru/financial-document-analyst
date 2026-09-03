"""Exact financial analytics over structured transaction records."""

from collections import defaultdict

from financial_document_analyst.domain.transactions import (
    CategoryTotal,
    MerchantTotal,
    MonthlyComparison,
    RecurringPayment,
    SpendingSummary,
    TransactionInput,
)
from financial_document_analyst.persistence.transactions import TransactionRepository


class FinancialAnalyticsService:
    """Provide deterministic calculations for questions with numerical answers."""

    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    def spending_summary(self, month: str, currency: str) -> SpendingSummary:
        """Calculate exact outgoing and incoming totals for one month."""

        transactions = self._repository.list_transactions(month=month, currency=currency)
        return SpendingSummary(
            month=month,
            currency=currency.upper(),
            expense_cents=-sum(
                transaction.amount_cents
                for transaction in transactions
                if transaction.amount_cents < 0
            ),
            income_cents=sum(
                transaction.amount_cents
                for transaction in transactions
                if transaction.amount_cents > 0
            ),
            transaction_count=len(transactions),
        )

    def category_breakdown(self, month: str, currency: str) -> list[CategoryTotal]:
        """Group exact outgoing amounts by normalized category."""

        totals: defaultdict[str, int] = defaultdict(int)
        for transaction in self._repository.list_transactions(month=month, currency=currency):
            if transaction.amount_cents < 0:
                totals[transaction.category] -= transaction.amount_cents
        return [
            CategoryTotal(category=category, amount_cents=amount, currency=currency.upper())
            for category, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ]

    def merchant_total(self, merchant: str, currency: str) -> MerchantTotal:
        """Calculate exact outgoing payments to a case-insensitive counterparty match."""

        matches = [
            transaction
            for transaction in self._repository.list_transactions(currency=currency)
            if transaction.counterparty.casefold() == merchant.casefold()
            and transaction.amount_cents < 0
        ]
        return MerchantTotal(
            merchant=merchant,
            amount_cents=-sum(transaction.amount_cents for transaction in matches),
            currency=currency.upper(),
            transaction_count=len(matches),
        )

    def compare_months(
        self, first_month: str, second_month: str, currency: str
    ) -> MonthlyComparison:
        """Compare exact expense totals between two calendar months."""

        first = self.spending_summary(first_month, currency)
        second = self.spending_summary(second_month, currency)
        return MonthlyComparison(
            first_month=first,
            second_month=second,
            expense_delta_cents=second.expense_cents - first.expense_cents,
        )

    def recurring_payments(self, currency: str, min_occurrences: int = 2) -> list[RecurringPayment]:
        """Find repeated outgoing payments to the same counterparty across months."""

        grouped: defaultdict[tuple[str, str], list[TransactionInput]] = defaultdict(list)
        for transaction in self._repository.list_transactions(currency=currency):
            if transaction.amount_cents < 0:
                grouped[(transaction.counterparty, transaction.currency)].append(transaction)

        recurring: list[RecurringPayment] = []
        for (counterparty, transaction_currency), transactions in grouped.items():
            months = sorted(
                {transaction.transaction_date.isoformat()[:7] for transaction in transactions}
            )
            if len(transactions) >= min_occurrences and len(months) >= 2:
                recurring.append(
                    RecurringPayment(
                        counterparty=counterparty,
                        currency=transaction_currency,
                        occurrence_count=len(transactions),
                        total_cents=-sum(transaction.amount_cents for transaction in transactions),
                        months=months,
                    )
                )
        return sorted(recurring, key=lambda payment: payment.total_cents, reverse=True)
