# Mitarbeit im Projekt

Diese Regeln gelten für dieses Repository. Das Projekt ist eine Einzelarbeit,
die Regeln gelten trotzdem: Sie halten die Historie nachvollziehbar und `main`
jederzeit lauffähig.

## Branching-Strategie: GitHub Flow

`main` ist **immer deploybar**. Direkt auf `main` wird nie gepusht, `main` ist
durch eine Branch Protection Rule geschützt ("Require a pull request before
merging").

1. Für jede Aufgabe einen kurzlebigen Branch von `main` abzweigen.
2. Committen, pushen, einen Pull Request öffnen.
3. Die eigene Änderung im PR selbst prüfen (Checkliste unten).
4. Die CI muss grün sein (Lint, Tests, Coverage-Gate).
5. Mergen und den Branch löschen.

```
git switch main && git pull
git switch -c feature/kurzbeschreibung
# arbeiten, committen
git push -u origin feature/kurzbeschreibung
# Pull Request auf GitHub öffnen
```

### Branch-Namen

Muster `<typ>/<kurzbeschreibung>`, Englisch, Kleinbuchstaben, Bindestriche.

| Typ | Zweck | Beispiel |
|---|---|---|
| `feature/` | neue Funktion | `feature/postgres-repository` |
| `fix/` | Fehlerbehebung | `fix/month-filter` |
| `chore/` | Wartung, Werkzeuge | `chore/repo-hygiene` |
| `docs/` | Dokumentation | `docs/contributing` |
| `build/` | Build und Packaging | `build/pyproject` |

## Commit-Konventionen

Englisch, Imperativ, ohne Punkt am Ende, ein Thema pro Commit. Empfohlen sind
Conventional Commits:

```
<typ>(<bereich>): <kurze Aussage>
```

Typen: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`.

```
feat(repository): add Postgres backend
build: add pyproject.toml with coverage gate
docs: add CONTRIBUTING guide
```

## Selbstprüfung im Pull Request

Statt eines Reviews prüfe ich jede Änderung selbst und halte das in der
PR-Beschreibung fest (siehe `.github/PULL_REQUEST_TEMPLATE.md`):

- Was wurde geändert und warum?
- `make lint` und `make cov` laufen lokal durch.
- Die CI ist grün.
- Dokumentation (README) ist angepasst, falls nötig.
