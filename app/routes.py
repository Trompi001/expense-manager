from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request

from app.models import (
    ValidationError,
    validate_amount,
    validate_category,
    validate_date,
    validate_description,
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

    Optionaler Filter: /api/expense?category=Lebensmittel
    """
    category = request.args.get("category")
    if category is not None:
        category = validate_category(category, _config().categories)
    return jsonify([e.to_dict() for e in _repo().list(category=category)])


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