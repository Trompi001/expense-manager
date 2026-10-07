"""Speicherschicht. Aufbau wie im Beispielprojekt: Protocol + In-Memory-Backend.

TODO: Postgres-Backend ergaenzen, sobald eine Datenbank dazukommt.
"""

from __future__ import annotations

import threading
from datetime import date
from decimal import Decimal
from typing import Protocol

from app.models import Expense


class ExpenseRepository(Protocol):
    """Speicher-Vertrag. Die Routen kennen nur diese Methoden."""

    def list(self, category: str | None = None) -> list[Expense]: ...
    def get(self, expense_id: int) -> Expense | None: ...
    def add(self, description: str, amount: Decimal, category: str, date: date) -> Expense: ...
    def healthy(self) -> bool: ...


class InMemoryExpenseRepository:
    """Haelt Ausgaben nur im Speicher; nach einem Neustart ist alles weg."""

    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def list(self, category: str | None = None) -> list[Expense]:
        """Ausgaben nach Datum sortiert (neueste zuerst), optional nach Kategorie gefiltert."""
        with self._lock:
            expenses = [
                e for e in self._expenses.values() if category is None or e.category == category
            ]
        return sorted(expenses, key=lambda e: (e.date, e.id), reverse=True)

    def get(self, expense_id: int) -> Expense | None:
        with self._lock:
            return self._expenses.get(expense_id)

    def add(self, description: str, amount: Decimal, category: str, date: date) -> Expense:
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

    def healthy(self) -> bool:
        return True


def create_repository(config) -> ExpenseRepository:
    return InMemoryExpenseRepository()