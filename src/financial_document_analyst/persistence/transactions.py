"""SQLite repository for normalized transactions."""

import sqlite3
from pathlib import Path

from financial_document_analyst.domain.transactions import TransactionInput


class TransactionRepository:
    """Persist transactions with exact integer amounts in a portable SQLite database."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._initialize()

    def replace_for_document(self, document_id: str, transactions: list[TransactionInput]) -> None:
        """Atomically replace a document's transactions after a repeat ingestion."""

        with self._connect() as connection:
            connection.execute("DELETE FROM transactions WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO transactions (
                    document_id, transaction_date, description, counterparty,
                    amount_cents, currency, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        transaction.document_id,
                        transaction.transaction_date.isoformat(),
                        transaction.description,
                        transaction.counterparty,
                        transaction.amount_cents,
                        transaction.currency,
                        transaction.category,
                    )
                    for transaction in transactions
                ],
            )

    def list_transactions(
        self, *, month: str | None = None, currency: str | None = None
    ) -> list[TransactionInput]:
        """Read normalized transactions, optionally restricted by month and currency."""

        conditions: list[str] = []
        parameters: list[str] = []
        if month:
            conditions.append("substr(transaction_date, 1, 7) = ?")
            parameters.append(month)
        if currency:
            conditions.append("currency = ?")
            parameters.append(currency.upper())
        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        query = (
            "SELECT document_id, transaction_date, description, counterparty, amount_cents, "
            f"currency, category FROM transactions{where_clause} ORDER BY transaction_date"
        )
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            TransactionInput(
                document_id=row["document_id"],
                transaction_date=row["transaction_date"],
                description=row["description"],
                counterparty=row["counterparty"],
                amount_cents=row["amount_cents"],
                currency=row["currency"],
                category=row["category"],
            )
            for row in rows
        ]

    def _initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    counterparty TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    category TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_document ON transactions(document_id)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection
