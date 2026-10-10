"""Known teaching cases used by the actual browser walkthrough."""

from built_to_last import case_data as data, engine
from built_to_last.progress import (
    decode_snapshot as decode_snapshot,
    score_summary as score_summary,
)
from browser.navigation import POSITIONS as POSITIONS


def choice(items, check, final="Continue"):
    return {"kind": "choice", "items": items, "check": check, "final": final}


def numbers(values, fields, prefix, check, final=None, radios=()):
    return {
        "kind": "numbers",
        "values": values,
        "fields": fields,
        "prefix": prefix,
        "check": check,
        "final": final,
        "radios": radios,
    }


START = "Begin the asset lifecycle"
PLAN = [
    choice(
        data.ACQUISITION_QUESTIONS,
        "Check the cost treatment",
        "Continue to later expenditures",
    ),
    choice(data.UPKEEP_QUESTIONS, "Check the expenditure", "Continue to depreciation"),
    numbers(
        engine.expected_depreciation_values(),
        data.DEPRECIATION_FIELDS,
        "widget_depreciation_value_",
        "Check the depreciation amounts",
    ),
    choice(
        data.DEPRECIATION_QUESTIONS,
        "Check the depreciation reasoning",
        "Continue to disposal",
    ),
    numbers(
        engine.expected_disposal_values(),
        data.DISPOSAL_FIELDS,
        "widget_disposal_value_",
        "Check the disposal amounts",
    ),
    choice(
        data.DISPOSAL_QUESTIONS,
        "Check the disposal reasoning",
        "Continue to intangible assets",
    ),
    choice(
        data.INTANGIBLE_QUESTIONS,
        "Check the intangible treatment",
        "Continue to statement analysis",
    ),
    numbers(
        engine.expected_analysis_values(),
        data.ANALYSIS_FIELDS,
        "widget_analysis_value_",
        "Check the ratios",
    ),
    choice(
        data.ANALYSIS_QUESTIONS, "Check the reporting analysis", "Complete the case"
    ),
]
