# Terraform: nginx-Webserver (Woche 7)

Startet einen `nginx:alpine`-Container, der die eigene `index.html` ausliefert.
Läuft gegen den lokalen Docker-Daemon, kein Cloud-Konto nötig.

## Voraussetzung

Docker läuft (`docker info`) und Terraform >= 1.5 ist installiert.
Findet Terraform den Docker-Socket nicht, `terraform.tfvars.example` nach
`terraform.tfvars` kopieren und `docker_host` setzen.

## Benutzung

```bash
terraform init      # Provider laden
terraform plan      # Vorschau
terraform apply     # Container anlegen (mit yes bestätigen)
curl http://localhost:8080/
terraform destroy   # aufräumen
```

Anderer Port: `terraform apply -var="host_port=9000"`. Ports <= 1024 werden abgelehnt.
