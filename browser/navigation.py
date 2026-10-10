"""App-specific reached pages; review never changes the canonical snapshot."""

from built_to_last.case_data import (
    ACQUISITION_QUESTIONS,
    ANALYSIS_QUESTIONS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    UPKEEP_QUESTIONS,
)
from built_to_last import engine

VIEW_KEY = "btl_browser_view"
VIEW_PARAM = "view"
STAGE_KEY = "btl_stage"
SCROLL_KEY = "btl_scroll_to_top"
RENDERERS = (
    "render_briefing",
    "render_acquisition",
    "render_upkeep",
    "render_depreciation",
    "render_disposal",
    "render_intangibles",
    "render_analysis",
    "render_completion",
)
GROUPS = {
    1: (ACQUISITION_QUESTIONS, "btl_acquisition_index", "btl_acquisition_responses"),
    2: (UPKEEP_QUESTIONS, "btl_upkeep_index", "btl_upkeep_responses"),
    3: (DEPRECIATION_QUESTIONS, "btl_depreciation_index", "btl_depreciation_responses"),
    4: (DISPOSAL_QUESTIONS, "btl_disposal_index", "btl_disposal_responses"),
    5: (INTANGIBLE_QUESTIONS, "btl_intangible_index", "btl_intangible_responses"),
    6: (ANALYSIS_QUESTIONS, "btl_analysis_index", "btl_analysis_responses"),
}
POSITIONS = [(0, None, 0)]
for stage in range(1, len(RENDERERS) - 1):
    group = GROUPS.get(stage)
    POSITIONS.extend(
        (stage, group[1] if group else None, index)
        for index in range(len(group[0]) if group else 1)
    )
POSITIONS.append((len(RENDERERS) - 1, None, 0))


def frontier(state):
    stage = state[STAGE_KEY]
    key = GROUPS[stage][1] if stage in GROUPS else None
    return POSITIONS.index((stage, key, state[key] if key else 0))


def restore_view(state, raw):
    try:
        view = int(raw) if isinstance(raw, str) else -1
    except ValueError:
        view = -1
    state[VIEW_KEY] = view if 0 <= view <= frontier(state) else frontier(state)


def move(state, direction):
    if direction not in (-1, 1):
        raise ValueError("Direction must be Back or Forward")
    target = state[VIEW_KEY] + direction
    if not 0 <= target <= frontier(state):
        return False
    state[VIEW_KEY] = target
    state[SCROLL_KEY] = True
    return True


def can_advance(state):
    if state[VIEW_KEY] != frontier(state):
        return False
    stage = state[STAGE_KEY]
    if stage == 0:
        return True
    for number, group in ((3, "depreciation"), (4, "disposal"), (6, "analysis")):
        if stage == number and not (
            state[f"btl_{group}_submitted"]
            and getattr(engine, f"evaluate_{group}")(state[f"btl_{group}_values"])[
                "correct"
            ]
        ):
            return False
    if stage not in GROUPS:
        return False
    items, key, responses = GROUPS[stage]
    item = items[state[key]]
    return state[responses].get(item.id) == item.correct


def advance(state):
    if not can_advance(state):
        return False
    target = state[VIEW_KEY] + 1
    stage, key, index = POSITIONS[target]
    state[STAGE_KEY] = stage
    if key:
        state[key] = index
    state[VIEW_KEY] = target
    state[SCROLL_KEY] = True
    return True
