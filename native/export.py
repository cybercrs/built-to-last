"""Capture unchanged Built to Last teaching screens and independent Python oracles."""

from __future__ import annotations
import hashlib
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from browser.build import shared_source  # noqa: E402
from browser import navigation  # noqa: E402
from built_to_last import case_data as case, engine, progress  # noqa: E402


class State(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class Container:
    def __init__(self, recorder, node):
        self.recorder, self.node = recorder, node

    def __enter__(self):
        self.recorder.stack.append(self.node["children"])
        return self

    def __exit__(self, *args):
        self.recorder.stack.pop()

    def metric(self, label, value, **kwargs):
        self.node["children"].append(
            {"kind": "metric", "label": label, "value": value, **kwargs}
        )


class Recorder:
    def __init__(self):
        self.session_state = State()
        self.stack = [[]]

    def node(self, kind, **kwargs):
        item = {"kind": kind, **kwargs}
        self.stack[-1].append(item)
        return item

    def set_page_config(self, **kwargs):
        pass

    def markdown(self, text, unsafe_allow_html=False):
        self.node(
            "html" if unsafe_allow_html else "markdown",
            text=text.strip().replace(r"\$", "$"),
        )

    def __getattr__(self, kind):
        if kind in {
            "header",
            "subheader",
            "write",
            "success",
            "warning",
            "info",
            "caption",
        }:
            return lambda text: self.node(kind, text=str(text).replace(r"\$", "$"))
        raise AttributeError(kind)

    def dataframe(self, rows, **kwargs):
        self.node("table", rows=rows)

    def progress(self, value, text):
        self.node("progress", value=value, text=text)

    def radio(self, label, options, **kwargs):
        self.node(
            "radio", label=label.replace(r"\$", "$"), options=options, key=kwargs["key"]
        )
        index = kwargs.get("index")
        return options[index] if index is not None else None

    def number_input(self, label, **kwargs):
        self.node(
            "number",
            label=label,
            key=kwargs["key"],
            min=kwargs["min_value"],
            max=kwargs["max_value"],
            step=kwargs["step"],
            decimal=isinstance(kwargs["step"], float),
        )
        return kwargs.get("value", 0)

    def button(self, label, **kwargs):
        self.node("button", label=label, key=kwargs.get("key"))
        return False

    def columns(self, count):
        node = self.node("columns", children=[])
        for _ in range(count if isinstance(count, int) else len(count)):
            node["children"].append({"kind": "column", "children": []})
        return [Container(self, x) for x in node["children"]]

    def tabs(self, labels):
        node = self.node(
            "tabs",
            children=[{"kind": "tab", "label": x, "children": []} for x in labels],
        )
        return [Container(self, x) for x in node["children"]]

    def expander(self, label):
        return Container(self, self.node("details", label=label, children=[]))

    @contextmanager
    def capture(self):
        self.stack = [[]]
        yield self.stack[0]


CHOICE = [
    {
        "stage": stage,
        "prefix": prefix,
        "draft": prefix,
        "indexKey": index,
        "responseKey": responses,
        "salt": prefix + "-answer-order:",
        "items": [asdict(x) for x in items],
    }
    for stage, prefix, index, responses, items in [
        (1, "acquisition", "ai", "ar", case.ACQUISITION_QUESTIONS),
        (2, "upkeep", "ui", "ur", case.UPKEEP_QUESTIONS),
        (3, "depreciation", "di", "dr", case.DEPRECIATION_QUESTIONS),
        (4, "disposal", "xi", "xr", case.DISPOSAL_QUESTIONS),
        (5, "intangible", "ii", "ir", case.INTANGIBLE_QUESTIONS),
        (6, "analysis", "ri", "rr", case.ANALYSIS_QUESTIONS),
    ]
]
NUMBERS = [
    {
        "stage": stage,
        "prefix": prefix,
        "draft": prefix,
        "valuesKey": value,
        "submittedKey": submitted,
        "fields": fields,
        "choices": [],
        "expected": expected,
        "allowFloat": True,
        "inputPrefix": f"widget_{prefix}_value_",
    }
    for stage, prefix, value, submitted, fields, expected in [
        (
            3,
            "depreciation",
            "dv",
            "ds",
            case.DEPRECIATION_FIELDS,
            engine.expected_depreciation_values(),
        ),
        (
            4,
            "disposal",
            "xv",
            "xs",
            case.DISPOSAL_FIELDS,
            engine.expected_disposal_values(),
        ),
        (
            6,
            "analysis",
            "rv",
            "rs",
            case.ANALYSIS_FIELDS,
            engine.expected_analysis_values(),
        ),
    ]
]


def state_at(stage, index=0, status="unanswered"):
    state = State(progress.activity_defaults())
    state.btl_shuffle_seed = 0
    state.btl_stage = stage
    for group in CHOICE:
        prefix = group["prefix"]
        items = group["items"]
        state[f"btl_{prefix}_index"] = (
            len(items) - 1
            if group["stage"] < stage
            else index
            if group["stage"] == stage
            else 0
        )
        state[f"btl_{prefix}_responses"] = {
            x["id"]: x["correct"]
            if group["stage"] < stage or i < index or status == "correct"
            else next(o for o in x["options"] if o != x["correct"])
            for i, x in enumerate(items)
            if group["stage"] < stage
            or (
                group["stage"] == stage
                and (i < index or (i == index and status in ["wrong", "correct"]))
            )
        }
    for group in NUMBERS:
        active = group["stage"] == stage
        if group["stage"] < stage or (
            active
            and (
                index > 0
                or status in ["calculated", "wrong", "correct", "wrongNumbers"]
            )
        ):
            good = group["stage"] < stage or index > 0 or status != "wrongNumbers"
            state[f"btl_{group['prefix']}_values"] = (
                group["expected"] if good else {k: 0 for k in group["expected"]}
            )
            state[f"btl_{group['prefix']}_submitted"] = True
    return state


def export():
    recorder = Recorder()
    namespace = {}
    with patch.dict(sys.modules, {"streamlit": recorder}):
        exec(compile(shared_source(), "original_renderer", "exec"), namespace)
    namespace["render_feedback_row"] = (
        lambda label, correct, detail, value="": recorder.node(
            "feedback", label=label, correct=correct, detail=detail, value=value
        )
    )
    positions = [
        {"stage": stage, "index": i} for stage, _key, i in navigation.POSITIONS
    ]
    screens = []
    for pos in positions:
        variants = {}
        for status in (
            ["unanswered", "wrongNumbers", "calculated", "wrong", "correct"]
            if any(x["stage"] == pos["stage"] for x in NUMBERS)
            else ["unanswered", "wrong", "correct"]
        ):
            recorder.session_state = state_at(**pos, status=status)
            with recorder.capture() as events:
                namespace[navigation.RENDERERS[pos["stage"]]]()
            variants[status] = events
        screens.append({**pos, "variants": variants})
    with recorder.capture() as hero:
        namespace["render_hero"]()
    defaults = progress.activity_defaults()
    defaults["btl_shuffle_seed"] = 0
    data = {
        "title": "Built to Last?",
        "slug": "built-to-last",
        "statePrefix": "btl",
        "source": "0e39ccf824d2e44bdc4ff3794e242077a0462baf",
        "seedKey": "z",
        "draftKey": "cd",
        "numericDraftKey": "nd",
        "baseVersion": 3,
        "extensionVersion": 4,
        "defaults": progress._payload_from_state(defaults),
        "groups": CHOICE,
        "numbers": NUMBERS,
        "positions": positions,
        "screens": screens,
        "hero": hero,
        "stages": namespace["STAGE_LABELS"],
        "facts": {
            "depreciation": case.DEPRECIATION_FACTS,
            "disposal": case.DISPOSAL_FACTS,
            "analysis": case.ANALYSIS_FACTS,
        },
    }
    here = Path(__file__).resolve().parent
    (here / "content.js").write_text(
        "// Generated without modifying original Python teaching sources.\nexport const DATA = "
        + json.dumps(data, separators=(",", ":"), ensure_ascii=True)
        + ";\n"
    )
    (here / "original.css").write_text(
        namespace["APP_CSS"].replace("<style>", "").replace("</style>", "").strip()
        + "\n"
    )
    fixtures = {
        "calculations": {
            "acquisition": engine.acquisition_totals(),
            "lifecycle": engine.lifecycle_totals(),
            "depreciationSchedule": engine.depreciation_schedule_through_2030(),
            "expected": {x["prefix"]: x["expected"] for x in NUMBERS},
        },
        "snapshots": [],
        "shuffles": [],
    }

    def add_snapshot(state, wire=None):
        wire = progress._payload_from_state(state) if wire is None else wire
        token = progress._encode(wire)
        restored = progress.decode_snapshot(token)
        assert restored is not None
        fixtures["snapshots"].append(
            {
                "token": token,
                "payload": progress._payload_from_state(restored),
                "seed": str(wire["z"]),
            }
        )

    for stage in range(8):
        add_snapshot(
            state_at(stage, status="wrong" if stage in range(1, 7) else "correct")
        )
    numeric_draft = state_at(3)
    numeric_draft.btl_shuffle_seed = 2**63 - 1
    numeric_draft.btl_numeric_drafts["depreciation"] = {"depreciable_cost": 45000}
    add_snapshot(numeric_draft)
    choice_draft = state_at(1)
    choice_draft.btl_choice_drafts["acquisition"] = {
        case.ACQUISITION_QUESTIONS[0].id: case.ACQUISITION_QUESTIONS[0].options[0]
    }
    add_snapshot(choice_draft)
    completed = state_at(7, status="correct")
    wire = progress._payload_from_state(completed)
    wire["xi"] = 2
    wire["xr"]["exchange"] = (
        "The fair value assigned to the old simulator and the new simulator"
    )
    wire["at"]["choice:exchange"] = 1
    wire["fp"]["choice:exchange"] = True
    add_snapshot(completed, wire)
    active = state_at(5)
    wire = progress._payload_from_state(active)
    wire["s"] = 4
    wire["xi"] = 2
    wire["cd"]["disposal"] = {
        "exchange": "The old simulator's original purchase invoice by itself"
    }
    wire["at"]["choice:exchange"] = 1
    wire["fp"]["choice:exchange"] = False
    add_snapshot(active, wire)
    for seed in [0, 1, 42, 2**53 + 1, 2**63 - 1]:
        for group in CHOICE:
            for item in group["items"]:
                salt = group["salt"] + item["id"]
                fixtures["shuffles"].append(
                    {
                        "seed": str(seed),
                        "input": item["options"],
                        "salt": salt,
                        "output": progress.stable_shuffle(item["options"], seed, salt),
                    }
                )
    (here / "tests").mkdir(exist_ok=True)
    (here / "tests/python-oracles.json").write_text(
        json.dumps(fixtures, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "pages": len(positions),
                "variants": sum(len(x["variants"]) for x in screens),
                "generated_sha256": {
                    name: hashlib.sha256((here / name).read_bytes()).hexdigest()
                    for name in ["content.js", "original.css"]
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    export()
