"""Expense Manager – Application Factory.

Config ist noch ein Platzhalter (TODO: durch app/config.py mit Config.from_env() ersetzen).
Start: `python wsgi.py`, dann http://127.0.0.1:8000
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from flask import Flask

from app.repository import ExpenseRepository, create_repository


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


def create_app(
    config: Config | None = None,
    repository: ExpenseRepository | None = None,
    registry: Any | None = None,
) -> Flask:
    """Application factory. Alle Argumente koennen fuer Tests injiziert werden."""
    config = config or Config()

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.extensions["app_config"] = config
    app.extensions["repository"] = repository or create_repository(config)

    # Prometheus nur aktivieren, wenn die Pakete installiert sind.
    try:
        from prometheus_flask_exporter import PrometheusMetrics

        metrics = PrometheusMetrics(app, registry=registry)
        metrics.info("expense_manager_info", "Application info", version=config.version)
    except ImportError:
        logging.getLogger(__name__).info("Prometheus nicht installiert, Metriken deaktiviert.")

    from app.routes import bp

    app.register_blueprint(bp)
    return app