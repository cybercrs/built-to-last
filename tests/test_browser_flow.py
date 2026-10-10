from pathlib import Path
import tempfile
from browser.build import app_files
import unittest

from streamlit.testing.v1 import AppTest

from built_to_last.case_data import (
    ACQUISITION_QUESTIONS,
    ANALYSIS_QUESTIONS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    UPKEEP_QUESTIONS,
)
from built_to_last.engine import (
    expected_analysis_values,
    expected_depreciation_values,
    expected_disposal_values,
)
from built_to_last.progress import SNAPSHOT_PARAM, decode_snapshot


BROWSER_TEMP = tempfile.TemporaryDirectory()
BROWSER_ROOT = Path(BROWSER_TEMP.name)
for name, content in app_files().items():
    target = BROWSER_ROOT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
BROWSER_APP = str(BROWSER_ROOT / "browser/app.py")


def button(app: AppTest, label: str):
    return next(item for item in app.button if item.label == label)


def complete_choice_group(app, questions, widget_prefix, check_label, final_label):
    for index, item in enumerate(questions):
        app.radio(key=f"widget_{widget_prefix}_{item.id}").set_value(item.correct)
        button(app, check_label).click().run()
        button(
            app, final_label if index == len(questions) - 1 else "Continue"
        ).click().run()


class PerfectAssetLifecycleFlowTests(unittest.TestCase):
    def test_wrong_choice_can_be_revised_without_an_extra_unlock_click(self):
        app = AppTest.from_file(BROWSER_APP, default_timeout=30).run()
        button(app, "Begin the asset lifecycle").click().run()
        item = ACQUISITION_QUESTIONS[0]
        wrong = next(option for option in item.options if option != item.correct)
        app.radio(key=f"widget_acquisition_{item.id}").set_value(wrong).run()

        saved_value = app.query_params[SNAPSHOT_PARAM]
        saved = decode_snapshot(
            saved_value[0] if isinstance(saved_value, list) else saved_value
        )
        self.assertEqual(saved["btl_choice_drafts"]["acquisition"][item.id], wrong)

        button(app, "Check the cost treatment").click().run()
        self.assertTrue(
            any(item.label == "Check revised decision" for item in app.button)
        )
        self.assertTrue(any("Hint:" in message.value for message in app.info))
        self.assertFalse(any(item.correct in message.value for message in app.info))
        app.radio(key=f"widget_acquisition_{item.id}").set_value(item.correct).run()
        button(app, "Check revised decision").click().run()
        self.assertTrue(any(item.label == "Continue" for item in app.button))

    def test_complete_case_reaches_debrief(self):
        app = AppTest.from_file(BROWSER_APP, default_timeout=30).run()
        self.assertFalse(app.exception)
        button(app, "Begin the asset lifecycle").click().run()

        complete_choice_group(
            app,
            ACQUISITION_QUESTIONS,
            "acquisition",
            "Check the cost treatment",
            "Continue to later expenditures",
        )
        complete_choice_group(
            app,
            UPKEEP_QUESTIONS,
            "upkeep",
            "Check the expenditure",
            "Continue to depreciation",
        )

        for key, value in expected_depreciation_values().items():
            app.number_input(key=f"widget_depreciation_value_{key}").set_value(value)
        button(app, "Check the depreciation amounts").click().run()
        complete_choice_group(
            app,
            DEPRECIATION_QUESTIONS,
            "depreciation",
            "Check the depreciation reasoning",
            "Continue to disposal",
        )

        for key, value in expected_disposal_values().items():
            app.number_input(key=f"widget_disposal_value_{key}").set_value(value)
        button(app, "Check the disposal amounts").click().run()
        complete_choice_group(
            app,
            DISPOSAL_QUESTIONS,
            "disposal",
            "Check the disposal reasoning",
            "Continue to intangible assets",
        )
        self.assertEqual(
            [item.id for item in DISPOSAL_QUESTIONS], ["sale_comparison", "retirement"]
        )
        self.assertEqual(app.session_state["btl_stage"], 5)

        complete_choice_group(
            app,
            INTANGIBLE_QUESTIONS,
            "intangible",
            "Check the intangible treatment",
            "Continue to statement analysis",
        )

        for key, value in expected_analysis_values().items():
            app.number_input(key=f"widget_analysis_value_{key}").set_value(value)
        button(app, "Check the ratios").click().run()
        complete_choice_group(
            app,
            ANALYSIS_QUESTIONS,
            "analysis",
            "Check the reporting analysis",
            "Complete the case",
        )

        self.assertFalse(app.exception)
        self.assertTrue(
            any("Asset lifecycle complete" in item.value for item in app.success)
        )
        self.assertIn(
            "Final mastery: complete", "\n".join(item.value for item in app.caption)
        )
        self.assertIn(
            "What the records now show", [item.value for item in app.subheader]
        )
        debrief = "\n".join(item.value for item in app.markdown)
        self.assertIn("$191,000", debrief)
        self.assertIn("$2,750", debrief)
        self.assertEqual(len(app.expander), 3)

        saved_value = app.query_params[SNAPSHOT_PARAM]
        saved = decode_snapshot(
            saved_value[0] if isinstance(saved_value, list) else saved_value
        )
        self.assertIsNotNone(saved)
        self.assertEqual(saved["btl_stage"], 7)
        self.assertEqual(
            len(saved["btl_intangible_responses"]), len(INTANGIBLE_QUESTIONS)
        )


if __name__ == "__main__":
    unittest.main()
