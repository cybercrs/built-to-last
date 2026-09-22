import unittest

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
from built_to_last.progress import (
    SNAPSHOT_PARAM,
    activity_defaults,
    decode_snapshot,
    encode_state,
    record_attempt,
    reset_saved_progress,
    restore_session_state,
    score_summary,
    stable_shuffle,
    _encode,
    _payload_from_state,
)


def completed_state():
    state = activity_defaults()
    state["btl_stage"] = 7
    for index_key, response_key, questions in (
        ("btl_acquisition_index", "btl_acquisition_responses", ACQUISITION_QUESTIONS),
        ("btl_upkeep_index", "btl_upkeep_responses", UPKEEP_QUESTIONS),
        ("btl_depreciation_index", "btl_depreciation_responses", DEPRECIATION_QUESTIONS),
        ("btl_disposal_index", "btl_disposal_responses", DISPOSAL_QUESTIONS),
        ("btl_intangible_index", "btl_intangible_responses", INTANGIBLE_QUESTIONS),
        ("btl_analysis_index", "btl_analysis_responses", ANALYSIS_QUESTIONS),
    ):
        state[index_key] = len(questions) - 1
        state[response_key] = {item.id: item.correct for item in questions}
    state["btl_depreciation_values"] = expected_depreciation_values()
    state["btl_depreciation_submitted"] = True
    state["btl_disposal_values"] = expected_disposal_values()
    state["btl_disposal_submitted"] = True
    state["btl_analysis_values"] = expected_analysis_values()
    state["btl_analysis_submitted"] = True
    return state


class ProgressSnapshotTests(unittest.TestCase):
    def test_round_trip_completed_progress(self):
        state = completed_state()
        for item in ACQUISITION_QUESTIONS:
            record_attempt(state, f"choice:{item.id}", True)
        token = encode_state(state)
        restored = decode_snapshot(token)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["btl_stage"], 7)
        self.assertEqual(restored["btl_disposal_values"]["book_value"], 20_750)
        self.assertNotIn("name", token.lower())
        self.assertNotIn("email", token.lower())

    def test_removed_disposal_decision_does_not_erase_completed_progress(self):
        payload = _payload_from_state(completed_state())
        payload["xi"] = 2
        payload["xr"]["exchange"] = "The fair value assigned to the old simulator and the new simulator"
        payload["at"]["choice:exchange"] = 1
        payload["fp"]["choice:exchange"] = True

        restored = decode_snapshot(_encode(payload))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["btl_stage"], 7)
        self.assertEqual(restored["btl_disposal_index"], 1)
        self.assertEqual(set(restored["btl_disposal_responses"]), {"sale_comparison", "retirement"})
        self.assertNotIn("choice:exchange", restored["btl_attempts"])

    def test_removed_disposal_decision_moves_active_student_to_intangibles(self):
        payload = _payload_from_state(completed_state())
        payload["s"] = 4
        payload["xi"] = 2
        payload["ii"] = 0
        payload["ir"] = {}
        payload["rv"] = {}
        payload["rs"] = False
        payload["ri"] = 0
        payload["rr"] = {}
        payload["cd"]["disposal"] = {"exchange": "The old simulator's original purchase invoice by itself"}
        payload["at"]["choice:exchange"] = 1
        payload["fp"]["choice:exchange"] = False

        restored = decode_snapshot(_encode(payload))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["btl_stage"], 5)
        self.assertEqual(restored["btl_disposal_index"], 1)
        self.assertEqual(restored["btl_choice_drafts"]["disposal"], {})
        self.assertNotIn("choice:exchange", restored["btl_first_pass"])

    def test_current_incorrect_choice_can_be_restored_for_revision(self):
        state = activity_defaults()
        state["btl_shuffle_seed"] = 34110
        state["btl_stage"] = 1
        first = ACQUISITION_QUESTIONS[0]
        wrong = next(option for option in first.options if option != first.correct)
        state["btl_acquisition_responses"] = {first.id: wrong}
        record_attempt(state, f"choice:{first.id}", False)
        restored = decode_snapshot(encode_state(state))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["btl_acquisition_responses"][first.id], wrong)

    def test_unsubmitted_choice_and_numeric_drafts_round_trip(self):
        state = activity_defaults()
        state["btl_shuffle_seed"] = 202610
        state["btl_stage"] = 1
        first = ACQUISITION_QUESTIONS[0]
        state["btl_choice_drafts"]["acquisition"] = {first.id: first.options[0]}
        restored = decode_snapshot(encode_state(state))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["btl_choice_drafts"]["acquisition"][first.id], first.options[0])

        state = activity_defaults()
        state["btl_shuffle_seed"] = 202610
        state["btl_stage"] = 3
        for index_key, response_key, questions in (
            (
                "btl_acquisition_index",
                "btl_acquisition_responses",
                ACQUISITION_QUESTIONS,
            ),
            ("btl_upkeep_index", "btl_upkeep_responses", UPKEEP_QUESTIONS),
        ):
            ordered = questions
            state[index_key] = len(ordered) - 1
            state[response_key] = {item.id: item.correct for item in ordered}
        state["btl_numeric_drafts"]["depreciation"] = {"depreciable_cost": 45_000}
        restored = decode_snapshot(encode_state(state))
        self.assertIsNotNone(restored)
        self.assertEqual(restored["btl_numeric_drafts"]["depreciation"]["depreciable_cost"], 45_000)

    def test_answer_shuffle_is_repeatable_and_changes_the_default_order(self):
        options = ACQUISITION_QUESTIONS[0].options
        first = stable_shuffle(options, 12345, "acquisition-answer-order:site_closing")
        second = stable_shuffle(options, 12345, "acquisition-answer-order:site_closing")
        self.assertEqual(first, second)
        self.assertNotEqual(first, list(options))

    def test_skipping_required_stages_is_rejected(self):
        state = activity_defaults()
        state["btl_stage"] = 4
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_future_calculation_is_rejected(self):
        state = activity_defaults()
        state["btl_stage"] = 1
        state["btl_depreciation_values"] = expected_depreciation_values()
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_incorrect_completed_calculation_is_rejected(self):
        state = completed_state()
        state["btl_disposal_values"]["book_value"] = 25_250
        self.assertIsNone(decode_snapshot(encode_state(state)))

    def test_malformed_or_oversized_tokens_are_rejected(self):
        self.assertIsNone(decode_snapshot("not-a-valid-token"))
        self.assertIsNone(decode_snapshot("x" * 20_001))

    def test_restore_and_reset(self):
        state = completed_state()
        destination = {}
        self.assertTrue(restore_session_state(destination, encode_state(state)))
        self.assertEqual(destination["btl_stage"], 7)

        query = {}
        reset_saved_progress(destination, query)
        self.assertEqual(destination["btl_stage"], 0)
        self.assertEqual(destination["btl_acquisition_responses"], {})
        self.assertIn(SNAPSHOT_PARAM, query)
        self.assertIsNotNone(decode_snapshot(query[SNAPSHOT_PARAM]))

    def test_score_summary_tracks_first_pass_and_revisions(self):
        state = activity_defaults()
        record_attempt(state, "choice:site_closing", False)
        record_attempt(state, "choice:site_closing", True)
        record_attempt(state, "choice:parking_lot", True)
        score = score_summary(state)
        self.assertEqual(score["attempted"], 2)
        self.assertEqual(score["correct"], 1)
        self.assertEqual(score["revisions"], 1)


if __name__ == "__main__":
    unittest.main()
