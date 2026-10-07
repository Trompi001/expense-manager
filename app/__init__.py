"""Expense Manager – Application Factory (Platzhalter-Version).

Laeuft ohne config.py, repository.py und routes.py, damit das Frontend
lokal angezeigt werden kann. Die Platzhalter sind mit TODO markiert und
werden spaeter durch die echten Module ersetzt.

Start: `python wsgi.py`, dann http://127.0.0.1:8000
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from flask import Blueprint, Flask, render_template


# TODO: durch app/config.py ersetzen (Config.from_env()).
@dataclass
class Config:
    version: str = "0.1-dev"
    log_level: str = "DEBUG"
    categories: list[str] = field(
        default_factory=lambda: [
            "Lebensmittel",
            "Miete",
            "Transport",
            "Freizeit",
            "Sonstiges",
        ]
    )


# TODO: durch app/repository.py ersetzen (ExpenseRepository, create_repository()).
class InMemoryExpenseRepository:
    """Haelt Ausgaben nur im Speicher; nach Neustart ist alles weg."""

    def __init__(self) -> None:
        self._expenses: list[dict[str, Any]] = []

    def list(self) -> list[dict[str, Any]]:
        return list(self._expenses)

    def add(self, expense: dict[str, Any]) -> None:
        self._expenses.append(expense)


# TODO: durch app/routes.py ersetzen.
bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    config: Config = bp_config()
    return render_template(
        "index.html",
        version=config.version,
        categories=config.categories,
    )


def bp_config() -> Config:
    from flask import current_app

    return current_app.extensions["app_config"]


def create_app(
    config: Config | None = None,
    repository: Any | None = None,
    registry: Any | None = None,
) -> Flask:
    """Application factory. Signatur bleibt kompatibel zur spaeteren Version."""
    config = config or Config()

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.extensions["app_config"] = config
    app.extensions["repository"] = repository or InMemoryExpenseRepository()

    # Prometheus nur aktivieren, wenn die Pakete installiert sind.
    try:
        from prometheus_flask_exporter import PrometheusMetrics

        metrics = PrometheusMetrics(app, registry=registry)
        metrics.info("expense_manager_info", "Application info", version=config.version)
    except ImportError:
        logging.getLogger(__name__).info("Prometheus nicht installiert, Metriken deaktiviert.")

    app.register_blueprint(bp)
    return app