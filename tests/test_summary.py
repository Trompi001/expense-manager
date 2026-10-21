import pytest


def add(client, amount, category="Lebensmittel", date="2024-06-01"):
    response = client.post(
        "/api/expense",
        json={"description": "x", "amount": amount, "category": category, "date": date},
    )
    assert response.status_code == 201


def summary(client, group_by):
    response = client.get(f"/api/summary?group_by={group_by}")
    assert response.status_code == 200
    return response.get_json()


@pytest.fixture
def filled(client):
    add(client, "10.10", "Miete", "2024-06-01")
    add(client, "0.20", "Miete", "2024-06-30")
    add(client, "5", "Transport", "2024-06-15")
    add(client, "7.50", "Transport", "2024-05-02")
    return client


def test_summary_by_category(filled):
    assert summary(filled, "category") == [
        {"category": "Miete", "total": "10.30"},
        {"category": "Transport", "total": "12.50"},
    ]


def test_summary_by_month_newest_first(filled):
    assert summary(filled, "month") == [
        {"month": "2024-06", "total": "15.30"},
        {"month": "2024-05", "total": "7.50"},
    ]


def test_summary_by_category_and_month(filled):
    assert summary(filled, "category_month") == [
        {"category": "Miete", "month": "2024-06", "total": "10.30"},
        {"category": "Transport", "month": "2024-06", "total": "5.00"},
        {"category": "Transport", "month": "2024-05", "total": "7.50"},
    ]


def test_summary_sums_are_exact_for_decimal_amounts(client):
    # 0.1 + 0.2 ergibt mit float 0.30000000000000004
    add(client, "0.10")
    add(client, "0.20")
    assert summary(client, "category") == [
        {"category": "Lebensmittel", "total": "0.30"}
    ]


def test_summary_keeps_years_apart(client):
    add(client, "1", date="2023-06-01")
    add(client, "2", date="2024-06-01")
    assert summary(client, "month") == [
        {"month": "2024-06", "total": "2.00"},
        {"month": "2023-06", "total": "1.00"},
    ]


@pytest.mark.parametrize("group_by", ["category", "month", "category_month"])
def test_summary_is_empty_without_expenses(client, group_by):
    assert summary(client, group_by) == []


def test_summary_follows_updates_and_deletes(client):
    add(client, "10")
    created = client.get("/api/expense").get_json()[0]
    client.put(
        f"/api/expense/{created['id']}",
        json={
            "description": "x",
            "amount": 25,
            "category": "Freizeit",
            "date": "2024-06-01",
        },
    )
    assert summary(client, "category") == [{"category": "Freizeit", "total": "25.00"}]
    client.delete(f"/api/expense/{created['id']}")
    assert summary(client, "category") == []


@pytest.mark.parametrize(
    "query", ["", "?group_by=", "?group_by=year", "?group_by=Category"]
)
def test_summary_rejects_missing_or_invalid_group_by(client, query):
    response = client.get(f"/api/summary{query}")
    assert response.status_code == 400
    assert response.get_json() == {
        "error": "group_by muss category, month oder category_month sein"
    }


def test_summary_only_allows_get(client):
    assert client.post("/api/summary?group_by=category").status_code == 405
