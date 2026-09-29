# Expense Manager

Eine Web-App zur Ausgabenverwaltung, mit der Nutzerinnen und Nutzer ihre Ausgaben erfassen und nach Kategorie und Monat auswerten können.

## Funktionen

- **Ausgaben erfassen:** Jede Ausgabe besteht aus Betrag, Kategorie und Datum und kann bearbeitet oder gelöscht werden.
- **Aggregationen (fachlicher Kern):** Summen je Kategorie, je Monat sowie je Kategorie und Monat kombiniert.
- **Budget-Warnungen (optional):** Pro Kategorie kann ein monatliches Budget hinterlegt werden. Wird es überschritten, zeigt die App eine Warnung an.

## Voraussetzungen

- Python ≥ 3.12
- Git
- Docker ≥ 24
- uv

## Installation

```
git clone git@github.com:<Tromppi001>/expense-manager.git
cd expense-manager
uv sync
```

`uv sync` legt die virtuelle Umgebung `.venv` an und installiert alle Abhängigkeiten exakt in den Versionen aus `uv.lock`. Ein manuelles Aktivieren der Umgebung ist nicht nötig, da alle Befehle über `uv run` ausgeführt werden.

## Nutzung
 
Lokal starten:
 
```
uv run flask --app src.app run
```
 
Der Befehl startet den Entwicklungsserver. Die App ist danach unter <http://localhost:5000> erreichbar. Beim ersten Start wird automatisch eine leere SQLite-Datenbank (`instance/expenses.db`) angelegt.
 
Alternativ im Container:
 
```
docker build -t expense-manager .
docker run -p 5000:5000 expense-manager
```
 
Tests ausführen:
 
```
uv run pytest
```
 
Die Tests laufen zusätzlich bei jedem Push und Pull Request automatisch über GitHub Actions (siehe `.github/workflows/ci.yml`).

## Projektstruktur
 
```
expense-manager/
├── README.md
├── .gitignore
├── LICENSE
├── pyproject.toml         Projektmetadaten und Abhängigkeiten
├── uv.lock                Gesperrte Versionen aller Abhängigkeiten
├── Dockerfile             Container-Image der App
├── .github/
│   └── workflows/
│       └── ci.yml         CI-Pipeline (Tests, Linting)
├── src/                   Quellcode der Anwendung
│   ├── app.py             Einstiegspunkt (Flask-App)
│   ├── models.py          Datenmodell (Ausgabe, Kategorie, Budget)
│   ├── reports.py         Aggregationen und Budget-Prüfung
│   └── templates/         HTML-Vorlagen
└── tests/                 Automatisierte Tests (pytest)
```

## Lizenz

Veröffentlicht unter der MIT-Lizenz (Datei `LICENSE` im Projekt-Repository).
