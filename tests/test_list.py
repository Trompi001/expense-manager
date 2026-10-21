import pytest
from helpers import descriptions, make_expense


def test_list_is_empty_initially(client):
    response = client.get("/api/expense")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_returns_created_expenses(client):
    make_expense(client)
    body = client.get("/api/expense").get_json()
    assert len(body) == 1
    assert body[0]["description"] == "Breakfast"


def test_list_is_sorted_newest_first(client):
    make_expense(client, description="old", date="2024-01-01")
    make_expense(client, description="new", date="2024-03-01")
    make_expense(client, description="mid", date="2024-02-01")
    descriptions = [e["description"] for e in client.get("/api/expense").get_json()]
    assert descriptions == ["new", "mid", "old"]


def test_list_same_date_newest_id_first(client):
    make_expense(client, description="first")
    make_expense(client, description="second")
    descriptions = [e["description"] for e in client.get("/api/expense").get_json()]
    assert descriptions == ["second", "first"]


def test_list_filters_by_category(client):
    make_expense(client, description="food", category="Lebensmittel")
    make_expense(client, description="rent", category="Miete")
    body = client.get("/api/expense?category=Miete").get_json()
    assert [e["description"] for e in body] == ["rent"]


def test_list_filter_without_matches_returns_empty_list(client):
    make_expense(client, category="Lebensmittel")
    response = client.get("/api/expense?category=Transport")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_filter_with_unknown_category_returns_400(client):
    response = client.get("/api/expense?category=Unbekannt")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Unbekannte Kategorie"}


def test_list_filters_by_month(client):
    make_expense(client, description="june", date="2024-06-30")
    make_expense(client, description="may", date="2024-05-31")
    assert descriptions(client, "?month=2024-06") == ["june"]
    assert descriptions(client, "?month=2024-05") == ["may"]


def test_list_month_filter_includes_first_and_last_day(client):
    make_expense(client, description="first", date="2024-06-01")
    make_expense(client, description="last", date="2024-06-30")
    make_expense(client, description="next", date="2024-07-01")
    assert descriptions(client, "?month=2024-06") == ["last", "first"]


def test_list_month_filter_distinguishes_years(client):
    make_expense(client, description="2023", date="2023-06-15")
    make_expense(client, description="2024", date="2024-06-15")
    assert descriptions(client, "?month=2024-06") == ["2024"]


def test_list_month_filter_without_matches_returns_empty_list(client):
    make_expense(client, date="2024-06-01")
    response = client.get("/api/expense?month=2024-07")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_month_and_category_filter_can_be_combined(client):
    make_expense(client, description="rent-june", category="Miete", date="2024-06-01")
    make_expense(
        client, description="food-june", category="Lebensmittel", date="2024-06-02"
    )
    make_expense(client, description="rent-may", category="Miete", date="2024-05-01")
    assert descriptions(client, "?month=2024-06&category=Miete") == ["rent-june"]


@pytest.mark.parametrize(
    "month", ["2024-6", "2024-13", "2024-00", "abc", "", "2024-06-01", "06-2024"]
)
def test_list_rejects_invalid_month(client, month):
    response = client.get(f"/api/expense?month={month}")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Monat muss im Format JJJJ-MM sein"}
