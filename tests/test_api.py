import pytest

VALID = {
    "description": "Breakfast",
    "amount": 5.0,
    "category": "Lebensmittel",
    "date": "2024-06-01",
}


def make_expense(client, **overrides):
    return client.post("/api/expense", json={**VALID, **overrides})


def test_unknown_route_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404


# --- List ------------------------------------------------------------------


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


# --- Create ----------------------------------------------------------------


def test_create_expense_returns_201_and_body(client):
    response = make_expense(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["description"] == "Breakfast"
    assert body["amount"] == "5.00"
    assert body["category"] == "Lebensmittel"
    assert body["date"] == "2024-06-01"
    assert isinstance(body["id"], int)


def test_create_assigns_incrementing_ids(client):
    first = make_expense(client).get_json()["id"]
    second = make_expense(client).get_json()["id"]
    assert second == first + 1


def test_create_trims_description(client):
    body = make_expense(client, description="  Lunch  ").get_json()
    assert body["description"] == "Lunch"


@pytest.mark.parametrize(
    ("amount", "expected"),
    [(5, "5.00"), (5.5, "5.50"), ("12.34", "12.34"), (0.01, "0.01")],
)
def test_create_formats_amount_with_two_decimals(client, amount, expected):
    response = make_expense(client, amount=amount)
    assert response.status_code == 201
    assert response.get_json()["amount"] == expected


def test_create_accepts_description_with_max_length(client):
    assert make_expense(client, description="a" * 200).status_code == 201


def test_create_with_empty_body_returns_400(client):
    response = client.post("/api/expense", json={})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Beschreibung fehlt"}


def test_create_without_json_returns_400(client):
    response = client.post("/api/expense", data="not json")
    assert response.status_code == 400


@pytest.mark.parametrize(
    ("description", "message"),
    [
        (None, "Beschreibung fehlt"),
        ("", "Beschreibung fehlt"),
        ("   ", "Beschreibung fehlt"),
        (123, "Beschreibung fehlt"),
        ("a" * 201, "Beschreibung ist laenger als 200 Zeichen"),
    ],
)
def test_create_rejects_invalid_description(client, description, message):
    response = make_expense(client, description=description)
    assert response.status_code == 400
    assert response.get_json() == {"error": message}


@pytest.mark.parametrize(
    ("amount", "message"),
    [
        (None, "Betrag fehlt"),
        (True, "Betrag fehlt"),
        ("abc", "Betrag ist keine Zahl"),
        (0, "Betrag muss groesser als 0 sein"),
        (-5, "Betrag muss groesser als 0 sein"),
        ("NaN", "Betrag muss groesser als 0 sein"),
        ("Infinity", "Betrag muss groesser als 0 sein"),
        (1.234, "Betrag darf hoechstens zwei Nachkommastellen haben"),
    ],
)
def test_create_rejects_invalid_amount(client, amount, message):
    response = make_expense(client, amount=amount)
    assert response.status_code == 400
    assert response.get_json() == {"error": message}


def test_create_rejects_missing_amount(client):
    payload = {k: v for k, v in VALID.items() if k != "amount"}
    response = client.post("/api/expense", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Betrag fehlt"}


@pytest.mark.parametrize("category", [None, "", "Food", "lebensmittel", 5])
def test_create_rejects_invalid_category(client, category):
    response = make_expense(client, category=category)
    assert response.status_code == 400
    assert response.get_json() == {"error": "Unbekannte Kategorie"}


@pytest.mark.parametrize(
    ("date", "message"),
    [
        (None, "Datum fehlt"),
        (20240601, "Datum fehlt"),
        ("01.06.2024", "Datum muss im Format JJJJ-MM-TT sein"),
        ("2024-13-01", "Datum muss im Format JJJJ-MM-TT sein"),
        ("2024-02-30", "Datum muss im Format JJJJ-MM-TT sein"),
        ("", "Datum muss im Format JJJJ-MM-TT sein"),
    ],
)
def test_create_rejects_invalid_date(client, date, message):
    response = make_expense(client, date=date)
    assert response.status_code == 400
    assert response.get_json() == {"error": message}


def test_invalid_create_does_not_store_anything(client):
    make_expense(client, amount=-1)
    assert client.get("/api/expense").get_json() == []


# --- Get by id -------------------------------------------------------------


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


# --- HTTP methods ----------------------------------------------------------


def test_delete_on_collection_is_not_allowed(client):
    assert client.delete("/api/expense").status_code == 405


def test_post_on_single_expense_is_not_allowed(client):
    assert client.post("/api/expense/1", json=VALID).status_code == 405
