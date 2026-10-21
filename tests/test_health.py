def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_reports_version(client):
    assert client.get("/health").get_json()["version"] == "test"


def test_ready_reports_ready_with_in_memory_repository(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_ready_returns_503_when_repository_is_unhealthy(app, client):
    class BrokenRepository:
        def healthy(self):
            return False

    app.extensions["repository"] = BrokenRepository()
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json()["status"] == "unavailable"


def test_metrics_endpoint_is_exposed(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"expense_manager_info" in response.data


def test_index_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Expense" in response.data
