"""Pure calculations and evaluations for Built to Last."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from built_to_last.case_data import (
    ACQUISITION_QUESTIONS,
    ANALYSIS_FACTS,
    ANALYSIS_FIELDS,
    ANALYSIS_QUESTIONS,
    DEPRECIATION_FACTS,
    DEPRECIATION_FIELDS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_FACTS,
    DISPOSAL_FIELDS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    UPKEEP_QUESTIONS,
    ChoiceQuestion,
)


QUESTION_GROUPS: tuple[tuple[ChoiceQuestion, ...], ...] = (
    ACQUISITION_QUESTIONS,
    UPKEEP_QUESTIONS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    ANALYSIS_QUESTIONS,
)


def format_currency(value: float | int) -> str:
    """Format a dollar amount for student feedback."""

    rounded = round(float(value))
    if rounded < 0:
        return f"-${abs(rounded):,.0f}"
    return f"${rounded:,.0f}"


def question_by_id(item_id: str) -> ChoiceQuestion:
    for group in QUESTION_GROUPS:
        for item in group:
            if item.id == item_id:
                return item
    raise KeyError(item_id)


def evaluate_choice(item_id: str, selected: str) -> dict[str, object]:
    item = question_by_id(item_id)
    return {
        "correct": selected == item.correct,
        "selected": selected,
        "expected": item.correct,
        "explanation": item.explanation,
        "account_effect": item.account_effect,
        "statement_effect": item.statement_effect,
    }


def acquisition_totals() -> dict[str, int]:
    """Return ending asset costs and immediate expenses from acquisition evidence."""

    return {
        "Land": 191_000,
        "Land Improvements": 36_000,
        "Building": 420_000,
        "Equipment": 94_000,
        "Current-period expense": 3_000,
        "Capitalized plant assets": 741_000,
    }


def lifecycle_totals() -> dict[str, int]:
    """Return cumulative balances after acquisition and later expenditures."""

    return {
        "Land": 191_000,
        "Land Improvements": 36_000,
        "Building": 510_000,
        "Equipment": 112_000,
        "Capitalized plant assets": 849_000,
        "Current-period expense": 10_200,
    }


def expected_depreciation_values() -> dict[str, int]:
    cost = DEPRECIATION_FACTS["cost"]
    salvage = DEPRECIATION_FACTS["salvage_value"]
    life = DEPRECIATION_FACTS["useful_life_years"]
    months = DEPRECIATION_FACTS["months_used_2028"]
    depreciable_cost = cost - salvage
    annual = depreciable_cost // life
    first_year = annual * months // 12
    accumulated = first_year + annual + annual
    return {
        "depreciable_cost": depreciable_cost,
        "annual_depreciation": annual,
        "first_year_expense": first_year,
        "accumulated_depreciation": accumulated,
        "book_value": cost - accumulated,
    }


def depreciation_schedule_through_2030() -> list[dict[str, object]]:
    expected = expected_depreciation_values()
    rows = []
    accumulated = 0
    for year, expense in ((2028, expected["first_year_expense"]), (2029, 9_000), (2030, 9_000)):
        accumulated += expense
        rows.append(
            {
                "Year": year,
                "Depreciation Expense": format_currency(expense),
                "Accumulated Depreciation": format_currency(accumulated),
                "Ending Book Value": format_currency(DEPRECIATION_FACTS["cost"] - accumulated),
            }
        )
    return rows


def expected_disposal_values() -> dict[str, int]:
    current_year = DISPOSAL_FACTS["annual_depreciation"] // 2
    accumulated = DISPOSAL_FACTS["accumulated_before_2031"] + current_year
    book_value = DISPOSAL_FACTS["cost"] - accumulated
    loss = book_value - DISPOSAL_FACTS["cash_proceeds"]
    return {
        "current_year_depreciation": current_year,
        "accumulated_depreciation": accumulated,
        "book_value": book_value,
        "loss_on_sale": loss,
    }


def expected_analysis_values() -> dict[str, float]:
    net_income = ANALYSIS_FACTS["net_income"]
    net_sales = ANALYSIS_FACTS["net_sales"]
    average_assets = ANALYSIS_FACTS["average_total_assets"]
    profit_margin = net_income / net_sales * 100
    asset_turnover = net_sales / average_assets
    return_on_assets = net_income / average_assets * 100
    return {
        "profit_margin": round(profit_margin, 2),
        "asset_turnover": round(asset_turnover, 2),
        "return_on_assets": round(return_on_assets, 2),
    }


def _evaluate_fields(
    responses: Mapping[str, float | int],
    fields: Sequence[tuple[str, str, float | int]],
    *,
    tolerance: float,
) -> dict[str, object]:
    results: dict[str, dict[str, object]] = {}
    all_correct = True
    for key, label, expected in fields:
        submitted = float(responses.get(key, 0))
        correct = abs(submitted - float(expected)) <= tolerance
        all_correct = all_correct and correct
        results[key] = {
            "label": label,
            "submitted": submitted,
            "expected": expected,
            "correct": correct,
        }
    return {"correct": all_correct, "fields": results}


def evaluate_depreciation(responses: Mapping[str, int]) -> dict[str, object]:
    return _evaluate_fields(responses, DEPRECIATION_FIELDS, tolerance=0.01)


def evaluate_disposal(responses: Mapping[str, int]) -> dict[str, object]:
    return _evaluate_fields(responses, DISPOSAL_FIELDS, tolerance=0.01)


def evaluate_analysis(responses: Mapping[str, float]) -> dict[str, object]:
    return _evaluate_fields(responses, ANALYSIS_FIELDS, tolerance=0.01)
