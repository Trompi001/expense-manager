.DEFAULT_GOAL := help
IMAGE ?= taskboard
TAG   ?= local

.PHONY: help install run test lint fmt cov build up down clean

help: ## Zeigt diese Hilfe an
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Installiert alle Abhängigkeiten inkl. Dev-Tools
	pip install -r requirements-dev.txt

run: ## Startet den Entwicklungsserver auf Port 8000
	flask --app wsgi run --debug --port 8000

test: ## Führt die Testsuite aus
	pytest

cov: ## Testsuite mit Abdeckungsbericht
	pytest --cov=app --cov-report=term-missing

lint: ## Prüft Stil und Importsortierung
	ruff check .
	ruff format --check .

fmt: ## Formatiert den Code
	ruff check --fix .
	ruff format .

build: ## Baut das Container-Image
	docker build --build-arg APP_VERSION=$(TAG) -t $(IMAGE):$(TAG) .

up: ## Startet Anwendung + Datenbank via Docker Compose
	docker compose up --build

down: ## Stoppt Docker Compose
	docker compose down

clean: ## Entfernt Caches und Testartefakte
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -name __pycache__ -type d -exec rm -rf {} +
