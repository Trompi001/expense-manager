# Multi-Stage-Build: Die Builder-Stufe installiert die Abhaengigkeiten, das
# Runtime-Image enthaelt weder pip-Cache noch Build-Werkzeuge. Ergebnis: ein
# kleineres Image mit weniger Angriffsflaeche.

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS builder
# Zuerst nur requirements.txt kopieren: Solange sie sich nicht aendert, bleibt
# dieser Layer im Cache, auch wenn sich der Anwendungscode aendert.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM base AS runtime
# Container laufen nie als root: Ein ausgebrochener Prozess waere sonst root im
# Container, und der Kernel wird mit dem Host geteilt.
RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser wsgi.py ./

USER appuser
EXPOSE 8000

ARG APP_VERSION=0.0.0-dev
ENV APP_VERSION=${APP_VERSION}

# Standard: ein Worker. Der In-Memory-Speicher (ohne DATABASE_URL) gehoert jedem
# Worker einzeln, ein zweiter Worker zeigte eine andere Ausgabenliste. Mit
# Postgres ist der Zustand geteilt, docker-compose.yml setzt darum 2 Worker.
ENV GUNICORN_WORKERS=1

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

# sh -c, damit ${GUNICORN_WORKERS} expandiert; exec, damit Gunicorn PID 1 wird
# und SIGTERM direkt erhaelt (sauberes Beenden bei `docker stop`).
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --access-logfile - wsgi:app"]
