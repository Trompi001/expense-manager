# Analyse: Warum gab es beim Rolling Update keinen Ausfall?

Skalierung: imperativ mit `kubectl scale deployment/expense-manager --replicas=3`.
Nachweise: `protokoll-scale.txt`, `protokoll-rollout.txt`, `protokoll-rollback.txt`.

## readinessProbe und maxUnavailable

Die `readinessProbe` auf `/ready` entscheidet, ob ein Pod Verkehr bekommt. Ein neuer
Pod gilt erst als bereit, wenn `/ready` mit 200 antwortet; bis dahin steht er nicht in
den Endpoints des Service. Ohne Probe zählt Kubernetes einen Pod als verfügbar, sobald
der Container gestartet ist. Der Service würde schon Anfragen an Gunicorn schicken,
bevor es sie annimmt, und diese Anfragen scheiterten.

`maxUnavailable: 0` heisst: Es müssen immer alle 3 Replikate verfügbar sein. Zusammen
mit `maxSurge: 1` startet Kubernetes zuerst einen neuen Pod und beendet erst danach einen
alten, wenn der neue Ready ist. Ohne Readiness-Probe wäre das wirkungslos, denn
„verfügbar“ würde falsch gemessen und alte Pods würden zu früh entfernt.

## Zwei Endpunkte: /health und /ready

`/health` (Liveness) prüft nur den Prozess, ohne Datenbank. Scheitert sie, startet
Kubernetes den Container neu. `/ready` prüft zusätzlich die Datenbank. Scheitert sie,
wird der Pod nur aus dem Service genommen, ohne Neustart. Würde die Liveness-Probe die
Datenbank prüfen, würde eine kurze Störung der Datenbank alle App-Pods neu starten.
Daraus entstünde eine Restart-Schleife und ein Totalausfall, den erst die Überwachung
verursacht hat.

## Lernbefund: Fehler ohne preStop-Hook

Im ersten Lauf (`protokoll-rollout-ohne-prestop.txt`) gab es drei Fehlversuche
(`[000]`, um 15:57:15 und zweimal um 15:57:20), obwohl Readiness-Probe und
`maxUnavailable: 0` gesetzt waren. Meine Erklärung (Vermutung, nicht bewiesen): Beim
Beenden eines alten Pods erhält Gunicorn `SIGTERM` und schliesst sofort den Port. Der
Service nimmt den Pod aber erst etwas später aus den Endpoints, daher gingen in diesem
Fenster noch Anfragen an den sterbenden Pod.

Fix: ein `preStop`-Hook (`sleep 5`) in `deployment.yaml`. Der Pod wird dadurch erst nach
einer kurzen Wartezeit beendet und ist bis dahin schon aus der Rotation. Der zweite Lauf
(`protokoll-rollout.txt`) enthält 74 Anfragen, alle mit `[200]`.

## Rollback

`kubectl rollout undo` stellte die vorige Revision (`expense-manager:local`) als neue
Revision 5 wieder her; die alte Revision 3 verschwand dabei aus der Liste
(siehe `protokoll-rollback.txt`).
