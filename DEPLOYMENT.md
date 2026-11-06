# Deployment-Runbook – Expense Manager

Der Expense Manager ist eine Flask-Web-App zur Ausgabenverwaltung (Erfassen, Auswerten nach Kategorie und Monat). Dieses Dokument führt Schritt für Schritt vom leeren Konto zur laufenden, verifizierten Instanz auf **Render (Free Tier)**. Es braucht kein Vorwissen über das Projekt.

Live-Instanz: `<APP_URL>` (z. B. `https://expense-manager-xxxx.onrender.com`)

Inhalt: [A Voraussetzungen](#a-voraussetzungen) · [B Lokale Installation](#b-lokale-installation) · [C Konfigurationsvariablen](#c-konfigurationsvariablen) · [D Deployment](#d-deployment-schritte-render) · [E Verifikation](#e-verifikation-nach-dem-deploy) · [F Rollback](#f-rollback) · [G Troubleshooting](#g-troubleshooting) · [H Kontakt](#h-kontakt-und-eskalation)

## A. Voraussetzungen

**Konten**

- GitHub-Konto mit Zugriff auf das Repository `Trompi001/expense-manager` (zum Deployen: Leserechte; zum Ändern von Secrets und Variablen: Admin-Rechte).
- Render-Konto (<https://render.com>, kostenlos, Anmeldung mit GitHub).

**Lokale Werkzeuge** (jeweils mit Prüfbefehl)

```bash
git --version       # erwartet: git version 2.x
python3 --version   # erwartet: Python 3.12.x oder neuer
curl --version      # erwartet: curl 7.x oder 8.x
make --version      # optional, erwartet: GNU Make 3.x oder 4.x
```

Docker ist nur nötig, wenn Sie das Image lokal bauen wollen (`docker --version`, Docker Compose v2).

**Rechte**

- Repository: wer pushen darf, entscheidet der Repository-Besitzer. `main` ist geschützt, Änderungen laufen über Pull Requests.
- Render-Service: verwaltet der Service-Owner (siehe Abschnitt H).

## B. Lokale Installation

```bash
git clone https://github.com/Trompi001/expense-manager.git
cd expense-manager
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
make run                         # startet http://127.0.0.1:8000
```

Ohne `make`: `flask --app wsgi run --debug --port 8000`.

Prüfen, in einem zweiten Terminal:

```bash
curl http://127.0.0.1:8000/health
# erwartet (Einrückung kann abweichen): {"status":"ok","version":"0.0.0-dev"}
```

Ohne `DATABASE_URL` liegen die Ausgaben nur im Arbeitsspeicher und sind nach einem Neustart weg. Tests und Lint lokal: `make test`, `make cov`, `make lint`.

## C. Konfigurationsvariablen

**Variablen der Anwendung** (Render: *Environment*, lokal: Umgebung bzw. `.env`)

| Variable | Standard | Geheim | Wirkung |
|---|---|---|---|
| `DATABASE_URL` | *(leer)* | **ja** | Leer: In-Memory-Speicher. Gesetzt (z. B. `postgresql://user:pw@host:5432/db`): Postgres, die Tabelle `expenses` wird beim Start angelegt. |
| `APP_VERSION` | `0.0.0-dev` | nein | Erscheint in `/health`, `/metrics` und auf der Startseite. Bei jedem Release erhöhen. |
| `LOG_LEVEL` | `INFO` | nein | Log-Schwelle: `DEBUG`, `INFO`, `WARNING`, `ERROR`. **Ein ungültiger Wert lässt die App beim Start abstürzen.** |
| `PORT` | `10000` (von Render vorgegeben) | nein | Port, an den Render den Verkehr leitet. Der Container lauscht fest auf `8000`, deshalb auf `8000` setzen. |
| `GUNICORN_WORKERS` | `1` | nein | Anzahl Worker. Ohne `DATABASE_URL` bei `1` lassen (siehe G). |
| `POSTGRES_PASSWORD` | `changeme` | **ja** | Nur für `docker compose` (lokal), nicht für Render. |

**Werte für die CD-Pipeline** (GitHub: *Settings → Secrets and variables → Actions*)

| Name | Typ | Geheim | Wirkung |
|---|---|---|---|
| `RENDER_DEPLOY_HOOK` | **Secret** | **ja** | URL des Render Deploy Hooks. Wer sie kennt, kann Deploys auslösen. |
| `APP_URL` | **Variable** (Reiter *Variables*) | nein | Öffentliche URL der Instanz, ohne Schrägstrich am Ende. |

**Umgang mit Geheimnissen:** Geheime Werte gehören nur in Render (*Environment*), in GitHub-Secrets oder in die lokale `.env`, nie ins Repository, nie in dieses Dokument und nie in ein Log. Die Datei `.env` steht in `.gitignore`. Ist ein Geheimnis doch irgendwo gelandet, neu erzeugen (der alte Wert wird dabei ungültig).

## D. Deployment-Schritte (Render)

**Hauptpfad: Dashboard.** Ein Blueprint (`render.yaml`) beschreibt dieselbe Konfiguration deklarativ, wird hier aber nicht parallel betrieben (derselbe Service nie gleichzeitig per Dashboard und Blueprint).

### D1. Einmalige Einrichtung

1. **Konto anlegen:** auf <https://render.com> mit GitHub anmelden, E-Mail bestätigen.
2. **Repository verbinden:** *New +* → *Web Service* → *Build and deploy from a Git repository* → GitHub-App von Render installieren und das Repository `expense-manager` freigeben → Repository auswählen → *Connect*.
3. **Service konfigurieren:**

   | Feld | Wert |
   |---|---|
   | Name | `expense-manager` |
   | Language / Runtime | `Docker` |
   | Branch | `main` |
   | Region | `Frankfurt` |
   | Root Directory | **leer lassen** (das `Dockerfile` liegt im Repository-Wurzelverzeichnis) |
   | Instance Type | `Free` |
   | Health Check Path (*Advanced*) | `/health` |
   | Docker Command | **leer lassen** (das Image startet Gunicorn selbst) |

4. **Umgebungsvariablen setzen** (*Environment Variables*, jeder Wert zum passenden Namen):

   | Key | Value |
   |---|---|
   | `PORT` | `8000` |
   | `LOG_LEVEL` | `INFO` |
   | `GUNICORN_WORKERS` | `1` |
   | `APP_VERSION` | `1.0.0` |

   `DATABASE_URL` **nicht** setzen (In-Memory-Betrieb). Die Werte sorgfältig den richtigen Namen zuordnen, siehe Fehlerbild 5 in G.
5. **Deployen:** *Deploy Web Service*. Render baut das Image und startet den Dienst.
6. **Auf „live" warten** (Reiter *Logs*). Erwartet am Ende sinngemäss:

   ```
   [INFO] Starting gunicorn 22.0.0
   [INFO] Listening at: http://0.0.0.0:8000
   [INFO] Booting worker with pid: ...
   ==> Your service is live
   ```

   Genau **eine** „Booting worker"-Zeile bestätigt den Einzel-Worker-Betrieb.

### D2. Wiederkehrender Deploy über die Pipeline

Nach der Einrichtung deployt die GitHub-Actions-Pipeline (`.github/workflows/cd.yml`). Einmalig vorbereiten:

1. **Deploy Hook holen:** Render-Service → *Settings* → *Deploy Hook* → URL kopieren.
2. **Auto-Deploy abschalten:** Render-Service → *Settings* → *Auto-Deploy* auf *No* (sonst deployt Render zusätzlich bei jedem Push).
3. **GitHub:** *Settings → Secrets and variables → Actions*
   - Reiter *Secrets*: `RENDER_DEPLOY_HOOK` = kopierte URL.
   - Reiter *Variables*: `APP_URL` = `https://<APP_URL>`.

Danach läuft der Ablauf so: Pull Request → CI grün (Lint, Tests, Image-Build) → Merge auf `main` → Workflow *CD* löst den Deploy aus, wartet 90 Sekunden und führt den Smoke-Test aus. Manuell starten: GitHub → *Actions* → *CD* → *Run workflow*.

## E. Verifikation nach dem Deploy

1. **Health-Check:**

   ```bash
   curl https://<APP_URL>/health
   # erwartet: {"status":"ok","version":"1.0.0"}
   ```

   Die Version muss dem gesetzten `APP_VERSION` entsprechen. Der erste Aufruf nach längerer Ruhe kann 30 bis 60 Sekunden dauern (Cold Start, siehe G).

2. **Smoke-Test** (prüft `/health`, `/ready` sowie Anlegen, Lesen und Löschen einer Ausgabe):

   ```bash
   ./scripts/smoke-test.sh https://<APP_URL>
   # erwartet am Ende:  SMOKE TEST PASSED
   ```

   Falls die Datei nicht ausführbar ist: `chmod +x scripts/smoke-test.sh`.

3. **Log prüfen** (Render → *Logs*): Der Health Check auf `/health` ist erfolgreich, sobald Render „Your service is live" meldet. Es erscheint genau eine „Booting worker"-Zeile.

4. **Pipeline:** Der Lauf *CD* in GitHub ist grün. Im Schritt *Trigger Render deploy* steht eine Deploy-ID (`{"deploy":{"id":"dep-..."}}`), im Schritt *Smoke-test the running service* endet die Ausgabe mit `SMOKE TEST PASSED`. In Render zeigt *Events* einen Deploy, der über den Deploy Hook ausgelöst wurde.

## F. Rollback

Ziel: zur letzten funktionierenden Version zurückkehren, wenn ein Deploy fehlschlägt oder die App sich falsch verhält.

**Weg 1: früheren Deploy erneut ausrollen (schnellster Weg)**

1. Render-Service → *Events* (bzw. *Deploys*).
2. Den letzten funktionierenden Deploy (Commit und Zeitpunkt vergleichen) öffnen und *Rollback* bzw. *Redeploy* wählen. Falls diese Schaltfläche fehlt: *Manual Deploy* → *Deploy a specific commit* und den Commit des letzten guten Stands angeben.
3. Beachten: Ein Rollback über das Dashboard kann *Auto-Deploy* für den Service ausschalten. In diesem Projekt ist es ohnehin aus, der Deploy läuft über die Pipeline.

**Weg 2: Änderung per Git zurücknehmen (nachvollziehbar, Roll-forward)**

```bash
git switch main && git pull
git switch -c fix/revert-bad-change
git revert <commit-der-fehlerhaften-aenderung>
git push -u origin fix/revert-bad-change
```

Pull Request öffnen, CI abwarten, mergen. Die Pipeline deployt den Revert automatisch.

**Rollback verifizieren**

```bash
curl https://<APP_URL>/health
# erwartet: {"status":"ok","version":"<Version des letzten guten Stands>"}
./scripts/smoke-test.sh https://<APP_URL>   # erwartet: SMOKE TEST PASSED
```

Die angezeigte Version ist nur dann aussagekräftig, wenn `APP_VERSION` bei Releases tatsächlich erhöht wurde. Sonst im Render-Reiter *Events* prüfen, welcher Commit aktiv ist.

**Grenzen**

- Ein Rollback tauscht nur den Code. Zustand und Datenbank rollen **nicht** zurück.
- Im jetzigen Betrieb (In-Memory, ohne `DATABASE_URL`) sind die Daten bei jedem Neustart und jedem Deploy ohnehin weg. Ein Rollback „verliert" dadurch nichts zusätzlich.
- Sobald Postgres angeschlossen ist, gilt: Schemaänderungen nur abwärtskompatibel und additiv durchführen, sonst versteht die alte Version das neue Schema nicht mehr und nur ein Roll-forward hilft.
- Auch Variablenänderungen rollen nicht mit zurück. Fehlerhafte Werte in *Environment* korrigieren.

## G. Troubleshooting

| # | Symptom | Ursache | Lösung |
|---|---|---|---|
| 1 | Deploy baut, geht aber nie live. Log: „No open ports detected" oder Health Check schlägt fehl. | Render leitet den Verkehr an `PORT` (Standard `10000`), der Container lauscht auf `8000`. | `PORT=8000` unter *Environment* setzen und neu deployen. |
| 2 | Deploy bleibt in einer „Deploying/unhealthy"-Schleife. | Health Check Path steht auf `/ready`. Ohne Datenbank bzw. bei langsamer DB liefert `/ready` `503`. | Health Check Path auf `/health` stellen (Liveness, ohne DB). |
| 3 | Erster Aufruf nach einigen Minuten dauert 30–60 Sekunden oder läuft in ein Timeout. Die App wirkt „down". | Cold Start: Die Free-Instanz schläft nach 15 Minuten ohne Zugriff und fährt beim nächsten Request hoch. | Kein Ausfall. Erneut aufrufen. Der Smoke-Test wartet mit Backoff darauf. Ohne Spin-down hilft nur ein bezahlter Tarif. |
| 4 | `/health` ist grün, aber der Smoke-Test schlägt beim Anlegen, Lesen oder Löschen mit `404` fehl. Ausgaben „verschwinden". | Ohne `DATABASE_URL` hält jeder Gunicorn-Worker einen eigenen Speicher. Bei mehr als einem Worker landen Anfragen auf verschiedenen Speichern. | `GUNICORN_WORKERS=1` setzen oder eine Datenbank (`DATABASE_URL`) anschliessen. |
| 5 | Deploy endet mit `Exited with status 3`. Log: `Worker failed to boot` und `ValueError: Unknown level: '8000'`. | Ein Variablenwert steht beim falschen Namen (z. B. `8000` bei `LOG_LEVEL`). Ein ungültiger `LOG_LEVEL` bricht den Start ab. | Unter *Environment* prüfen: `PORT=8000`, `LOG_LEVEL=INFO` (genau so, ohne Leerzeichen). Speichern, Render startet neu. |
| 6 | CD-Lauf ist rot mit `APP_URL variable is not set`, obwohl ein Wert eingetragen ist. Der Deploy selbst wurde ausgelöst. | `APP_URL` wurde als **Secret** statt als **Variable** angelegt. Der Workflow liest `vars.APP_URL`. | In GitHub unter *Variables* als Repository-Variable anlegen, das Secret löschen, Workflow neu starten. |
| 7 | Deploy Hook-URL taucht in einem Log oder Chat auf. | `echo` oder `curl -v` mit der URL, oder versehentlich kopiert. | Hook in Render neu erzeugen (der alte wird ungültig), Secret in GitHub aktualisieren. URLs nie ausgeben. |

## H. Kontakt und Eskalation

Platzhalter für die Abgabe, bei echtem Betrieb ausfüllen:

- **Service-Owner:** `<Name/Team>` (zuständig für Render-Service, Deploy Hook und Secrets)
- **Vertretung:** `<Name/Team>`
- **Kommunikationsweg:** `<z. B. Chat-Kanal #expense-manager, E-Mail an <Adresse>>`
- **Eskalation:**
  1. Fehler bei einem Deploy: zuerst Abschnitte E bis G durcharbeiten (Rollback nach F, wenn die Instanz nicht erreichbar ist).
  2. Nach 30 Minuten ohne Lösung: Service-Owner informieren.
  3. Nach 60 Minuten Ausfall der Produktivinstanz oder bei Verdacht auf ein kompromittiertes Geheimnis: Eskalation an `<Vorgesetzte/r bzw. Projektleitung>`. Bei einem Geheimnis sofort rotieren (siehe Fehlerbild 7).
