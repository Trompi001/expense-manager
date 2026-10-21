"""Expense Manager – Application Factory.

Konfiguration kommt aus app/config.py (Config.from_env()).
Start: `python wsgi.py`, dann http://127.0.0.1:8000
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask

from app.config import Config
from app.repository import ExpenseRepository, create_repository


def create_app(
    config: Config | None = None,
    repository: ExpenseRepository | None = None,
    registry: Any | None = None,
) -> Flask:
    """Application factory. Alle Argumente koennen fuer Tests injiziert werden."""
    config = config or Config.from_env()

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