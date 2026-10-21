"""Gemeinsame Hilfsmittel fuer die API-Tests."""

VALID = {
    "description": "Breakfast",
    "amount": 5.0,
    "category": "Lebensmittel",
    "date": "2024-06-01",
}


def make_expense(client, **overrides):
    """Legt eine Ausgabe an. Nicht angegebene Felder kommen aus VALID."""
    return client.post("/api/expense", json={**VALID, **overrides})


def descriptions(client, query=""):
    """Beschreibungen der Liste, z. B. descriptions(client, "?month=2024-06")."""
    return [e["description"] for e in client.get(f"/api/expense{query}").get_json()]
