import re
import unittest

from built_to_last.case_data import (
    ACQUISITION_QUESTIONS,
    ANALYSIS_FIELDS,
    ANALYSIS_QUESTIONS,
    CHOICE_HINTS,
    DEPRECIATION_FIELDS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_FIELDS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    NUMERIC_HINTS,
    UPKEEP_QUESTIONS,
)
from built_to_last.engine import (
    acquisition_totals,
    evaluate_analysis,
    evaluate_choice,
    evaluate_depreciation,
    evaluate_disposal,
    expected_analysis_values,
    expected_depreciation_values,
    expected_disposal_values,
    format_currency,
    lifecycle_totals,
)


ALL_QUESTIONS = (
    *ACQUISITION_QUESTIONS,
    *UPKEEP_QUESTIONS,
    *DEPRECIATION_QUESTIONS,
    *DISPOSAL_QUESTIONS,
    *INTANGIBLE_QUESTIONS,
    *ANALYSIS_QUESTIONS,
)


class AssetLifecycleCalculationTests(unittest.TestCase):
    def test_acquisition_and_later_expenditure_totals(self):
        acquisition = acquisition_totals()
        self.assertEqual(acquisition["Land"], 191_000)
        self.assertEqual(acquisition["Land Improvements"], 36_000)
        self.assertEqual(acquisition["Building"], 420_000)
        self.assertEqual(acquisition["Equipment"], 94_000)
        self.assertEqual(acquisition["Capitalized plant assets"], 741_000)
        self.assertEqual(acquisition["Current-period expense"], 3_000)

        lifecycle = lifecycle_totals()
        self.assertEqual(lifecycle["Building"], 510_000)
        self.assertEqual(lifecycle["Equipment"], 112_000)
        self.assertEqual(lifecycle["Capitalized plant assets"], 849_000)
        self.assertEqual(lifecycle["Current-period expense"], 10_200)

    def test_depreciation_balances(self):
        expected = expected_depreciation_values()
        self.assertEqual(expected["depreciable_cost"], 45_000)
        self.assertEqual(expected["annual_depreciation"], 9_000)
        self.assertEqual(expected["first_year_expense"], 6_750)
        self.assertEqual(expected["accumulated_depreciation"], 24_750)
        self.assertEqual(expected["book_value"], 25_250)
        self.assertTrue(evaluate_depreciation(expected)["correct"])

    def test_disposal_balances_and_loss(self):
        expected = expected_disposal_values()
        self.assertEqual(expected["current_year_depreciation"], 4_500)
        self.assertEqual(expected["accumulated_depreciation"], 29_250)
        self.assertEqual(expected["book_value"], 20_750)
        self.assertEqual(expected["loss_on_sale"], 2_750)
        self.assertTrue(evaluate_disposal(expected)["correct"])

    def test_analysis_relationship(self):
        expected = expected_analysis_values()
        self.assertEqual(expected["profit_margin"], 8.0)
        self.assertEqual(expected["asset_turnover"], 1.5)
        self.assertEqual(expected["return_on_assets"], 12.0)
        self.assertAlmostEqual(
            expected["profit_margin"] * expected["asset_turnover"],
            expected["return_on_assets"],
        )
        self.assertTrue(evaluate_analysis(expected)["correct"])

    def test_every_choice_has_feedback_and_account_statement_connections(self):
        for item in ALL_QUESTIONS:
            result = evaluate_choice(item.id, item.correct)
            self.assertTrue(result["correct"], item.id)
            self.assertTrue(item.explanation, item.id)
            self.assertTrue(item.account_effect, item.id)
            self.assertTrue(item.statement_effect, item.id)
            self.assertIn(item.id, CHOICE_HINTS)
            self.assertIn(item.correct, item.options)
            self.assertEqual(len(set(item.options)), len(item.options))
        for group, fields in (
            ("depreciation", DEPRECIATION_FIELDS),
            ("disposal", DISPOSAL_FIELDS),
            ("analysis", ANALYSIS_FIELDS),
        ):
            self.assertEqual(set(NUMERIC_HINTS[group]), {key for key, _label, _value in fields})

    def test_numeric_fields_match_the_calculation_engines(self):
        self.assertEqual(
            {key: expected for key, _label, expected in DEPRECIATION_FIELDS},
            expected_depreciation_values(),
        )
        self.assertEqual(
            {key: expected for key, _label, expected in DISPOSAL_FIELDS},
            expected_disposal_values(),
        )
        self.assertEqual(
            {key: expected for key, _label, expected in ANALYSIS_FIELDS},
            expected_analysis_values(),
        )

    def test_student_case_language_uses_course_level_reasoning(self):
        fields = []
        for item in ALL_QUESTIONS:
            fields.extend(
                (
                    item.artifact,
                    item.title,
                    item.story,
                    item.prompt,
                    item.explanation,
                    item.account_effect,
                    item.statement_effect,
                    *item.options,
                )
            )
        student_text = " ".join(fields).lower()
        for banned in (
            r"\bdebits?\b",
            r"\bcredits?\b",
            r"\bjournal\b",
            r"\bledger\b",
            r"\bposting\b",
            r"\bimpair(?:ment|ed|ing)?\b",
        ):
            self.assertIsNone(re.search(banned, student_text), banned)

    def test_currency_format(self):
        self.assertEqual(format_currency(-2_750), "-$2,750")
        self.assertEqual(format_currency(849_000), "$849,000")


if __name__ == "__main__":
    unittest.main()
