from helpers import VALID


def test_unknown_route_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404


def test_delete_on_collection_is_not_allowed(client):
    assert client.delete("/api/expense").status_code == 405


def test_post_on_single_expense_is_not_allowed(client):
    assert client.post("/api/expense/1", json=VALID).status_code == 405
