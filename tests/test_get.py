from helpers import make_expense


def test_get_expense_returns_created_expense(client):
    created = make_expense(client).get_json()
    response = client.get(f"/api/expense/{created['id']}")
    assert response.status_code == 200
    assert response.get_json() == created


def test_get_unknown_expense_returns_404(client):
    response = client.get("/api/expense/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Ausgabe nicht gefunden"}


def test_get_expense_with_non_integer_id_returns_404(client):
    assert client.get("/api/expense/abc").status_code == 404
