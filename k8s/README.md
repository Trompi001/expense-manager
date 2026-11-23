# Kubernetes (lokal mit kind)

Manifeste für den Expense Manager, abgeleitet aus Woche 08 (cds-devops).
Alle Befehle aus diesem Verzeichnis (`k8s/`) ausführen.

| Datei | Zweck |
|---|---|
| `kind-config.yaml` | Cluster: 1 Control-Plane, 2 Worker, Port 30080 nach aussen |
| `namespace.yaml` | Namespace `expense-manager` |
| `configmap.yaml` | `APP_VERSION`, `LOG_LEVEL` |
| `secret.example.yaml` | Beispiel für `DATABASE_URL` (echte Werte nie committen) |
| `deployment.yaml` | Probes (`/health`, `/ready`), resources, securityContext, Rolling Update (`maxSurge: 1`, `maxUnavailable: 0`) |
| `service.yaml` | ClusterIP, Port 80 -> 8000 |
| `service-nodeport.yaml` | NodePort 30080 (`http://localhost:30080`) |
| `hpa.yaml` | Autoscaler 2-5 Replikate bei 70 % CPU (braucht metrics-server) |

## Ablauf

```bash
make cluster    # kind-Cluster erzeugen
make load       # Image bauen und in den Cluster laden (sonst ErrImagePull)
make deploy     # Namespace, ConfigMap, Deployment, Service
make scale      # auf 3 Replikate
kubectl apply -f service-nodeport.yaml
make update     # Rolling Update auf expense-manager:v2
make rollback
make clean
```

## Hinweise

- Ohne `DATABASE_URL` nutzt die App den In-Memory-Speicher; jedes Replikat hat
  dann eigene Daten. Für den Mehr-Replikat-Betrieb in Produktion ist eine
  gemeinsame Postgres-Datenbank nötig (Secret im Deployment einkommentieren, sobald
  eine Datenbank im Cluster läuft; sonst schlägt `/ready` fehl).
- `readOnlyRootFilesystem: true` braucht das `emptyDir` auf `/tmp`, sonst startet
  Gunicorn nicht (CrashLoopBackOff, Ursache sichtbar mit `kubectl logs --previous`).
