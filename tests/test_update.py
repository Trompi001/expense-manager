import pytest
from helpers import VALID, descriptions, make_expense


def test_update_replaces_all_fields(client):
    created = make_expense(client).get_json()
    response = client.put(
        f"/api/expense/{created['id']}",
        json={
            "description": "Dinner",
            "amount": 42.5,
            "category": "Freizeit",
            "date": "2024-07-15",
        },
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "id": created["id"],
        "description": "Dinner",
        "amount": "42.50",
        "category": "Freizeit",
        "date": "2024-07-15",
    }


def test_update_is_persisted(client):
    created = make_expense(client).get_json()
    client.put(
        f"/api/expense/{created['id']}", json={**VALID, "description": "Changed"}
    )
    assert (
        client.get(f"/api/expense/{created['id']}").get_json()["description"]
        == "Changed"
    )
    assert descriptions(client) == ["Changed"]


def test_update_does_not_create_a_new_expense(client):
    created = make_expense(client).get_json()
    client.put(f"/api/expense/{created['id']}", json={**VALID, "amount": 9})
    assert len(client.get("/api/expense").get_json()) == 1


def test_update_only_changes_the_given_expense(client):
    first = make_expense(client, description="first").get_json()
    make_expense(client, description="second")
    client.put(f"/api/expense/{first['id']}", json={**VALID, "description": "changed"})
    assert sorted(descriptions(client)) == ["changed", "second"]


def test_update_unknown_expense_returns_404(client):
    response = client.put("/api/expense/999", json=VALID)
    assert response.status_code == 404
    assert response.get_json() == {"error": "Ausgabe nicht gefunden"}


def test_update_unknown_expense_returns_404_even_with_invalid_body(client):
    assert client.put("/api/expense/999", json={}).status_code == 404


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("description", "", "Beschreibung fehlt"),
        ("amount", -1, "Betrag muss groesser als 0 sein"),
        ("amount", 1.234, "Betrag darf hoechstens zwei Nachkommastellen haben"),
        ("category", "Food", "Unbekannte Kategorie"),
        ("date", "2024-02-30", "Datum muss im Format JJJJ-MM-TT sein"),
    ],
)
def test_update_rejects_invalid_data_and_keeps_old_values(
    client, field, value, message
):
    created = make_expense(client).get_json()
    response = client.put(f"/api/expense/{created['id']}", json={**VALID, field: value})
    assert response.status_code == 400
    assert response.get_json() == {"error": message}
    assert client.get(f"/api/expense/{created['id']}").get_json() == created


def test_update_with_empty_body_returns_400(client):
    created = make_expense(client).get_json()
    assert client.put(f"/api/expense/{created['id']}", json={}).status_code == 400


def test_update_with_non_integer_id_returns_404(client):
    assert client.put("/api/expense/abc", json=VALID).status_code == 404
