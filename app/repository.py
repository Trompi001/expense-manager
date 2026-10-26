"""Speicherschicht: Protocol mit zwei Backends.

- InMemoryExpenseRepository: Standard ohne DATABASE_URL (Tests, lokale Entwicklung)
- PostgresExpenseRepository: aktiv, sobald DATABASE_URL gesetzt ist
"""

from __future__ import annotations

import logging
import threading
from datetime import date
from decimal import Decimal
from typing import Protocol

from app.models import Expense

log = logging.getLogger(__name__)


class ExpenseRepository(Protocol):
    """Speicher-Vertrag. Die Routen kennen nur diese Methoden."""

    def list(
        self, category: str | None = None, month: str | None = None
    ) -> list[Expense]: ...
    def get(self, expense_id: int) -> Expense | None: ...
    def add(
        self, description: str, amount: Decimal, category: str, date: date
    ) -> Expense: ...
    def update(
        self,
        expense_id: int,
        description: str,
        amount: Decimal,
        category: str,
        date: date,
    ) -> Expense | None: ...
    def delete(self, expense_id: int) -> bool: ...
    def healthy(self) -> bool: ...


class InMemoryExpenseRepository:
    """Haelt Ausgaben nur im Speicher; nach einem Neustart ist alles weg."""

    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def list(
        self, category: str | None = None, month: str | None = None
    ) -> list[Expense]:
        """Ausgaben nach Datum sortiert (neueste zuerst).

        Optional nach Kategorie und/oder Monat ("JJJJ-MM") gefiltert.
        """
        with self._lock:
            expenses = [
                e
                for e in self._expenses.values()
                if (category is None or e.category == category)
                and (month is None or e.date.strftime("%Y-%m") == month)
            ]
        return sorted(expenses, key=lambda e: (e.date, e.id), reverse=True)

    def get(self, expense_id: int) -> Expense | None:
        with self._lock:
            return self._expenses.get(expense_id)

    def add(
        self, description: str, amount: Decimal, category: str, date: date
    ) -> Expense:
        with self._lock:
            expense = Expense(
                id=self._next_id,
                description=description,
                amount=amount,
                category=category,
                date=date,
            )
            self._expenses[expense.id] = expense
            self._next_id += 1
            return expense

    def update(
        self,
        expense_id: int,
        description: str,
        amount: Decimal,
        category: str,
        date: date,
    ) -> Expense | None:
        """Ersetzt alle Felder einer Ausgabe. Gibt None zurueck, wenn die ID unbekannt ist."""
        with self._lock:
            if expense_id not in self._expenses:
                return None
            expense = Expense(
                id=expense_id,
                description=description,
                amount=amount,
                category=category,
                date=date,
            )
            self._expenses[expense_id] = expense
            return expense

    def delete(self, expense_id: int) -> bool:
        """Loescht eine Ausgabe. Gibt False zurueck, wenn die ID unbekannt ist."""
        with self._lock:
            return self._expenses.pop(expense_id, None) is not None

    def healthy(self) -> bool:
        return True


class PostgresExpenseRepository:
    """Postgres-Backend. Geteilter Zustand, daher mehrere Gunicorn-Worker moeglich.

    `pool` kann fuer Tests injiziert werden; sonst wird ein ConnectionPool
    zum angegebenen DSN geoeffnet.
    """

    _COLUMNS = "id, description, amount, category, date"

    def __init__(self, dsn: str, pool=None) -> None:
        if pool is None:
            from psycopg_pool import ConnectionPool

            pool = ConnectionPool(dsn, min_size=1, max_size=5, open=True)
        self._pool = pool
        self._create_schema()

    def _create_schema(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id          SERIAL PRIMARY KEY,
                    description TEXT NOT NULL,
                    amount      NUMERIC(12, 2) NOT NULL,
                    category    TEXT NOT NULL,
                    date        DATE NOT NULL
                )
                """
            )

    def list(
        self, category: str | None = None, month: str | None = None
    ) -> list[Expense]:
        conditions: list[str] = []
        params: list[str] = []
        if category is not None:
            conditions.append("category = %s")
            params.append(category)
        if month is not None:
            conditions.append("to_char(date, 'YYYY-MM') = %s")
            params.append(month)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = (
            f"SELECT {self._COLUMNS} FROM expenses {where} ORDER BY date DESC, id DESC"
        )
        with self._pool.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Expense(*row) for row in rows]

    def get(self, expense_id: int) -> Expense | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT {self._COLUMNS} FROM expenses WHERE id = %s", (expense_id,)
            ).fetchone()
        return Expense(*row) if row else None

    def add(
        self, description: str, amount: Decimal, category: str, date: date
    ) -> Expense:
        with self._pool.connection() as conn:
            row = conn.execute(
                "INSERT INTO expenses (description, amount, category, date) "
                f"VALUES (%s, %s, %s, %s) RETURNING {self._COLUMNS}",
                (description, amount, category, date),
            ).fetchone()
        return Expense(*row)

    def update(
        self,
        expense_id: int,
        description: str,
        amount: Decimal,
        category: str,
        date: date,
    ) -> Expense | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                "UPDATE expenses SET description = %s, amount = %s, category = %s, "
                f"date = %s WHERE id = %s RETURNING {self._COLUMNS}",
                (description, amount, category, date, expense_id),
            ).fetchone()
        return Expense(*row) if row else None

    def delete(self, expense_id: int) -> bool:
        with self._pool.connection() as conn:
            result = conn.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        return result.rowcount > 0

    def healthy(self) -> bool:
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            log.exception("Datenbank-Healthcheck fehlgeschlagen")
            return False


def create_repository(config) -> ExpenseRepository:
    if config.database_url:
        log.info("Verwende Postgres-Repository")
        return PostgresExpenseRepository(config.database_url)
    # Der In-Memory-Speicher gehoert jedem Gunicorn-Worker einzeln. Mit mehreren
    # Workern waeren die Daten uneinheitlich; dafuer DATABASE_URL setzen.
    log.warning(
        "Keine DATABASE_URL gesetzt, verwende In-Memory-Speicher: "
        "Zustand gilt pro Prozess und geht beim Neustart verloren"
    )
    return InMemoryExpenseRepository()
