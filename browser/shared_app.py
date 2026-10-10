"""Student-facing Streamlit application for Built to Last."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from html import escape

import streamlit as st

from built_to_last.case_data import (
    ACQUISITION_QUESTIONS,
    ANALYSIS_FACTS,
    ANALYSIS_FIELDS,
    ANALYSIS_QUESTIONS,
    CHOICE_HINTS,
    COMPANY_NAME,
    DEPRECIATION_FACTS,
    DEPRECIATION_FIELDS,
    DEPRECIATION_QUESTIONS,
    DISPOSAL_FACTS,
    DISPOSAL_FIELDS,
    DISPOSAL_QUESTIONS,
    INTANGIBLE_QUESTIONS,
    NUMERIC_HINTS,
    REPORTING_DATE,
    UPKEEP_QUESTIONS,
    ChoiceQuestion,
)

from built_to_last.engine import (
    acquisition_totals,
    depreciation_schedule_through_2030,
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

from built_to_last.progress import (
    SNAPSHOT_PARAM,
    activity_defaults,
    record_attempt,
    reset_saved_progress,
    restore_session_state,
    score_summary,
    stable_shuffle,
    sync_progress_query,
)

st.set_page_config(
    page_title="Built to Last?",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

UD_RED = "#CE0037"

UD_BLUE = "#003087"

INK = "#14213D"

MUTED = "#59677A"

BACKGROUND = "#F4F7FB"

SUCCESS = "#137A4B"

WARNING = "#986000"

GOLD = "#F3B61F"

APP_CSS = f"""
<style>
    :root {{
        --ud-red: {UD_RED};
        --ud-blue: {UD_BLUE};
        --ink: {INK};
        --muted: {MUTED};
        --background: {BACKGROUND};
        --success: {SUCCESS};
        --warning: {WARNING};
        --gold: {GOLD};
    }}

    .stApp {{ background: var(--background); }}
    [data-testid="stHeaderActionElements"] {{ display: none; }}
    [data-testid="stToolbar"] {{ visibility: hidden; height: 0; }}
    [data-testid="stDecoration"] {{ background: var(--ud-red); }}
    .block-container {{ max-width: 1160px; padding-top: 1.35rem; padding-bottom: 4rem; }}
    h1, h2, h3 {{ color: var(--ink); letter-spacing: -0.02em; }}
    p, li, label {{ color: var(--ink); }}

    .hero {{
        background:
            radial-gradient(circle at 92% 10%, rgba(243, 182, 31, 0.34), transparent 25%),
            linear-gradient(125deg, #001F55 0%, var(--ud-blue) 60%, #164E91 100%);
        border-top: 7px solid var(--ud-red);
        border-radius: 18px;
        box-shadow: 0 16px 38px rgba(0, 48, 135, 0.17);
        margin-bottom: 1rem;
        padding: 2rem 2.2rem 1.8rem;
    }}
    .hero-kicker {{ color: #FFFFFF; font-size: 0.8rem; font-weight: 850; letter-spacing: 0.13em; }}
    .hero h1 {{ color: #FFFFFF; font-size: clamp(2.15rem, 5vw, 3.7rem); margin: 0.15rem 0 0; }}
    .hero p {{ color: #F1F5FF; font-size: 1.08rem; margin: 0.65rem 0 0; max-width: 880px; }}
    .hero strong {{ color: var(--gold); }}

    .stage-row {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 0.34rem; margin: 0 0 1.3rem; }}
    .stage-pill {{
        background: #E6EAF1; border: 1px solid #D3D9E4; border-radius: 999px;
        color: #5C6879; font-size: 0.68rem; font-weight: 760; padding: 0.46rem 0.3rem; text-align: center;
    }}
    .stage-pill.complete {{ background: #E5F3EB; border-color: #A5D2B9; color: #0A653D; }}
    .stage-pill.active {{ background: var(--ud-red); border-color: var(--ud-red); color: #FFFFFF; }}

    .eyebrow {{ color: var(--ud-red); font-size: 0.78rem; font-weight: 850; letter-spacing: 0.1em; text-transform: uppercase; }}
    .lead {{ color: var(--muted); font-size: 1.07rem; max-width: 920px; }}
    .card {{
        background: #FFFFFF; border: 1px solid #D9E0EA; border-left: 7px solid var(--ud-blue);
        border-radius: 14px; box-shadow: 0 8px 22px rgba(20, 33, 61, 0.06);
        margin: 0.75rem 0 1rem; padding: 1.15rem 1.3rem;
    }}
    .card .document {{ color: var(--ud-blue); font-size: 0.78rem; font-weight: 850; letter-spacing: 0.06em; text-transform: uppercase; }}
    .card h3 {{ margin: 0.28rem 0 0.48rem; }}
    .card p {{ font-size: 1.04rem; margin: 0; }}

    .concept-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.72rem; margin: 1rem 0 1.3rem; }}
    .concept-card {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 13px; padding: 1rem; }}
    .concept-card strong {{ color: var(--ud-blue); display: block; margin: 0.2rem 0; }}
    .concept-number {{ color: var(--ud-red); font-size: 1.15rem; font-weight: 900; }}
    .concept-card span {{ color: var(--muted); font-size: 0.9rem; }}

    .metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.65rem; margin: 0.9rem 0 1.1rem; }}
    .metric-box {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 12px; padding: 0.85rem; text-align: center; }}
    .metric-box strong {{ color: var(--ud-blue); display: block; font-size: 1.3rem; }}
    .metric-box span {{ color: var(--muted); font-size: 0.8rem; }}

    .feedback-row {{
        align-items: flex-start; background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 10px;
        display: flex; gap: 1rem; justify-content: space-between; margin: 0.42rem 0; padding: 0.7rem 0.82rem;
    }}
    .feedback-row.correct {{ border-left: 5px solid var(--success); }}
    .feedback-row.review {{ border-left: 5px solid var(--warning); }}
    .feedback-label {{ font-weight: 780; }}
    .feedback-detail {{ color: var(--muted); font-size: 0.9rem; margin-top: 0.12rem; }}
    .feedback-value {{ font-variant-numeric: tabular-nums; text-align: right; }}

    .effect-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.65rem; margin: 0.7rem 0; }}
    .effect-box {{ background: #EEF4FF; border: 1px solid #C6D7F2; border-radius: 11px; padding: 0.82rem 0.95rem; }}
    .effect-box span {{ color: var(--muted); display: block; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; }}
    .effect-box strong {{ color: var(--ud-blue); display: block; font-size: 0.95rem; margin-top: 0.25rem; }}

    .formula {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 12px; margin: 0.7rem 0 1rem; padding: 0.95rem 1.1rem; }}
    .formula strong {{ color: var(--ud-blue); }}
    .bridge-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.72rem; margin: 0.85rem 0 1rem; }}
    .bridge-card {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 12px; padding: 0.95rem 1rem; }}
    .bridge-card.before {{ border-top: 5px solid var(--ud-blue); }}
    .bridge-card.after {{ border-top: 5px solid var(--ud-red); }}
    .bridge-label {{ color: var(--muted); font-size: 0.76rem; font-weight: 850; letter-spacing: 0.06em; text-transform: uppercase; }}
    .bridge-equation {{ color: var(--ink); font-size: 1.05rem; font-weight: 850; margin: 0.45rem 0 0.2rem; }}
    .bridge-caption {{ color: var(--muted); font-size: 0.84rem; }}
    .principle {{ background: #FFF5F7; border-left: 5px solid var(--ud-red); border-radius: 9px; margin: 0.7rem 0; padding: 0.82rem 0.95rem; }}
    .principle strong {{ color: var(--ud-red); }}

    .chain {{ align-items: stretch; display: grid; gap: 0.45rem; grid-template-columns: repeat(6, 1fr); margin: 1rem 0; }}
    .chain-step {{ background: #FFFFFF; border: 1px solid #D9E0EA; border-radius: 10px; color: var(--ud-blue); font-weight: 800; padding: 0.78rem; text-align: center; }}

    .stButton > button, .stFormSubmitButton > button {{ border-radius: 9px; font-weight: 760; min-height: 2.7rem; }}
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background: var(--ud-red); border-color: var(--ud-red); color: #FFFFFF; }}
    button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {{ background: var(--ud-red); border-color: var(--ud-red); color: #FFFFFF; }}
    button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p {{ color: #FFFFFF !important; }}

    @media (max-width: 820px) {{
        .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
        .hero {{ padding: 1.4rem 1.2rem; }}
        .stage-row {{ grid-template-columns: 1fr; }}
        .stage-pill {{ display: none; }}
        .stage-pill.active {{ display: block; }}
        .concept-grid, .metric-grid, .effect-grid, .bridge-grid, .chain {{ grid-template-columns: 1fr; }}
        .feedback-row {{ display: block; }}
        .feedback-value {{ margin-top: 0.3rem; text-align: left; }}
    }}
</style>
"""

STAGE_LABELS = (
    "Brief",
    "1. Acquire",
    "2. Later costs",
    "3. Depreciation",
    "4. Disposal",
    "5. Intangibles",
    "6. Analysis",
    "Complete",
)

def initialize_state() -> None:
    if "btl_restore_attempted" not in st.session_state:
        restored = restore_session_state(st.session_state, st.query_params.get(SNAPSHOT_PARAM))
        st.session_state.btl_restore_attempted = True
        if restored:
            st.session_state.btl_scroll_to_top = True
    for key, value in activity_defaults().items():
        if key not in st.session_state:
            st.session_state[key] = value

def restart_activity() -> None:
    reset_saved_progress(st.session_state, st.query_params)
    st.session_state.btl_scroll_to_top = True

def set_stage(stage: int) -> None:
    st.session_state.btl_stage = stage
    st.session_state.btl_scroll_to_top = True

def advance_item(index_key: str, count: int, next_stage: int) -> None:
    index = int(st.session_state[index_key])
    if index < count - 1:
        st.session_state[index_key] = index + 1
        st.session_state.btl_scroll_to_top = True
    else:
        set_stage(next_stage)

def selected_index(options: Sequence[str], selected: str | None) -> int | None:
    return list(options).index(selected) if selected in options else None

def escape_dollar_markdown(value: object) -> str:
    """Keep currency text from being rendered as inline math."""

    return str(value).replace("$", r"\$")

def save_choice_draft(group: str, item_id: str, widget_key: str) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.btl_choice_drafts.items()}
    group_drafts = dict(drafts[group])
    value = st.session_state.get(widget_key)
    if value is None:
        group_drafts.pop(item_id, None)
    else:
        group_drafts[item_id] = str(value)
    drafts[group] = group_drafts
    st.session_state.btl_choice_drafts = drafts

def clear_choice_draft(group: str, item_id: str) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.btl_choice_drafts.items()}
    group_drafts = dict(drafts[group])
    group_drafts.pop(item_id, None)
    drafts[group] = group_drafts
    st.session_state.btl_choice_drafts = drafts

def save_numeric_draft(group: str, field_key: str, widget_key: str) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.btl_numeric_drafts.items()}
    group_drafts = dict(drafts[group])
    group_drafts[field_key] = st.session_state[widget_key]
    drafts[group] = group_drafts
    st.session_state.btl_numeric_drafts = drafts

def clear_numeric_draft(group: str) -> None:
    drafts = {key: dict(value) for key, value in st.session_state.btl_numeric_drafts.items()}
    drafts[group] = {}
    st.session_state.btl_numeric_drafts = drafts

def render_scroll_reset() -> None:
    """Reset after navigation without overriding student-initiated scrolling."""

    if not st.session_state.pop("btl_scroll_to_top", False):
        return
    st.iframe(
        """
        <script>
        (() => {
          const parent = window.parent;
          const main = parent.document.querySelector('section[data-testid="stMain"]');
          if (!main) return;
          let cancelled = false;
          let finished = false;
          const scrollingKeys = new Set(['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' ']);
          const cancel = () => { cancelled = true; cleanup(); };
          const cancelKey = (event) => { if (scrollingKeys.has(event.key)) cancel(); };
          const cleanup = () => {
            parent.removeEventListener('wheel', cancel);
            parent.removeEventListener('touchstart', cancel);
            parent.removeEventListener('keydown', cancelKey);
          };
          const reset = () => {
            if (finished) return;
            finished = true;
            if (!cancelled) main.scrollTo({ top: 0, left: 0, behavior: 'auto' });
            cleanup();
          };
          parent.addEventListener('wheel', cancel, { passive: true });
          parent.addEventListener('touchstart', cancel, { passive: true });
          parent.addEventListener('keydown', cancelKey);
          parent.requestAnimationFrame(() => parent.requestAnimationFrame(reset));
          parent.setTimeout(reset, 120);
        })();
        </script>
        """,
        height=1,
        tab_index=-1,
    )

def render_hero() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">ASSET LIFECYCLE DECISION LAB</div>
          <h1>Built to Last?</h1>
          <p>Guide <strong>{escape(COMPANY_NAME)}</strong> from acquisition through analysis using account changes, ending balances, and financial-statement effects.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_stage_row() -> None:
    current = int(st.session_state.btl_stage)
    pills = []
    for index, label in enumerate(STAGE_LABELS):
        status = "complete" if index < current else "active" if index == current else ""
        pills.append(f'<div class="stage-pill {status}">{escape(label)}</div>')
    st.markdown(f'<div class="stage-row">{"".join(pills)}</div>', unsafe_allow_html=True)

def render_card(artifact: str, title: str, story: str) -> None:
    st.markdown(
        f"""
        <div class="card">
          <div class="document">{escape(artifact)}</div>
          <h3>{escape(title)}</h3>
          <p>{escape(story)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_feedback_row(label: str, correct: bool, detail: str, value: str = "") -> None:
    status = "correct" if correct else "review"
    symbol = "Correct" if correct else "Review"
    st.markdown(
        f"""
        <div class="feedback-row {status}">
          <div><div class="feedback-label">{escape(label)} - {symbol}</div><div class="feedback-detail">{escape(detail)}</div></div>
          <div class="feedback-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_effects(account_effect: str, statement_effect: str) -> None:
    st.markdown(
        f"""
        <div class="effect-grid">
          <div class="effect-box"><span>Account changes</span><strong>{escape(account_effect)}</strong></div>
          <div class="effect-box"><span>Financial statement effect</span><strong>{escape(statement_effect)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_briefing() -> None:
    st.markdown('<div class="eyebrow">Your assignment</div>', unsafe_allow_html=True)
    st.header("Follow one investment through its entire reporting life")
    st.markdown(
        "<p class='lead'>Gem City Adventure Works has opened a recreation center and is reviewing its long-lived investments through December 31, 2031. You will use purchase records, service invoices, a van schedule, a sale agreement, legal-rights documents, and performance figures. Each decision changes what the company can report next.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="chain">
          <div class="chain-step">Acquire</div>
          <div class="chain-step">Maintain or improve</div>
          <div class="chain-step">Allocate cost</div>
          <div class="chain-step">Dispose</div>
          <div class="chain-step">Classify intangibles</div>
          <div class="chain-step">Analyze results</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("At each stop, decide which accounts change, determine the resulting balances, and explain the financial-statement effect. You can revise each decision before moving on.")
    st.button("Begin the asset lifecycle", type="primary", width="stretch", on_click=set_stage, args=(1,))

def render_sequential_stage(
    *,
    eyebrow: str,
    heading: str,
    lead: str,
    questions: Sequence[ChoiceQuestion],
    index_key: str,
    response_key: str,
    widget_prefix: str,
    check_label: str,
    next_stage: int,
    next_label: str,
    completion_renderer: Callable[[], None] | None = None,
) -> None:
    st.markdown(f'<div class="eyebrow">{escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.header(heading)
    st.markdown(f"<p class='lead'>{escape(lead)}</p>", unsafe_allow_html=True)

    index = int(st.session_state[index_key])
    seed = int(st.session_state.btl_shuffle_seed)
    ordered_questions = list(questions)
    item = ordered_questions[index]
    responses = dict(st.session_state[response_key])
    saved = responses.get(item.id)
    widget_key = f"widget_{widget_prefix}_{item.id}"

    st.progress((index + 1) / len(ordered_questions), text=f"Decision {index + 1} of {len(ordered_questions)}")
    render_card(item.artifact, item.title, item.story)
    st.write(escape_dollar_markdown(item.prompt))

    result = evaluate_choice(item.id, saved) if saved is not None else None
    if result is not None and result["correct"]:
        st.success(escape_dollar_markdown(f"Correct. {result['explanation']}"))
        render_effects(str(result["account_effect"]), str(result["statement_effect"]))
    elif result is not None:
        st.warning("Review this decision and try again.")
        st.info(escape_dollar_markdown(f"Hint: {CHOICE_HINTS[item.id]}"))

    if result is not None and result["correct"]:
        if index == len(questions) - 1 and completion_renderer is not None:
            completion_renderer()
        st.button(
            next_label if index == len(questions) - 1 else "Continue",
            type="primary",
            width="stretch",
            on_click=advance_item,
            args=(index_key, len(ordered_questions), next_stage),
        )
        return

    if result is not None:
        st.info("Change your choice below, then check the revised decision.")

    draft = st.session_state.btl_choice_drafts[widget_prefix].get(item.id, saved)
    ordered_options = stable_shuffle(item.options, seed, f"{widget_prefix}-answer-order:{item.id}")
    selected = st.radio(
        "Choose the best response",
        ordered_options,
        index=selected_index(ordered_options, draft),
        format_func=escape_dollar_markdown,
        key=widget_key,
        on_change=save_choice_draft,
        args=(widget_prefix, item.id, widget_key),
    )
    button_label = "Check revised decision" if result is not None else check_label
    if st.button(button_label, type="primary", width="stretch"):
        if selected is None:
            st.warning("Choose a response before checking your decision.")
        else:
            selected = str(selected)
            responses[item.id] = selected
            st.session_state[response_key] = responses
            clear_choice_draft(widget_prefix, item.id)
            result = evaluate_choice(item.id, selected)
            record_attempt(st.session_state, f"choice:{item.id}", bool(result["correct"]))
            st.rerun()

def render_acquisition_summary() -> None:
    totals = acquisition_totals()
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{format_currency(totals['Land'])}</strong><span>Land</span></div>
          <div class="metric-box"><strong>{format_currency(totals['Land Improvements'])}</strong><span>Land Improvements</span></div>
          <div class="metric-box"><strong>{format_currency(totals['Building'])}</strong><span>Building</span></div>
          <div class="metric-box"><strong>{format_currency(totals['Equipment'])}</strong><span>Equipment</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_acquisition() -> None:
    render_sequential_stage(
        eyebrow="Step 1 of the asset lifecycle",
        heading="Build the historical-cost asset package",
        lead="The company paid $180,000 for land and $420,000 for a ready-to-use building. Both purchase prices are in the case file. Now evaluate the additional closing, site, equipment, and training costs.",
        questions=ACQUISITION_QUESTIONS,
        index_key="btl_acquisition_index",
        response_key="btl_acquisition_responses",
        widget_prefix="acquisition",
        check_label="Check the cost treatment",
        next_stage=2,
        next_label="Continue to later expenditures",
        completion_renderer=render_acquisition_summary,
    )

def render_lifecycle_summary() -> None:
    totals = lifecycle_totals()
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{format_currency(totals['Building'])}</strong><span>Ending Building cost</span></div>
          <div class="metric-box"><strong>{format_currency(totals['Equipment'])}</strong><span>Ending Equipment cost</span></div>
          <div class="metric-box"><strong>{format_currency(totals['Capitalized plant assets'])}</strong><span>Site and recreation asset cost</span></div>
          <div class="metric-box"><strong>{format_currency(totals['Current-period expense'])}</strong><span>Immediate expenses identified</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_upkeep() -> None:
    render_sequential_stage(
        eyebrow="Step 2 of the asset lifecycle",
        heading="Separate ordinary repairs from future benefits",
        lead="Use the nature of the work, its frequency, and its benefit period to determine whether an asset account or current expense increases.",
        questions=UPKEEP_QUESTIONS,
        index_key="btl_upkeep_index",
        response_key="btl_upkeep_responses",
        widget_prefix="upkeep",
        check_label="Check the expenditure",
        next_stage=3,
        next_label="Continue to depreciation",
        completion_renderer=render_lifecycle_summary,
    )

def render_depreciation() -> None:
    st.markdown('<div class="eyebrow">Step 3 of the asset lifecycle</div>', unsafe_allow_html=True)
    st.header("Allocate the van's cost using straight-line depreciation")
    st.markdown(
        "<p class='lead'>The delivery van cost $50,000, has a $5,000 expected salvage value and a five-year useful life, and was placed in service on April 1, 2028. Calculate the 2028 through 2030 balances using straight-line depreciation. Enter whole dollars.</p>",
        unsafe_allow_html=True,
    )

    submitted_before = bool(st.session_state.btl_depreciation_submitted)
    result = (
        evaluate_depreciation(st.session_state.btl_depreciation_values)
        if submitted_before
        else None
    )
    if result is not None:
        for key, label, _value in DEPRECIATION_FIELDS:
            field = result["fields"][key]
            render_feedback_row(
                label,
                bool(field["correct"]),
                "That balance follows from the van's cost and use period." if field["correct"] else NUMERIC_HINTS["depreciation"][key],
                f"Submitted {format_currency(field['submitted'])}",
            )

    if result is None or not result["correct"]:
        if result is not None:
            st.info("Update the amounts below, then check the revised schedule.")
        previous = dict(st.session_state.btl_depreciation_values)
        drafts = dict(st.session_state.btl_numeric_drafts["depreciation"])
        entered = {}
        for key, label, _expected in DEPRECIATION_FIELDS:
            entered[key] = st.number_input(
                label,
                min_value=0,
                max_value=1_000_000,
                value=int(drafts.get(key, previous.get(key, 0))),
                step=250,
                key=f"widget_depreciation_value_{key}",
                on_change=save_numeric_draft,
                args=("depreciation", key, f"widget_depreciation_value_{key}"),
            )
        button_label = "Check revised depreciation amounts" if result is not None else "Check the depreciation amounts"
        if st.button(button_label, type="primary", width="stretch"):
            values = {key: int(value) for key, value in entered.items()}
            st.session_state.btl_depreciation_values = values
            st.session_state.btl_depreciation_submitted = True
            clear_numeric_draft("depreciation")
            result = evaluate_depreciation(values)
            for key, _label, _expected in DEPRECIATION_FIELDS:
                record_attempt(st.session_state, f"depreciation:{key}", bool(result["fields"][key]["correct"]))
            st.rerun()
        return

    st.success("The schedule now carries cost allocation from the partial first year through the 2030 ending balances.")
    st.dataframe(depreciation_schedule_through_2030(), hide_index=True, width="stretch")
    st.markdown(
        """
        <div class="bridge-grid">
          <div class="bridge-card before"><div class="bridge-label">Start of 2030</div><div class="bridge-equation">$50,000 cost - $15,750 accumulated depreciation = $34,250 book value</div><div class="bridge-caption">The asset cost stays in Equipment while the contra-asset balance carries prior allocation.</div></div>
          <div class="bridge-card after"><div class="bridge-label">End of 2030</div><div class="bridge-equation">$50,000 cost - $24,750 accumulated depreciation = $25,250 book value</div><div class="bridge-caption">Assets and equity each decrease $9,000 through the year's depreciation expense.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_sequential_stage(
        eyebrow="Depreciation interpretation",
        heading="Explain what the balances mean",
        lead="Now connect the calculation to its account and financial-statement effects.",
        questions=DEPRECIATION_QUESTIONS,
        index_key="btl_depreciation_index",
        response_key="btl_depreciation_responses",
        widget_prefix="depreciation",
        check_label="Check the depreciation reasoning",
        next_stage=4,
        next_label="Continue to disposal",
    )

def render_disposal() -> None:
    st.markdown('<div class="eyebrow">Step 4 of the asset lifecycle</div>', unsafe_allow_html=True)
    st.header("Update the balances before selling the van")
    st.markdown(
        f"<p class='lead'>On {escape(DISPOSAL_FACTS['sale_date'])}, the company sells the van for {format_currency(DISPOSAL_FACTS['cash_proceeds'])}. Bring depreciation through the sale date, then compare proceeds with the updated book value. Enter whole dollars.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{format_currency(DISPOSAL_FACTS['cost'])}</strong><span>Van cost</span></div>
          <div class="metric-box"><strong>{format_currency(DISPOSAL_FACTS['accumulated_before_2031'])}</strong><span>Accumulated depreciation before 2031</span></div>
          <div class="metric-box"><strong>{format_currency(DISPOSAL_FACTS['annual_depreciation'])}</strong><span>Annual depreciation</span></div>
          <div class="metric-box"><strong>{format_currency(DISPOSAL_FACTS['cash_proceeds'])}</strong><span>Sale proceeds</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    submitted_before = bool(st.session_state.btl_disposal_submitted)
    result = evaluate_disposal(st.session_state.btl_disposal_values) if submitted_before else None
    if result is not None:
        for key, label, _value in DISPOSAL_FIELDS:
            field = result["fields"][key]
            render_feedback_row(
                label,
                bool(field["correct"]),
                "That balance is consistent with the sale-date analysis." if field["correct"] else NUMERIC_HINTS["disposal"][key],
                f"Submitted {format_currency(field['submitted'])}",
            )

    if result is None or not result["correct"]:
        if result is not None:
            st.info("Update the amounts below, then check the revised disposal analysis.")
        previous = dict(st.session_state.btl_disposal_values)
        drafts = dict(st.session_state.btl_numeric_drafts["disposal"])
        entered = {}
        for key, label, _expected in DISPOSAL_FIELDS:
            entered[key] = st.number_input(
                label,
                min_value=0,
                max_value=1_000_000,
                value=int(drafts.get(key, previous.get(key, 0))),
                step=250,
                key=f"widget_disposal_value_{key}",
                on_change=save_numeric_draft,
                args=("disposal", key, f"widget_disposal_value_{key}"),
            )
        button_label = "Check revised disposal amounts" if result is not None else "Check the disposal amounts"
        if st.button(button_label, type="primary", width="stretch"):
            values = {key: int(value) for key, value in entered.items()}
            st.session_state.btl_disposal_values = values
            st.session_state.btl_disposal_submitted = True
            clear_numeric_draft("disposal")
            result = evaluate_disposal(values)
            for key, _label, _expected in DISPOSAL_FIELDS:
                record_attempt(st.session_state, f"disposal:{key}", bool(result["fields"][key]["correct"]))
            st.rerun()
        return

    st.success("The van's book value is current, so the sale proceeds can be compared with the correct carrying amount.")
    st.markdown(
        """
        <div class="bridge-grid">
          <div class="bridge-card before"><div class="bridge-label">Immediately before the sale</div><div class="bridge-equation">$50,000 cost - $29,250 accumulated depreciation = $20,750 net van</div><div class="bridge-caption">The company first updates depreciation so the comparison uses the sale-date book value.</div></div>
          <div class="bridge-card after"><div class="bridge-label">Immediately after the sale</div><div class="bridge-equation">$18,000 cash received - $20,750 book value = $2,750 loss</div><div class="bridge-caption">Assets decrease $2,750 = liabilities change $0 + equity decreases $2,750.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_sequential_stage(
        eyebrow="Disposal interpretation",
        heading="Explain how assets leave the company",
        lead="Use the updated book value to explain how each disposal changes accounts and reported results.",
        questions=DISPOSAL_QUESTIONS,
        index_key="btl_disposal_index",
        response_key="btl_disposal_responses",
        widget_prefix="disposal",
        check_label="Check the disposal reasoning",
        next_stage=5,
        next_label="Continue to intangible assets",
    )

def render_intangibles() -> None:
    render_sequential_stage(
        eyebrow="Step 5 of the asset lifecycle",
        heading="Account for rights and competitive advantages",
        lead="Determine the account change first, then decide whether the cost is allocated over a limited life, remains unamortized while indefinite, or becomes current expense.",
        questions=INTANGIBLE_QUESTIONS,
        index_key="btl_intangible_index",
        response_key="btl_intangible_responses",
        widget_prefix="intangible",
        check_label="Check the intangible treatment",
        next_stage=6,
        next_label="Continue to statement analysis",
    )

def render_analysis() -> None:
    st.markdown('<div class="eyebrow">Step 6 of the asset lifecycle</div>', unsafe_allow_html=True)
    st.header("Connect the asset base to performance")
    st.markdown(
        f"<p class='lead'>At {escape(REPORTING_DATE)}, the company reports the figures below. Calculate profit margin, asset turnover, and return on assets. Round each percentage and turnover measure to two decimal places.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{format_currency(ANALYSIS_FACTS['net_income'])}</strong><span>Net income</span></div>
          <div class="metric-box"><strong>{format_currency(ANALYSIS_FACTS['net_sales'])}</strong><span>Net sales</span></div>
          <div class="metric-box"><strong>{format_currency(ANALYSIS_FACTS['average_total_assets'])}</strong><span>Average total assets</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    submitted_before = bool(st.session_state.btl_analysis_submitted)
    result = evaluate_analysis(st.session_state.btl_analysis_values) if submitted_before else None
    if result is not None:
        for key, label, _value in ANALYSIS_FIELDS:
            field = result["fields"][key]
            unit = " times" if key == "asset_turnover" else "%"
            render_feedback_row(
                label,
                bool(field["correct"]),
                "That measure fits the reported amounts." if field["correct"] else NUMERIC_HINTS["analysis"][key],
                f"Submitted {float(field['submitted']):.2f}{unit}",
            )

    if result is None or not result["correct"]:
        if result is not None:
            st.info("Update the measures below, then check the revised performance analysis.")
        previous = dict(st.session_state.btl_analysis_values)
        drafts = dict(st.session_state.btl_numeric_drafts["analysis"])
        entered = {}
        for key, label, _expected in ANALYSIS_FIELDS:
            unit = " (times)" if key == "asset_turnover" else " (%)"
            entered[key] = st.number_input(
                f"{label}{unit}",
                min_value=0.0,
                max_value=100.0,
                value=float(drafts.get(key, previous.get(key, 0.0))),
                step=0.1,
                format="%.2f",
                key=f"widget_analysis_value_{key}",
                on_change=save_numeric_draft,
                args=("analysis", key, f"widget_analysis_value_{key}"),
            )
        button_label = "Check revised ratios" if result is not None else "Check the ratios"
        if st.button(button_label, type="primary", width="stretch"):
            values = {key: float(value) for key, value in entered.items()}
            st.session_state.btl_analysis_values = values
            st.session_state.btl_analysis_submitted = True
            clear_numeric_draft("analysis")
            result = evaluate_analysis(values)
            for key, _label, _expected in ANALYSIS_FIELDS:
                record_attempt(st.session_state, f"analysis:{key}", bool(result["fields"][key]["correct"]))
            st.rerun()
        return

    st.success("The company earns 12 cents for each dollar of average assets, produced by an 8% margin and 1.50 times turnover.")
    render_sequential_stage(
        eyebrow="Presentation and interpretation",
        heading="Turn the numbers into useful reporting",
        lead="Finish by connecting asset presentation, disclosures, and management strategy.",
        questions=ANALYSIS_QUESTIONS,
        index_key="btl_analysis_index",
        response_key="btl_analysis_responses",
        widget_prefix="analysis",
        check_label="Check the reporting analysis",
        next_stage=7,
        next_label="Complete the case",
    )

def render_completion() -> None:
    score = score_summary(st.session_state)
    totals = lifecycle_totals()
    disposal = expected_disposal_values()
    ratios = expected_analysis_values()
    st.markdown('<div class="eyebrow">Case debrief</div>', unsafe_allow_html=True)
    st.header("The asset lifecycle is complete")
    st.success("Asset lifecycle complete. You connected evidence, account balances, financial statements, and performance analysis.")
    st.markdown(
        """
        <div class="chain">
          <div class="chain-step">Historical cost</div>
          <div class="chain-step">Later expenditures</div>
          <div class="chain-step">Cost allocation</div>
          <div class="chain-step">Disposal</div>
          <div class="chain-step">Intangible rights</div>
          <div class="chain-step">Return on assets</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-box"><strong>{format_currency(totals['Capitalized plant assets'])}</strong><span>Site and recreation asset cost</span></div>
          <div class="metric-box"><strong>{format_currency(expected_depreciation_values()['annual_depreciation'])}</strong><span>Full-year van depreciation</span></div>
          <div class="metric-box"><strong>{format_currency(disposal['book_value'])}</strong><span>Van book value at sale</span></div>
          <div class="metric-box"><strong>{ratios['return_on_assets']:.0f}%</strong><span>Return on assets</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("What the records now show")
    st.markdown(
        escape_dollar_markdown(
            "1. **Acquisition and later work.** Land ends at $191,000, including $5,000 of assumed property taxes still payable. "
            "The site and recreation assets total $849,000 at cost after the building and equipment additions. "
            "Training and ordinary repairs created $10,200 of expense when incurred rather than additional asset cost.\n"
            "2. **Allocation.** The van's $50,000 cost stays in Equipment while accumulated depreciation reaches $24,750 by the end of 2030. "
            "Its $25,250 book value is allocated cost, not an estimate of its selling price.\n"
            "3. **Disposal.** Another $4,500 of depreciation brings the van's sale-date book value to $20,750. "
            "The $18,000 cash proceeds replace part of that asset, and the $2,750 loss reduces 2031 income and equity.\n"
            "4. **Rights and performance.** The successful patent defense raises Patent from $60,000 to $72,000 before later amortization; "
            "the $75,000 research and development spending is a current expense. "
            "At the end of 2031, an 8% profit margin and 1.50-times asset turnover produce a 12% return on assets."
        )
    )
    st.subheader("Discuss the decisions")
    with st.expander("Why did the unpaid property taxes increase Land but not Cash paid at closing?"):
        st.write(escape_dollar_markdown(
            "The company assumed a $5,000 obligation as part of acquiring the site. Land includes that amount, "
            "while Property Taxes Payable increases $5,000. The separate $6,000 closing costs reduced Cash."
        ))
    with st.expander("Why can an addition and an ordinary repair have different effects on current income?"):
        st.write(
            "An addition creates capacity or benefit beyond the current period, so it raises the asset balance and affects income through later cost allocation. "
            "An ordinary repair maintains existing service and raises current-period expense."
        )
    with st.expander("What would need to happen for the new attraction to improve return on assets?"):
        st.write(
            "It must generate enough additional net income relative to the larger average asset base. "
            "Managers should watch both profit per sales dollar and sales generated per asset dollar as demand develops."
        )
    st.caption(
        f"First-pass evidence: {score['correct']} of {score['attempted']} attempted checkpoints correct; "
        f"{score['revisions']} revision(s). Final mastery: complete."
    )
    st.button("Start over", width="stretch", on_click=restart_activity)
