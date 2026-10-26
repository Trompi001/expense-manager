# Expense Manager

Eine Web-App zur Ausgabenverwaltung, mit der Nutzerinnen und Nutzer ihre Ausgaben erfassen und nach Kategorie und Monat auswerten können.

## Funktionen

- **Ausgaben erfassen:** Jede Ausgabe besteht aus Beschreibung, Betrag, Kategorie und Datum und kann bearbeitet oder gelöscht werden. Die Liste lässt sich nach Kategorie und Monat filtern.
- **Aggregationen (fachlicher Kern):** Summen je Kategorie, je Monat sowie je Kategorie und Monat kombiniert, als Balkenansicht im Tab «Auswertung».
- **Budget-Warnungen (optional, geplant):** Pro Kategorie kann ein monatliches Budget hinterlegt werden. Wird es überschritten, zeigt die App eine Warnung an.

Beträge werden intern als `Decimal` gerechnet und in CHF mit zwei Nachkommastellen ausgegeben.

## Voraussetzungen

- Python ≥ 3.9
- Git
- `make` (optional, für die Kurzbefehle im `Makefile`)

## Installation

```
git clone git@github.com:<benutzername>/expense-manager.git
cd expense-manager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Statt des letzten Befehls geht auch `make install`. Für den reinen Betrieb ohne Test- und Lint-Werkzeuge genügt `pip install -r requirements.txt`.

## Nutzung

Entwicklungsserver starten:

```
make run
```

oder ohne `make`:

```
flask --app wsgi run --debug --port 8000
```

Die App ist danach unter <http://127.0.0.1:8000> erreichbar. Ohne `DATABASE_URL` liegen die Ausgaben nur im Arbeitsspeicher und sind nach einem Neustart weg. Mit `DATABASE_URL` (siehe Konfiguration) werden sie in Postgres gespeichert.

Weitere Befehle (`make help` zeigt alle):

| Befehl | Wirkung |
|---|---|
| `make test` | führt die Testsuite aus (`pytest`) |
| `make cov` | Testsuite mit Abdeckungsbericht |
| `make lint` | prüft Stil und Formatierung mit ruff |
| `make fmt` | formatiert den Code mit ruff |
| `make clean` | entfernt Caches und Testartefakte |

## Konfiguration

Die Konfiguration kommt aus Umgebungsvariablen (siehe `app/config.py`):

| Variable | Standard | Bedeutung |
|---|---|---|
| `APP_VERSION` | `0.0.0-dev` | Version, die `/health` und die Startseite anzeigen |
| `LOG_LEVEL` | `INFO` | Log-Stufe (`DEBUG`, `INFO`, `WARNING`, …) |
| `DATABASE_URL` | – | leer: In-Memory-Speicher. Gesetzt (z. B. `postgresql://user:pw@host:5432/db`): Postgres, die Tabelle `expenses` wird beim Start angelegt |

Die Kategorien sind in `app/config.py` hinterlegt: Lebensmittel, Miete, Transport, Freizeit, Sonstiges.

## API

| Methode und Pfad | Beschreibung |
|---|---|
| `GET /api/expense` | Liste, neueste zuerst. Optionale Filter: `?category=Miete`, `?month=2026-10` (kombinierbar) |
| `POST /api/expense` | neue Ausgabe (`description`, `amount`, `category`, `date`), Antwort 201 |
| `GET /api/expense/<id>` | einzelne Ausgabe, 404 wenn unbekannt |
| `PUT /api/expense/<id>` | ersetzt alle Felder einer Ausgabe |
| `DELETE /api/expense/<id>` | löscht eine Ausgabe, Antwort 204 |
| `GET /api/summary?group_by=…` | Summen, `group_by` ist `category`, `month` oder `category_month` |
| `GET /health` | Liveness: der Prozess läuft |
| `GET /ready` | Readiness: die Speicherschicht ist bereit (sonst 503) |
| `GET /metrics` | Prometheus-Metriken |

Ungültige Eingaben werden mit 400 und `{"error": "…"}` beantwortet.

Beispiel:

```
curl -X POST http://127.0.0.1:8000/api/expense \
  -H "Content-Type: application/json" \
  -d '{"description": "Wocheneinkauf", "amount": 84.35, "category": "Lebensmittel", "date": "2026-10-18"}'

curl "http://127.0.0.1:8000/api/summary?group_by=category"
```

## Tests

Mit aktivierter virtueller Umgebung, im Projektordner:

```
pytest
```

`make test` führt denselben Befehl aus. Mit Abdeckungsbericht: `make cov` (entspricht `pytest --cov=app --cov-report=term-missing`).

Die Tests liegen in `tests/`, eine Datei pro Thema (Liste, Erstellen, Ändern, Löschen, Auswertung, Health, …). Die Fixtures `app` und `client` in `tests/conftest.py` geben jedem Test einen frischen Speicher.

## Projektstruktur

```
expense-manager/
├── README.md
├── LICENSE
├── Makefile                Kurzbefehle (run, test, lint, …)
├── pytest.ini              pytest-Konfiguration
├── requirements.txt        Laufzeit-Abhängigkeiten
├── requirements-dev.txt    zusätzlich Test- und Lint-Werkzeuge
├── wsgi.py                 Einstiegspunkt (z. B. für gunicorn)
├── app/
│   ├── __init__.py         create_app(): Application Factory
│   ├── aggregations.py     Summen je Kategorie und Monat (reine Funktionen)
│   ├── config.py           Konfiguration aus der Umgebung
│   ├── models.py           Ausgabe und Validierung
│   ├── repository.py       Speicherschicht (In-Memory und Postgres)
│   ├── routes.py           HTTP-Routen (API und Startseite)
│   ├── static/             CSS
│   └── templates/          HTML-Vorlage
└── tests/                  automatisierte Tests (pytest)
```

## Mitarbeit und Branching

Es gilt **GitHub Flow**: `main` ist immer lauffähig und geschützt, jede Änderung läuft über einen kurzlebigen Branch (`feature/…`, `fix/…`, `chore/…`, `docs/…`) und einen Pull Request mit grüner CI. Die Details, die Commit-Konventionen und die Selbstprüfung stehen in [CONTRIBUTING.md](CONTRIBUTING.md).

## Lizenz

Veröffentlicht unter der MIT-Lizenz (Datei `LICENSE` im Projekt-Repository).
