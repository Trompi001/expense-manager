# Shortcuts for the Kubernetes lab. Run all targets from this directory
# (code/k8s/). Order for a first run:
#
#   make cluster   ->  make load   ->  make deploy  ->  make status
#   make forward   (in a second shell:  curl localhost:8080/health)
#   make scale     ->  make update ->  make rollback
#   make clean
.DEFAULT_GOAL := help

CLUSTER   := expense-manager
NAMESPACE := expense-manager
APP_DIR   := ..
IMAGE     := expense-manager:local
IMAGE_V2  := expense-manager:v2

.PHONY: help cluster load deploy status forward scale update rollback clean

help: ## Zeigt diese Hilfe an
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

cluster: ## kind-Cluster mit 1 Control-Plane und 2 Workern erzeugen
	kind create cluster --config kind-config.yaml
	kubectl cluster-info --context kind-$(CLUSTER)

load: ## Image expense-manager:local bauen und ins Cluster laden
	docker build -t $(IMAGE) --build-arg APP_VERSION=1.0.0 $(APP_DIR)
	kind load docker-image $(IMAGE) --name $(CLUSTER)

deploy: ## Namespace, ConfigMap, Deployment und Service anwenden
	kubectl apply -f namespace.yaml
	kubectl apply -f configmap.yaml
	kubectl apply -f deployment.yaml
	kubectl apply -f service.yaml
	kubectl -n $(NAMESPACE) rollout status deployment/expense-manager

status: ## Pods (mit Knoten), Deployment und Service anzeigen
	kubectl -n $(NAMESPACE) get pods -o wide
	kubectl -n $(NAMESPACE) get deployment,service

forward: ## Service lokal unter http://localhost:8080 verfügbar machen
	kubectl -n $(NAMESPACE) port-forward service/expense-manager 8080:80

scale: ## Auf 3 Replikate skalieren
	kubectl -n $(NAMESPACE) scale deployment/expense-manager --replicas=3
	kubectl -n $(NAMESPACE) rollout status deployment/expense-manager

update: ## Rolling Update auf expense-manager:v2 (baut, lädt, setzt Image)
	docker build -t $(IMAGE_V2) --build-arg APP_VERSION=2.0.0 $(APP_DIR)
	kind load docker-image $(IMAGE_V2) --name $(CLUSTER)
	kubectl -n $(NAMESPACE) set image deployment/expense-manager expense-manager=$(IMAGE_V2)
	kubectl -n $(NAMESPACE) rollout status deployment/expense-manager

rollback: ## Letztes Rollout rückgängig machen
	kubectl -n $(NAMESPACE) rollout undo deployment/expense-manager
	kubectl -n $(NAMESPACE) rollout status deployment/expense-manager

clean: ## kind-Cluster löschen
	kind delete cluster --name $(CLUSTER)
