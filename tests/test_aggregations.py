from datetime import date
from decimal import Decimal

from app.aggregations import (
    month_key,
    sum_by_category,
    sum_by_category_and_month,
    sum_by_month,
)
from app.models import Expense


def expense(amount, category="Lebensmittel", day="2024-06-01", expense_id=1):
    return Expense(
        id=expense_id,
        description="x",
        amount=Decimal(amount),
        category=category,
        date=date.fromisoformat(day),
    )


def test_month_key_is_year_and_zero_padded_month():
    assert month_key(expense("1", day="2024-06-30")) == "2024-06"
    assert month_key(expense("1", day="2024-12-01")) == "2024-12"


def test_all_aggregations_return_empty_dict_for_no_expenses():
    assert sum_by_category([]) == {}
    assert sum_by_month([]) == {}
    assert sum_by_category_and_month([]) == {}


def test_sum_by_category_adds_amounts():
    expenses = [
        expense("10.50", "Miete"),
        expense("4.50", "Miete"),
        expense("3", "Transport"),
    ]
    assert sum_by_category(expenses) == {
        "Miete": Decimal("15.00"),
        "Transport": Decimal("3.00"),
    }


def test_sum_by_category_is_sorted_alphabetically():
    expenses = [
        expense("1", "Transport"),
        expense("1", "Freizeit"),
        expense("1", "Miete"),
    ]
    assert list(sum_by_category(expenses)) == ["Freizeit", "Miete", "Transport"]


def test_sum_by_month_adds_amounts_per_month():
    expenses = [
        expense("10", day="2024-06-01"),
        expense("5", day="2024-06-30"),
        expense("2", day="2024-05-31"),
    ]
    assert sum_by_month(expenses) == {"2024-06": Decimal(15), "2024-05": Decimal(2)}


def test_sum_by_month_is_sorted_newest_first():
    expenses = [
        expense("1", day="2023-12-01"),
        expense("1", day="2024-02-01"),
        expense("1", day="2024-01-01"),
    ]
    assert list(sum_by_month(expenses)) == ["2024-02", "2024-01", "2023-12"]


def test_sum_by_category_and_month_groups_by_both():
    expenses = [
        expense("10", "Miete", "2024-06-01"),
        expense("5", "Miete", "2024-06-15"),
        expense("7", "Miete", "2024-05-01"),
        expense("3", "Transport", "2024-06-10"),
    ]
    assert sum_by_category_and_month(expenses) == {
        ("Miete", "2024-06"): Decimal(15),
        ("Transport", "2024-06"): Decimal(3),
        ("Miete", "2024-05"): Decimal(7),
    }


def test_sum_by_category_and_month_sorts_month_desc_then_category_asc():
    expenses = [
        expense("1", "Transport", "2024-05-01"),
        expense("1", "Miete", "2024-05-01"),
        expense("1", "Transport", "2024-06-01"),
        expense("1", "Miete", "2024-06-01"),
    ]
    assert list(sum_by_category_and_month(expenses)) == [
        ("Miete", "2024-06"),
        ("Transport", "2024-06"),
        ("Miete", "2024-05"),
        ("Transport", "2024-05"),
    ]


def test_sums_use_decimal_and_avoid_float_errors():
    expenses = [expense("0.10"), expense("0.20")]
    assert sum_by_category(expenses)["Lebensmittel"] == Decimal("0.30")
    assert sum_by_month(expenses)["2024-06"] == Decimal("0.30")


def test_aggregations_accept_any_iterable():
    generator = (expense("2") for _ in range(3))
    assert sum_by_category(generator) == {"Lebensmittel": Decimal("6.00")}
