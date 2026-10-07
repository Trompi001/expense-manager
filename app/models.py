"""Domaenenmodell und Validierung fuer Ausgaben."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

MAX_DESCRIPTION_LENGTH = 200


class ValidationError(ValueError):
    """Ungueltige Eingabe. Die Route macht daraus eine 400-Antwort."""


@dataclass
class Expense:
    id: int
    description: str
    amount: Decimal  # Decimal statt float: keine Rundungsfehler bei Geld
    category: str
    date: date

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "amount": f"{self.amount:.2f}",  # als String, damit nichts gerundet wird
            "category": self.category,
            "date": self.date.isoformat(),
        }


def validate_description(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Beschreibung fehlt")
    value = value.strip()
    if len(value) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(f"Beschreibung ist laenger als {MAX_DESCRIPTION_LENGTH} Zeichen")
    return value


def validate_amount(value: object) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError("Betrag fehlt")
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValidationError("Betrag ist keine Zahl") from None
    if not amount.is_finite() or amount <= 0:
        raise ValidationError("Betrag muss groesser als 0 sein")
    if amount.as_tuple().exponent < -2:
        raise ValidationError("Betrag darf hoechstens zwei Nachkommastellen haben")
    return amount.quantize(Decimal("0.01"))


def validate_category(value: object, allowed: list[str]) -> str:
    if value not in allowed:
        raise ValidationError("Unbekannte Kategorie")
    return value


def validate_date(value: object) -> date:
    if not isinstance(value, str):
        raise ValidationError("Datum fehlt")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError("Datum muss im Format JJJJ-MM-TT sein") from None