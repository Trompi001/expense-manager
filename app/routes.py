import os
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request

from app.aggregations import (
    sum_by_category,
    sum_by_category_and_month,
    sum_by_month,
)
from app.models import (
    ValidationError,
    validate_amount,
    validate_category,
    validate_date,
    validate_description,
    validate_month,
)

bp = Blueprint("main", __name__)


def _repo():
    return current_app.extensions["repository"]


def _config():
    return current_app.extensions["app_config"]


@bp.errorhandler(ValidationError)
def _handle_validation_error(exc: ValidationError):
    return jsonify(error=str(exc)), 400


@bp.get("/")
def index():
    return render_template(
        "index.html",
        version=_config().version,
        categories=_config().categories,
    )


@bp.get("/health")
def health():
    """Liveness: laeuft der Prozess? Darf die Datenbank nicht anfassen."""
    return jsonify(status="ok", version=_config().version)


@bp.get("/ready")
def ready():
    """Readiness: kann diese Instanz Anfragen bedienen?"""
    if _repo().healthy():
        return jsonify(status="ready")
    return jsonify(status="unavailable"), 503


@bp.get("/api/expense")
def list_expenses():
    """Ausgaben nach Datum sortiert (neueste zuerst).

    Optionale Filter (auch kombinierbar):
    /api/expense?category=Lebensmittel
    /api/expense?month=2024-06
    """
    category = request.args.get("category")
    if category is not None:
        category = validate_category(category, _config().categories)
    month = request.args.get("month")
    if month is not None:
        month = validate_month(month)
    return jsonify([e.to_dict() for e in _repo().list(category=category, month=month)])


@bp.post("/api/expense")
def create_expense():
    payload = request.get_json(silent=True) or {}
    expense = _repo().add(
        description=validate_description(payload.get("description")),
        amount=validate_amount(payload.get("amount")),
        category=validate_category(payload.get("category"), _config().categories),
        date=validate_date(payload.get("date")),
    )
    return jsonify(expense.to_dict()), 201


@bp.get("/api/expense/<int:expense_id>")
def get_expense(expense_id: int):
    expense = _repo().get(expense_id)
    if expense is None:
        return jsonify(error="Ausgabe nicht gefunden"), 404
    return jsonify(expense.to_dict())


@bp.put("/api/expense/<int:expense_id>")
def update_expense(expense_id: int):
    """Ersetzt alle Felder einer Ausgabe (gleiche Validierung wie beim Erstellen)."""
    if _repo().get(expense_id) is None:
        return jsonify(error="Ausgabe nicht gefunden"), 404
    payload = request.get_json(silent=True) or {}
    expense = _repo().update(
        expense_id,
        description=validate_description(payload.get("description")),
        amount=validate_amount(payload.get("amount")),
        category=validate_category(payload.get("category"), _config().categories),
        date=validate_date(payload.get("date")),
    )
    if expense is None:
        return jsonify(error="Ausgabe nicht gefunden"), 404
    return jsonify(expense.to_dict())


@bp.delete("/api/expense/<int:expense_id>")
def delete_expense(expense_id: int):
    if not _repo().delete(expense_id):
        return jsonify(error="Ausgabe nicht gefunden"), 404
    return "", 204


GROUPINGS = ("category", "month", "category_month")


@bp.get("/api/summary")
def summary():
    """Summen der Ausgaben.

    /api/summary?group_by=category        -> Summe je Kategorie
    /api/summary?group_by=month           -> Summe je Monat (JJJJ-MM)
    /api/summary?group_by=category_month  -> Summe je Kategorie und Monat
    """
    group_by = request.args.get("group_by")
    if group_by not in GROUPINGS:
        raise ValidationError("group_by muss category, month oder category_month sein")

    expenses = _repo().list()
    if group_by == "category":
        rows = [
            {"category": category, "total": f"{total:.2f}"}
            for category, total in sum_by_category(expenses).items()
        ]
    elif group_by == "month":
        rows = [
            {"month": month, "total": f"{total:.2f}"}
            for month, total in sum_by_month(expenses).items()
        ]
    else:
        rows = [
            {"category": category, "month": month, "total": f"{total:.2f}"}
            for (category, month), total in sum_by_category_and_month(expenses).items()
        ]
    return jsonify(rows)
