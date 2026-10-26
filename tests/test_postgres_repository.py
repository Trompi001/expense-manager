"""Tests fuer das Postgres-Backend.

Die meisten Tests laufen gegen einen Fake-Pool und pruefen SQL und Parameter.
Der Integrationstest laeuft nur, wenn TEST_DATABASE_URL auf eine echte
Postgres-Datenbank zeigt (z. B. aus docker compose).
"""

import os
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

import pytest

from app import repository
from app.config import Config
from app.models import Expense
from app.repository import (
    InMemoryExpenseRepository,
    PostgresExpenseRepository,
    create_repository,
)

ROW = (1, "Wocheneinkauf", Decimal("84.35"), "Lebensmittel", date(2026, 10, 18))


class FakeResult:
    def __init__(self, rows=None, rowcount=0):
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.results = []
        self.fail = False

    def execute(self, sql, params=None):
        if self.fail:
            raise RuntimeError("db down")
        self.calls.append((" ".join(sql.split()), params))
        return self.results.pop(0) if self.results else FakeResult()


class FakePool:
    def __init__(self):
        self.conn = FakeConnection()

    @contextmanager
    def connection(self):
        yield self.conn


@pytest.fixture
def pool():
    return FakePool()


@pytest.fixture
def repo(pool):
    return PostgresExpenseRepository("unused", pool=pool)


def test_schema_is_created_on_init(pool, repo):
    sql, _ = pool.conn.calls[0]
    assert sql.startswith("CREATE TABLE IF NOT EXISTS expenses")


def test_list_without_filters(pool, repo):
    pool.conn.results = [FakeResult([ROW])]
    expenses = repo.list()
    sql, params = pool.conn.calls[-1]
    assert "WHERE" not in sql
    assert "ORDER BY date DESC, id DESC" in sql
    assert params == []
    assert expenses == [Expense(*ROW)]


def test_list_with_category_and_month(pool, repo):
    pool.conn.results = [FakeResult([])]
    assert repo.list(category="Miete", month="2026-10") == []
    sql, params = pool.conn.calls[-1]
    assert "category = %s AND to_char(date, 'YYYY-MM') = %s" in sql
    assert params == ["Miete", "2026-10"]


def test_get_returns_expense_or_none(pool, repo):
    pool.conn.results = [FakeResult([ROW]), FakeResult([])]
    assert repo.get(1) == Expense(*ROW)
    assert repo.get(99) is None


def test_add_inserts_and_returns_expense(pool, repo):
    pool.conn.results = [FakeResult([ROW])]
    expense = repo.add("Wocheneinkauf", Decimal("84.35"), "Lebensmittel", ROW[4])
    sql, params = pool.conn.calls[-1]
    assert sql.startswith("INSERT INTO expenses")
    assert params == ("Wocheneinkauf", Decimal("84.35"), "Lebensmittel", ROW[4])
    assert expense.id == 1


def test_update_returns_expense_or_none(pool, repo):
    pool.conn.results = [FakeResult([ROW]), FakeResult([])]
    assert repo.update(1, "x", Decimal("1.00"), "Miete", ROW[4]) == Expense(*ROW)
    assert repo.update(99, "x", Decimal("1.00"), "Miete", ROW[4]) is None
    sql, params = pool.conn.calls[-1]
    assert sql.startswith("UPDATE expenses")
    assert params[-1] == 99


def test_delete_reports_whether_a_row_was_removed(pool, repo):
    pool.conn.results = [FakeResult(rowcount=1), FakeResult(rowcount=0)]
    assert repo.delete(1) is True
    assert repo.delete(99) is False


def test_healthy_is_true_when_query_succeeds(repo):
    assert repo.healthy() is True


def test_healthy_is_false_when_database_fails(pool, repo):
    pool.conn.fail = True
    assert repo.healthy() is False


def test_create_repository_uses_in_memory_without_database_url():
    config = Config(database_url=None, version="test", log_level="WARNING")
    assert isinstance(create_repository(config), InMemoryExpenseRepository)


def test_create_repository_uses_postgres_with_database_url(monkeypatch):
    created = {}

    class StubPostgres:
        def __init__(self, dsn):
            created["dsn"] = dsn

    monkeypatch.setattr(repository, "PostgresExpenseRepository", StubPostgres)
    config = Config(database_url="postgresql://x", version="test", log_level="WARNING")
    assert isinstance(create_repository(config), StubPostgres)
    assert created["dsn"] == "postgresql://x"


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL nicht gesetzt"
)
def test_roundtrip_against_real_postgres():
    repo = PostgresExpenseRepository(os.environ["TEST_DATABASE_URL"])
    with repo._pool.connection() as conn:
        conn.execute("DELETE FROM expenses")
    created = repo.add("Test", Decimal("12.50"), "Miete", date(2026, 10, 1))
    assert repo.get(created.id) == created
    assert repo.list(month="2026-10") == [created]
    updated = repo.update(
        created.id, "Neu", Decimal("20.00"), "Freizeit", date(2026, 9, 1)
    )
    assert updated.description == "Neu"
    assert repo.delete(created.id) is True
    assert repo.get(created.id) is None
    assert repo.healthy() is True
