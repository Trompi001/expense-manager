from helpers import descriptions, make_expense


def test_delete_returns_204_without_body(client):
    created = make_expense(client).get_json()
    response = client.delete(f"/api/expense/{created['id']}")
    assert response.status_code == 204
    assert response.data == b""


def test_deleted_expense_is_gone(client):
    created = make_expense(client).get_json()
    client.delete(f"/api/expense/{created['id']}")
    assert client.get("/api/expense").get_json() == []
    assert client.get(f"/api/expense/{created['id']}").status_code == 404


def test_delete_only_removes_the_given_expense(client):
    first = make_expense(client, description="first").get_json()
    make_expense(client, description="second")
    client.delete(f"/api/expense/{first['id']}")
    assert descriptions(client) == ["second"]


def test_delete_unknown_expense_returns_404(client):
    response = client.delete("/api/expense/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Ausgabe nicht gefunden"}


def test_delete_twice_returns_404_the_second_time(client):
    created = make_expense(client).get_json()
    assert client.delete(f"/api/expense/{created['id']}").status_code == 204
    assert client.delete(f"/api/expense/{created['id']}").status_code == 404


def test_ids_are_not_reused_after_delete(client):
    first = make_expense(client).get_json()
    client.delete(f"/api/expense/{first['id']}")
    second = make_expense(client).get_json()
    assert second["id"] != first["id"]


def test_delete_with_non_integer_id_returns_404(client):
    assert client.delete("/api/expense/abc").status_code == 404
