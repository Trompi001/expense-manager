"""Aggregationen ueber Ausgaben (fachlicher Kern).

Alle Funktionen sind reine Funktionen: Sie bekommen eine Liste von Ausgaben
und liefern die Summen zurueck. Es gibt weder HTTP noch Datenbank, daher lassen
sie sich einfach testen. Gerechnet wird mit Decimal, nicht mit float.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from app.models import Expense

ZERO = Decimal("0.00")


def month_key(expense: Expense) -> str:
    """Monat einer Ausgabe als "JJJJ-MM", z. B. "2024-06"."""
    return expense.date.strftime("%Y-%m")


def sum_by_category(expenses: Iterable[Expense]) -> dict[str, Decimal]:
    """Summe je Kategorie, alphabetisch nach Kategorie sortiert."""
    totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for e in expenses:
        totals[e.category] += e.amount
    return dict(sorted(totals.items()))


def sum_by_month(expenses: Iterable[Expense]) -> dict[str, Decimal]:
    """Summe je Monat ("JJJJ-MM"), neuester Monat zuerst."""
    totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for e in expenses:
        totals[month_key(e)] += e.amount
    return dict(sorted(totals.items(), reverse=True))


def sum_by_category_and_month(
    expenses: Iterable[Expense],
) -> dict[tuple[str, str], Decimal]:
    """Summe je (Kategorie, Monat), neuester Monat zuerst, dann nach Kategorie."""
    totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    for e in expenses:
        totals[(e.category, month_key(e))] += e.amount
    # Monat absteigend, Kategorie aufsteigend
    ordered = sorted(totals.items(), key=lambda item: item[0][0])
    ordered.sort(key=lambda item: item[0][1], reverse=True)
    return dict(ordered)
