"""Compact, validated, non-identifying progress snapshots."""

from __future__ import annotations

import base64
import hashlib
import json
import random
import secrets
import zlib
from collections.abc import MutableMapping, Sequence
from typing import Any

from built_to_last.case_data import (
    ACQUISITION_QUESTIONS,
    ANALYSIS_FIELDS,
    ANALYSIS_QUESTIONS,
    DEPRECIATION_FIELDS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_FIELDS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    UPKEEP_QUESTIONS,
    ChoiceQuestion,
)
from built_to_last.engine import evaluate_analysis, evaluate_depreciation, evaluate_disposal


SNAPSHOT_PARAM = "progress"
SNAPSHOT_VERSION = 3
MAX_TOKEN_LENGTH = 20_000
MAX_JSON_BYTES = 40_000
FINAL_STAGE = 7


def activity_defaults() -> dict[str, Any]:
    return {
        "btl_stage": 0,
        "btl_shuffle_seed": secrets.randbits(63),
        "btl_choice_drafts": {
            "acquisition": {},
            "upkeep": {},
            "depreciation": {},
            "disposal": {},
            "intangible": {},
            "analysis": {},
        },
        "btl_numeric_drafts": {
            "depreciation": {},
            "disposal": {},
            "analysis": {},
        },
        "btl_acquisition_index": 0,
        "btl_acquisition_responses": {},
        "btl_upkeep_index": 0,
        "btl_upkeep_responses": {},
        "btl_depreciation_values": {},
        "btl_depreciation_submitted": False,
        "btl_depreciation_index": 0,
        "btl_depreciation_responses": {},
        "btl_disposal_values": {},
        "btl_disposal_submitted": False,
        "btl_disposal_index": 0,
        "btl_disposal_responses": {},
        "btl_intangible_index": 0,
        "btl_intangible_responses": {},
        "btl_analysis_values": {},
        "btl_analysis_submitted": False,
        "btl_analysis_index": 0,
        "btl_analysis_responses": {},
        "btl_attempts": {},
        "btl_first_pass": {},
        "btl_scroll_to_top": False,
    }


def stable_shuffle(items: Sequence[Any], seed: int, salt: str) -> list[Any]:
    """Return a stable per-student order that survives reruns and refreshes."""

    digest = hashlib.sha256(f"{seed}:{salt}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    ordered = list(items)
    rng.shuffle(ordered)
    if len(ordered) > 1 and ordered == list(items):
        ordered = ordered[1:] + ordered[:1]
    return ordered


def _encode(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def _decode(token: str) -> object:
    padding = "=" * (-len(token) % 4)
    compressed = base64.b64decode(token + padding, altchars=b"-_", validate=True)
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(compressed, MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES or decompressor.unconsumed_tail:
        raise ValueError("Snapshot is too large")
    raw += decompressor.flush(MAX_JSON_BYTES + 1 - len(raw))
    if len(raw) > MAX_JSON_BYTES or decompressor.unused_data:
        raise ValueError("Snapshot is invalid")
    return json.loads(raw.decode("utf-8"))


def _require_index(value: object, count: int) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise ValueError("Invalid activity index")
    return value


def _validate_choice_group(
    raw: object,
    raw_index: object,
    items: Sequence[ChoiceQuestion],
    stage: int,
    group_stage: int,
) -> tuple[dict[str, str], int]:
    if not isinstance(raw, dict):
        raise ValueError("Answers must be an object")
    ordered_items = list(items)
    ids = [item.id for item in ordered_items]
    if set(raw) != set(ids[: len(raw)]):
        raise ValueError("Answers must follow the activity order")
    normalized: dict[str, str] = {}
    for item in ordered_items[: len(raw)]:
        value = raw[item.id]
        if not isinstance(value, str) or value not in item.options:
            raise ValueError("Unknown answer")
        normalized[item.id] = value

    index = _require_index(raw_index, len(ordered_items))
    valid_indexes = {min(len(normalized), len(ordered_items) - 1)}
    if normalized:
        valid_indexes.add(len(normalized) - 1)
    if index not in valid_indexes:
        raise ValueError("Answer index and answers do not agree")

    if stage < group_stage and normalized:
        raise ValueError("Future answers are not allowed")
    if stage < group_stage and index != 0:
        raise ValueError("Future index is not allowed")
    if stage > group_stage:
        if len(normalized) != len(ordered_items) or any(
            normalized[item.id] != item.correct for item in ordered_items
        ):
            raise ValueError("Completed stage is incomplete")
    if stage == group_stage and normalized:
        completed_count = index if index == len(normalized) else max(0, len(normalized) - 1)
        for item in ordered_items[:completed_count]:
            if normalized[item.id] != item.correct:
                raise ValueError("Earlier answers must be correct")
    return normalized, index


def _validate_choice_draft(
    raw: object,
    items: Sequence[ChoiceQuestion],
    responses: dict[str, str],
    index: int,
    stage: int,
    group_stage: int,
) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("Choice draft must be an object")
    if stage != group_stage:
        if raw:
            raise ValueError("Choice draft is outside the active step")
        return {}

    ordered_items = list(items)
    current = ordered_items[index]
    if set(raw) - {current.id}:
        raise ValueError("Choice draft is not for the current decision")
    if not raw:
        return {}

    value = raw[current.id]
    if not isinstance(value, str) or value not in current.options:
        raise ValueError("Unknown draft answer")
    if responses.get(current.id) == current.correct:
        raise ValueError("A completed decision cannot have a draft")
    return {current.id: value}


def _validate_numeric_draft(
    raw: object,
    fields: Sequence[tuple[str, str, float | int]],
    stage: int,
    group_stage: int,
) -> dict[str, float | int]:
    if not isinstance(raw, dict):
        raise ValueError("Numeric draft must be an object")
    if stage != group_stage:
        if raw:
            raise ValueError("Numeric draft is outside the active step")
        return {}

    allowed = {key for key, _label, _expected in fields}
    if set(raw) - allowed:
        raise ValueError("Unknown numeric draft field")
    normalized: dict[str, float | int] = {}
    for key, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Numeric draft value is invalid")
        if not 0 <= float(value) <= 1_000_000_000:
            raise ValueError("Numeric draft value is out of range")
        normalized[key] = value
    return normalized


def _validate_values(
    raw: object,
    submitted: object,
    fields: Sequence[tuple[str, str, float | int]],
) -> tuple[dict[str, float | int], bool]:
    if type(submitted) is not bool or not isinstance(raw, dict):
        raise ValueError("Invalid calculation state")
    keys = [key for key, _label, _expected in fields]
    if raw and set(raw) != set(keys):
        raise ValueError("Calculation fields are incomplete")
    normalized: dict[str, float | int] = {}
    for key in keys:
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Calculation value is invalid")
        if not 0 <= float(value) <= 1_000_000_000:
            raise ValueError("Calculation value is out of range")
        normalized[key] = value
    if submitted and len(normalized) != len(keys):
        raise ValueError("Submitted calculation is incomplete")
    return normalized, submitted


def _validate_attempts(raw: object, *, booleans: bool) -> dict[str, Any]:
    if not isinstance(raw, dict) or len(raw) > 100:
        raise ValueError("Invalid attempt data")
    normalized = {}
    for key, value in raw.items():
        if not isinstance(key, str) or len(key) > 100:
            raise ValueError("Invalid attempt key")
        if booleans:
            if type(value) is not bool:
                raise ValueError("Invalid first-pass value")
        elif type(value) is not int or not 1 <= value <= 50:
            raise ValueError("Invalid attempt count")
        normalized[key] = value
    return normalized


def _payload_from_state(state: MutableMapping[str, Any]) -> dict[str, Any]:
    return {
        "v": SNAPSHOT_VERSION,
        "s": int(state.get("btl_stage", 0)),
        "z": int(state.get("btl_shuffle_seed", 0)),
        "cd": {
            key: dict(value)
            for key, value in state.get("btl_choice_drafts", {}).items()
        },
        "nd": {
            key: dict(value)
            for key, value in state.get("btl_numeric_drafts", {}).items()
        },
        "ai": int(state.get("btl_acquisition_index", 0)),
        "ar": dict(state.get("btl_acquisition_responses", {})),
        "ui": int(state.get("btl_upkeep_index", 0)),
        "ur": dict(state.get("btl_upkeep_responses", {})),
        "dv": dict(state.get("btl_depreciation_values", {})),
        "ds": bool(state.get("btl_depreciation_submitted", False)),
        "di": int(state.get("btl_depreciation_index", 0)),
        "dr": dict(state.get("btl_depreciation_responses", {})),
        "xv": dict(state.get("btl_disposal_values", {})),
        "xs": bool(state.get("btl_disposal_submitted", False)),
        "xi": int(state.get("btl_disposal_index", 0)),
        "xr": dict(state.get("btl_disposal_responses", {})),
        "ii": int(state.get("btl_intangible_index", 0)),
        "ir": dict(state.get("btl_intangible_responses", {})),
        "rv": dict(state.get("btl_analysis_values", {})),
        "rs": bool(state.get("btl_analysis_submitted", False)),
        "ri": int(state.get("btl_analysis_index", 0)),
        "rr": dict(state.get("btl_analysis_responses", {})),
        "at": dict(state.get("btl_attempts", {})),
        "fp": dict(state.get("btl_first_pass", {})),
    }


def encode_state(state: MutableMapping[str, Any]) -> str:
    return _encode(_payload_from_state(state))


def _migrate_removed_disposal_decision(payload: dict[str, Any]) -> None:
    """Preserve saved work when the former third disposal decision is removed."""

    responses = payload["xr"]
    index = payload["xi"]
    stage = payload["s"]
    drafts = payload["cd"]
    attempts = payload["at"]
    first_pass = payload["fp"]
    if (
        not isinstance(responses, dict)
        or type(index) is not int
        or type(stage) is not int
        or not isinstance(drafts, dict)
        or not isinstance(drafts.get("disposal"), dict)
        or not isinstance(attempts, dict)
        or not isinstance(first_pass, dict)
    ):
        raise ValueError("Invalid saved disposal state")

    retired_answer = responses.get("exchange")
    retired_draft = drafts["disposal"].get("exchange")
    if index == 2:
        if stage < 4 or any(
            responses.get(item.id) != item.correct for item in DISPOSAL_QUESTIONS
        ):
            raise ValueError("Earlier disposal decisions are incomplete")
        if stage > 4 and retired_answer != "The fair value assigned to the old simulator and the new simulator":
            raise ValueError("Saved disposal stage is incomplete")
        if retired_answer is not None and (not isinstance(retired_answer, str) or len(retired_answer) > 300):
            raise ValueError("Invalid saved disposal answer")
        if retired_draft is not None and (not isinstance(retired_draft, str) or len(retired_draft) > 300):
            raise ValueError("Invalid saved disposal draft")
        payload["xi"] = len(DISPOSAL_QUESTIONS) - 1
        if stage == 4:
            payload["s"] = 5
    elif retired_answer is not None or retired_draft is not None:
        raise ValueError("Retired decision appears outside its former position")

    responses.pop("exchange", None)
    drafts["disposal"].pop("exchange", None)
    attempts.pop("choice:exchange", None)
    first_pass.pop("choice:exchange", None)


def decode_snapshot(token: object) -> dict[str, Any] | None:
    if isinstance(token, list):
        token = token[0] if token else None
    if not isinstance(token, str) or not token or len(token) > MAX_TOKEN_LENGTH:
        return None
    try:
        payload = _decode(token)
        expected_keys = {
            "v", "s", "z", "cd", "nd", "ai", "ar", "ui", "ur", "dv", "ds", "di",
            "dr", "xv", "xs", "xi", "xr", "ii", "ir", "rv", "rs", "ri", "rr", "at",
            "fp",
        }
        if not isinstance(payload, dict) or set(payload) != expected_keys:
            raise ValueError("Snapshot fields are invalid")
        if payload["v"] != SNAPSHOT_VERSION:
            raise ValueError("Unsupported snapshot version")
        _migrate_removed_disposal_decision(payload)
        stage = payload["s"]
        if type(stage) is not int or not 0 <= stage <= FINAL_STAGE:
            raise ValueError("Invalid stage")
        shuffle_seed = payload["z"]
        if type(shuffle_seed) is not int or not 0 <= shuffle_seed < 2**63:
            raise ValueError("Invalid shuffle seed")

        acquisition, acquisition_index = _validate_choice_group(
            payload["ar"], payload["ai"], ACQUISITION_QUESTIONS, stage, 1,
        )
        upkeep, upkeep_index = _validate_choice_group(
            payload["ur"], payload["ui"], UPKEEP_QUESTIONS, stage, 2,
        )
        depreciation_values, depreciation_submitted = _validate_values(
            payload["dv"], payload["ds"], DEPRECIATION_FIELDS
        )
        depreciation, depreciation_index = _validate_choice_group(
            payload["dr"], payload["di"], DEPRECIATION_QUESTIONS, stage, 3,
        )
        disposal_values, disposal_submitted = _validate_values(
            payload["xv"], payload["xs"], DISPOSAL_FIELDS
        )
        disposal, disposal_index = _validate_choice_group(
            payload["xr"], payload["xi"], DISPOSAL_QUESTIONS, stage, 4,
        )
        intangible, intangible_index = _validate_choice_group(
            payload["ir"], payload["ii"], INTANGIBLE_QUESTIONS, stage, 5,
        )
        analysis_values, analysis_submitted = _validate_values(
            payload["rv"], payload["rs"], ANALYSIS_FIELDS
        )
        analysis, analysis_index = _validate_choice_group(
            payload["rr"], payload["ri"], ANALYSIS_QUESTIONS, stage, 6,
        )

        raw_choice_drafts = payload["cd"]
        choice_specs = {
            "acquisition": (
                ACQUISITION_QUESTIONS, acquisition, acquisition_index, 1,
            ),
            "upkeep": (UPKEEP_QUESTIONS, upkeep, upkeep_index, 2),
            "depreciation": (
                DEPRECIATION_QUESTIONS, depreciation, depreciation_index, 3,
            ),
            "disposal": (
                DISPOSAL_QUESTIONS, disposal, disposal_index, 4,
            ),
            "intangible": (
                INTANGIBLE_QUESTIONS, intangible, intangible_index, 5,
            ),
            "analysis": (
                ANALYSIS_QUESTIONS, analysis, analysis_index, 6,
            ),
        }
        if not isinstance(raw_choice_drafts, dict) or set(raw_choice_drafts) != set(choice_specs):
            raise ValueError("Invalid choice draft groups")
        choice_drafts = {
            key: _validate_choice_draft(
                raw_choice_drafts[key], items, responses, index, stage, group_stage,
            )
            for key, (items, responses, index, group_stage) in choice_specs.items()
        }

        raw_numeric_drafts = payload["nd"]
        numeric_specs = {
            "depreciation": (DEPRECIATION_FIELDS, 3),
            "disposal": (DISPOSAL_FIELDS, 4),
            "analysis": (ANALYSIS_FIELDS, 6),
        }
        if not isinstance(raw_numeric_drafts, dict) or set(raw_numeric_drafts) != set(numeric_specs):
            raise ValueError("Invalid numeric draft groups")
        numeric_drafts = {
            key: _validate_numeric_draft(raw_numeric_drafts[key], fields, stage, group_stage)
            for key, (fields, group_stage) in numeric_specs.items()
        }

        if stage < 3 and (depreciation_values or depreciation_submitted):
            raise ValueError("Future calculation is not allowed")
        if stage > 3 and not (depreciation_submitted and evaluate_depreciation(depreciation_values)["correct"]):
            raise ValueError("Depreciation stage is incomplete")
        if depreciation and not (depreciation_submitted and evaluate_depreciation(depreciation_values)["correct"]):
            raise ValueError("Depreciation reasoning requires correct calculations")
        if depreciation_submitted and evaluate_depreciation(depreciation_values)["correct"] and numeric_drafts["depreciation"]:
            raise ValueError("Completed depreciation amounts cannot have a draft")

        if stage < 4 and (disposal_values or disposal_submitted):
            raise ValueError("Future calculation is not allowed")
        if stage > 4 and not (disposal_submitted and evaluate_disposal(disposal_values)["correct"]):
            raise ValueError("Disposal stage is incomplete")
        if disposal and not (disposal_submitted and evaluate_disposal(disposal_values)["correct"]):
            raise ValueError("Disposal reasoning requires correct calculations")
        if disposal_submitted and evaluate_disposal(disposal_values)["correct"] and numeric_drafts["disposal"]:
            raise ValueError("Completed disposal amounts cannot have a draft")

        if stage < 6 and (analysis_values or analysis_submitted):
            raise ValueError("Future calculation is not allowed")
        if stage > 6 and not (analysis_submitted and evaluate_analysis(analysis_values)["correct"]):
            raise ValueError("Analysis stage is incomplete")
        if analysis and not (analysis_submitted and evaluate_analysis(analysis_values)["correct"]):
            raise ValueError("Analysis reasoning requires correct calculations")
        if analysis_submitted and evaluate_analysis(analysis_values)["correct"] and numeric_drafts["analysis"]:
            raise ValueError("Completed analysis amounts cannot have a draft")

        attempts = _validate_attempts(payload["at"], booleans=False)
        first_pass = _validate_attempts(payload["fp"], booleans=True)
        if set(first_pass) - set(attempts):
            raise ValueError("First-pass data has no attempt")

        return {
            "btl_stage": stage,
            "btl_shuffle_seed": shuffle_seed,
            "btl_choice_drafts": choice_drafts,
            "btl_numeric_drafts": numeric_drafts,
            "btl_acquisition_index": acquisition_index,
            "btl_acquisition_responses": acquisition,
            "btl_upkeep_index": upkeep_index,
            "btl_upkeep_responses": upkeep,
            "btl_depreciation_values": depreciation_values,
            "btl_depreciation_submitted": depreciation_submitted,
            "btl_depreciation_index": depreciation_index,
            "btl_depreciation_responses": depreciation,
            "btl_disposal_values": disposal_values,
            "btl_disposal_submitted": disposal_submitted,
            "btl_disposal_index": disposal_index,
            "btl_disposal_responses": disposal,
            "btl_intangible_index": intangible_index,
            "btl_intangible_responses": intangible,
            "btl_analysis_values": analysis_values,
            "btl_analysis_submitted": analysis_submitted,
            "btl_analysis_index": analysis_index,
            "btl_analysis_responses": analysis,
            "btl_attempts": attempts,
            "btl_first_pass": first_pass,
        }
    except (ValueError, TypeError, KeyError, OverflowError, json.JSONDecodeError, zlib.error):
        return None


def restore_session_state(destination: MutableMapping[str, Any], token: object) -> bool:
    restored = decode_snapshot(token)
    if restored is None:
        return False
    destination.update(restored)
    return True


def sync_progress_query(state: MutableMapping[str, Any], query: MutableMapping[str, Any]) -> None:
    token = encode_state(state)
    current = query.get(SNAPSHOT_PARAM)
    if isinstance(current, list):
        current = current[0] if current else None
    if current != token:
        query[SNAPSHOT_PARAM] = token


def reset_saved_progress(state: MutableMapping[str, Any], query: MutableMapping[str, Any]) -> None:
    for key in list(state):
        if key.startswith("btl_") or key.startswith("widget_"):
            del state[key]
    state.update(activity_defaults())
    query[SNAPSHOT_PARAM] = encode_state(state)


def record_attempt(state: MutableMapping[str, Any], key: str, correct: bool) -> None:
    attempts = dict(state.get("btl_attempts", {}))
    first_pass = dict(state.get("btl_first_pass", {}))
    attempts[key] = attempts.get(key, 0) + 1
    if key not in first_pass:
        first_pass[key] = bool(correct)
    state["btl_attempts"] = attempts
    state["btl_first_pass"] = first_pass


def score_summary(state: MutableMapping[str, Any]) -> dict[str, int]:
    attempts = dict(state.get("btl_attempts", {}))
    first_pass = dict(state.get("btl_first_pass", {}))
    return {
        "attempted": len(attempts),
        "correct": sum(1 for value in first_pass.values() if value),
        "revisions": sum(max(0, count - 1) for count in attempts.values()),
    }
