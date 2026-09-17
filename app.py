import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from supabase import create_client
import json
import html


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="IPQC Finding Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# COLORS
# ============================================================

BG = "#090E17"
CARD = "#111B2D"
BORDER = "#2A3C59"

TEXT = "#F1F5F9"
MUTED = "#9FB0CA"

CYAN = "#22D3EE"
BLUE = "#6366F1"
PURPLE = "#9B7BF3"
TEAL = "#1489A8"

GREEN = "#22C55E"
ORANGE = "#F59E0B"
RED = "#EF4444"


AREA_COLORS = {
    "DP": CYAN,
    "FOL": BLUE,
    "MOL": TEAL,
    "EOL": ORANGE
}

SHIFT_COLORS = {
    "A": CYAN,
    "B": BLUE,
    "C": TEAL,
    "D": PURPLE
}

TIME_COLORS = {
    "DAY": ORANGE,
    "NIGHT": "#475569"
}

CATEGORY_COLORS = {
    "Method / Handling": CYAN,
    "Machine / Facility": RED,
    "Material / Product": ORANGE,
    "Document / Record": PURPLE,
    "Personnel Compliance": GREEN
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background-color: {BG};
    }}

    .block-container {{
        max-width: 1800px;
        padding-top: 3.5rem !important;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 2rem;
    }}

    h1 {{
        color: {TEXT};
        font-size: 28px !important;
        line-height: 1.3 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    h2, h3 {{
        color: {TEXT};
    }}

    p {{
        color: {MUTED};
    }}

    div[data-testid="stPlotlyChart"] {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {CARD};
    }}

    div[data-testid="stVerticalBlock"] {{
        gap: 0.8rem;
    }}

    .ai-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 20px 22px;
        min-height: 340px;
        box-sizing: border-box;
    }}

    .ai-title {{
        color: {MUTED};
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1.2px;
        margin-bottom: 15px;
    }}

    .lowlight-header {{
        background: rgba(239, 68, 68, 0.10);
        border: 1px solid rgba(239, 68, 68, 0.50);
        border-radius: 7px;
        padding: 10px 13px;
        color: {RED};
        font-weight: 700;
        margin-bottom: 15px;
    }}

    .highlight-header {{
        background: rgba(34, 197, 94, 0.10);
        border: 1px solid rgba(34, 197, 94, 0.45);
        border-radius: 7px;
        padding: 10px 13px;
        color: {GREEN};
        font-weight: 700;
        margin-bottom: 15px;
    }}

    .ai-label {{
        color: {TEXT};
        font-size: 13px;
        font-weight: 700;
        margin-top: 13px;
        margin-bottom: 4px;
    }}

    .ai-text {{
        color: {MUTED};
        font-size: 13px;
        line-height: 1.55;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def init_supabase():

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = init_supabase()


# ============================================================
# LOAD FINDINGS
# ============================================================

@st.cache_data(ttl=60)
def load_findings():

    response = (
        supabase
        .table("Findings")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


try:

    df = load_findings()

except Exception as e:

    st.error(
        f"Unable to load findings from Supabase: {e}"
    )

    st.stop()


# ============================================================
# CURRENT MALAYSIA TIME
# ============================================================

current_time = datetime.now(
    ZoneInfo("Asia/Kuala_Lumpur")
)


# ============================================================
# HEADER
# ============================================================

header1, header2 = st.columns(
    [4, 1]
)


with header1:

    st.title(
        "IPQC Finding Monitoring Dashboard"
    )

    st.caption(
        "Total Summary"
    )


with header2:

    st.markdown(
        f"""
<div style="text-align:right; color:{MUTED}; font-size:13px; padding-top:10px;">
Last Updated<br>
<b style="color:{TEXT};">
{current_time.strftime("%d-%b-%Y %H:%M")}
</b>
</div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# EMPTY DATABASE
# ============================================================

if df.empty:

    st.info(
        "No findings recorded yet. "
        "Submit findings through the IPQC Finding Entry system."
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

df["finding_datetime_parsed"] = pd.to_datetime(
    df["finding_datetime"],
    format="%d-%b-%Y %H:%M:%S",
    errors="coerce"
)


df["status_clean"] = (
    df["status"]
    .fillna("Open")
    .astype(str)
    .str.strip()
    .str.title()
)


# ============================================================
# SHIFT
# ============================================================

df["shift_letter"] = (
    df["shift"]
    .fillna("")
    .astype(str)
    .str.split(" - ")
    .str[0]
    .str.strip()
)


df["shift_type"] = (
    df["shift"]
    .fillna("")
    .astype(str)
    .str.split(" - ")
    .str[-1]
    .str.strip()
    .str.upper()
)


# ============================================================
# AGING
# ============================================================

today = pd.Timestamp(
    current_time.date()
)


df["aging_days"] = (
    today
    -
    df["finding_datetime_parsed"].dt.normalize()
).dt.days


df["aging_days"] = (
    df["aging_days"]
    .fillna(0)
    .clip(lower=0)
)


# ============================================================
# ISO WORK WEEK
# ============================================================

df["week_number"] = (
    df["finding_datetime_parsed"]
    .dt
    .isocalendar()
    .week
)


df["week_year"] = (
    df["finding_datetime_parsed"]
    .dt
    .isocalendar()
    .year
)


df["work_week"] = (
    "WW"
    +
    df["week_number"]
    .astype(str)
    .str
    .zfill(2)
)


# ============================================================
# SHORT CATEGORY NAME
# ============================================================

def shorten_category(category):

    if pd.isna(category):
        return "Unknown"

    category = str(category).strip()

    if "Method / Handling" in category:
        return "Method / Handling"

    elif "Machine / Facility" in category:
        return "Machine / Facility"

    elif "Material / Product" in category:
        return "Material / Product"

    elif "Document / Record" in category:
        return "Document / Record"

    elif "Personnel Compliance" in category:
        return "Personnel Compliance"

    return category


df["category_short"] = (
    df["category"]
    .apply(shorten_category)
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.title(
    "Dashboard Filters"
)


area_options = sorted(
    df["area"]
    .dropna()
    .unique()
    .tolist()
)


selected_area = st.sidebar.multiselect(
    "Area",
    area_options,
    default=area_options
)


category_options = sorted(
    df["category_short"]
    .dropna()
    .unique()
    .tolist()
)


selected_category = st.sidebar.multiselect(
    "Category",
    category_options,
    default=category_options
)


shift_options = sorted(
    df["shift_letter"]
    .dropna()
    .unique()
    .tolist()
)


selected_shift = st.sidebar.multiselect(
    "Shift",
    shift_options,
    default=shift_options
)


status_options = sorted(
    df["status_clean"]
    .dropna()
    .unique()
    .tolist()
)


selected_status = st.sidebar.multiselect(
    "Status",
    status_options,
    default=status_options
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    df["area"].isin(selected_area)
    &
    df["category_short"].isin(selected_category)
    &
    df["shift_letter"].isin(selected_shift)
    &
    df["status_clean"].isin(selected_status)
].copy()


if filtered_df.empty:

    st.warning(
        "No findings match the selected filters."
    )

    st.stop()


# ============================================================
# TOTAL CASES
# ============================================================

total_cases = len(
    filtered_df
)


# ============================================================
# COMMON CHART STYLE
# ============================================================

def style_chart(fig):

    fig.update_layout(
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,

        font=dict(
            color=TEXT,
            size=12
        ),

        title=dict(
            font=dict(
                color=MUTED,
                size=15
            ),
            x=0.04,
            xanchor="left"
        ),

        margin=dict(
            l=35,
            r=25,
            t=55,
            b=55
        )
    )

    return fig


BOTTOM_LEGEND = dict(
    orientation="h",
    yanchor="top",
    y=-0.03,
    xanchor="center",
    x=0.5,
    font=dict(
        size=10
    )
)


# ============================================================
# ROW 1
# ============================================================

row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(
    [1, 1, 1, 1]
)


# ============================================================
# TOTAL CASES
# ============================================================

total_chart = go.Figure(
    data=[
        go.Pie(
            values=[total_cases],
            labels=["Total Cases"],
            hole=0.67,
            marker=dict(
                colors=[GREEN]
            ),
            textinfo="none",
            hovertemplate=(
                f"Total Cases: {total_cases}"
                "<extra></extra>"
            )
        )
    ]
)


total_chart.add_annotation(
    text=f"<b>{total_cases}</b>",
    x=0.5,
    y=0.5,
    showarrow=False,
    font=dict(
        size=28,
        color=GREEN
    )
)


total_chart.update_layout(
    title="● TOTAL CASES — OVERALL",
    showlegend=False,
    height=290
)


style_chart(
    total_chart
)


with row1_col1:

    st.plotly_chart(
        total_chart,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ============================================================
# SHIFT DISTRIBUTION
# ============================================================

shift_data = (
    filtered_df
    .groupby("shift_letter")
    .size()
    .reset_index(name="Cases")
)


shift_chart = px.pie(
    shift_data,
    names="shift_letter",
    values="Cases",
    hole=0.58,
    color="shift_letter",
    color_discrete_map=SHIFT_COLORS
)


shift_chart.update_traces(
    textinfo="none",
    hovertemplate=(
        "Shift %{label}<br>"
        "Cases: %{value}<br>"
        "%{percent}"
        "<extra></extra>"
    )
)


shift_chart.update_layout(
    title="● SHIFT DISTRIBUTION (%) — OVERALL",
    height=290,
    legend=BOTTOM_LEGEND
)


style_chart(
    shift_chart
)


with row1_col2:

    st.plotly_chart(
        shift_chart,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ============================================================
# TIME DISTRIBUTION
# ============================================================

time_data = (
    filtered_df
    .groupby("shift_type")
    .size()
    .reset_index(name="Cases")
)


time_chart = px.pie(
    time_data,
    names="shift_type",
    values="Cases",
    hole=0.58,
    color="shift_type",
    color_discrete_map=TIME_COLORS
)


time_chart.update_traces(
    textinfo="none",
    hovertemplate=(
        "%{label}<br>"
        "Cases: %{value}<br>"
        "%{percent}"
        "<extra></extra>"
    )
)


time_chart.update_layout(
    title="● TIME DISTRIBUTION (%) — OVERALL",
    height=290,
    legend=BOTTOM_LEGEND
)


style_chart(
    time_chart
)


with row1_col3:

    st.plotly_chart(
        time_chart,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ============================================================
# CATEGORY DISTRIBUTION
# ============================================================

category_data = (
    filtered_df
    .groupby("category_short")
    .size()
    .reset_index(name="Cases")
)


category_chart = px.pie(
    category_data,
    names="category_short",
    values="Cases",
    color="category_short",
    color_discrete_map=CATEGORY_COLORS
)


category_chart.update_traces(
    textinfo="none",
    hovertemplate=(
        "%{label}<br>"
        "Cases: %{value}<br>"
        "%{percent}"
        "<extra></extra>"
    )
)


category_chart.update_layout(
    title="● FINDING CATEGORY (%) — OVERALL",
    height=290,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.03,
        xanchor="center",
        x=0.5,
        font=dict(
            size=9
        )
    )
)


style_chart(
    category_chart
)


with row1_col4:

    st.plotly_chart(
        category_chart,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# ============================================================
# ROW 2
# ============================================================

row2_col1, row2_col2 = st.columns(
    [1.65, 1]
)


# ============================================================
# WEEKLY FINDING TREND
# ============================================================

current_date = current_time.date()


current_week_monday = (
    current_date
    -
    timedelta(
        days=current_date.weekday()
    )
)


latest_10_weeks = []


for weeks_ago in range(9, -1, -1):

    week_date = (
        current_week_monday
        -
        timedelta(
            weeks=weeks_ago
        )
    )

    iso_year, iso_week, _ = (
        week_date.isocalendar()
    )

    latest_10_weeks.append(
        {
            "week_year": iso_year,
            "week_number": iso_week,
            "work_week": f"WW{iso_week:02d}"
        }
    )


week_template = pd.DataFrame(
    latest_10_weeks
)


weekly_counts = (
    filtered_df
    .dropna(
        subset=[
            "week_year",
            "week_number"
        ]
    )
    .groupby(
        [
            "week_year",
            "week_number"
        ]
    )
    .size()
    .reset_index(
        name="Cases"
    )
)


week_template["week_year"] = (
    week_template["week_year"]
    .astype(int)
)


week_template["week_number"] = (
    week_template["week_number"]
    .astype(int)
)


weekly_counts["week_year"] = (
    weekly_counts["week_year"]
    .astype(int)
)


weekly_counts["week_number"] = (
    weekly_counts["week_number"]
    .astype(int)
)


weekly_data = (
    week_template
    .merge(
        weekly_counts,
        on=[
            "week_year",
            "week_number"
        ],
        how="left"
    )
)


weekly_data["Cases"] = (
    weekly_data["Cases"]
    .fillna(0)
    .astype(int)
)


weekly_chart = go.Figure()


weekly_chart.add_trace(
    go.Bar(
        x=weekly_data["work_week"],
        y=weekly_data["Cases"],
        name="Total Findings",
        marker_color=ORANGE,
        text=weekly_data["Cases"],
        textposition="outside",
        hovertemplate=(
            "%{x}<br>"
            "Findings: %{y}"
            "<extra></extra>"
        )
    )
)


weekly_chart.add_trace(
    go.Scatter(
        x=weekly_data["work_week"],
        y=weekly_data["Cases"],
        name="Finding Trend",
        mode="lines+markers",
        line=dict(
            color=CYAN,
            width=3
        ),
        marker=dict(
            size=7
        ),
        hovertemplate=(
            "%{x}<br>"
            "Findings: %{y}"
            "<extra></extra>"
        )
    )
)


weekly_chart.update_layout(
    title="● WEEKLY FINDING TREND — LATEST 10 WEEKS",
    height=315,
    xaxis_title="",
    yaxis_title="Cases",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.01,
        xanchor="center",
        x=0.55,
        font=dict(
            size=10
        )
    ),
    xaxis=dict(
        gridcolor="#334155",
        categoryorder="array",
        categoryarray=weekly_data[
            "work_week"
        ].tolist()
    ),
    yaxis=dict(
        gridcolor="#475569",
        rangemode="tozero",
        dtick=1
    )
)


style_chart(
    weekly_chart
)


with row2_col1:

    st.plotly_chart(
        weekly_chart,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )


# ============================================================
# FINDINGS BY AREA
# ============================================================

area_order = [
    "DP",
    "FOL",
    "MOL",
    "EOL"
]


area_data = (
    filtered_df
    .groupby("area")
    .size()
    .reindex(
        area_order,
        fill_value=0
    )
    .reset_index(
        name="Cases"
    )
)


area_chart = go.Figure()


area_chart.add_trace(
    go.Bar(
        x=area_data["Cases"],
        y=area_data["area"],
        orientation="h",
        marker=dict(
            color=[
                AREA_COLORS.get(
                    area,
                    CYAN
                )
                for area
                in area_data["area"]
            ]
        ),
        text=area_data["Cases"],
        textposition="outside",
        hovertemplate=(
            "%{y}<br>"
            "Cases: %{x}"
            "<extra></extra>"
        )
    )
)


area_chart.update_layout(
    title="● FINDINGS BY AREA — OVERALL",
    height=315,
    xaxis_title="Cases",
    yaxis_title="",
    showlegend=False,
    xaxis=dict(
        gridcolor="#475569",
        rangemode="tozero",
        dtick=1
    ),
    yaxis=dict(
        categoryorder="array",
        categoryarray=[
            "EOL",
            "MOL",
            "FOL",
            "DP"
        ]
    )
)


style_chart(
    area_chart
)


with row2_col2:

    st.plotly_chart(
        area_chart,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )


# ============================================================
# MANAGEMENT INSIGHTS
#
# IMPORTANT:
# OpenAI is called ONLY when the button is clicked.
# ============================================================

@st.cache_resource
def get_ai_summary_store():

    return {}


ai_summary_store = (
    get_ai_summary_store()
)


# ============================================================
# CURRENT WORK WEEK
# ============================================================

current_iso_year, current_iso_week, _ = (
    current_date.isocalendar()
)


current_work_week = (
    f"WW{current_iso_week:02d}"
)


# ============================================================
# CURRENT WW FINDINGS
# ============================================================

current_week_df = filtered_df[
    (
        filtered_df["week_year"]
        == current_iso_year
    )
    &
    (
        filtered_df["week_number"]
        == current_iso_week
    )
].copy()


# ============================================================
# HISTORICAL FINDINGS
# ============================================================

historical_df = filtered_df[
    (
        filtered_df["week_year"]
        < current_iso_year
    )
    |
    (
        (
            filtered_df["week_year"]
            == current_iso_year
        )
        &
        (
            filtered_df["week_number"]
            < current_iso_week
        )
    )
].copy()


# ============================================================
# CURRENT WW STATISTICS
# ============================================================

current_total = len(
    current_week_df
)


current_open = len(
    current_week_df[
        current_week_df["status_clean"]
        == "Open"
    ]
)


current_closed = len(
    current_week_df[
        current_week_df["status_clean"]
        == "Closed"
    ]
)


current_area_counts = (
    current_week_df["area"]
    .value_counts()
    .reindex(
        area_order,
        fill_value=0
    )
    .to_dict()
)


current_category_counts = (
    current_week_df["category_short"]
    .value_counts()
    .to_dict()
)


current_shift_counts = (
    current_week_df["shift_letter"]
    .value_counts()
    .to_dict()
)


# ============================================================
# CURRENT WW RECORDS FOR AI
# ============================================================

AI_COLUMNS = [
    "finding_datetime",
    "area",
    "station",
    "equipment_id",
    "category_short",
    "finding_description",
    "interview_result",
    "containment_action",
    "status_clean"
]


current_ai_df = current_week_df[
    [
        column
        for column in AI_COLUMNS
        if column in current_week_df.columns
    ]
].copy()


current_records = (
    current_ai_df
    .fillna("")
    .to_dict(
        orient="records"
    )
)


# ============================================================
# HISTORICAL RECORDS FOR AI
# ============================================================

HISTORY_COLUMNS = [
    "work_week",
    "finding_datetime",
    "area",
    "station",
    "equipment_id",
    "category_short",
    "finding_description",
    "interview_result",
    "containment_action",
    "status_clean"
]


historical_ai_df = (
    historical_df
    .sort_values(
        "finding_datetime_parsed",
        ascending=False
    )
    .head(150)
)


historical_ai_df = historical_ai_df[
    [
        column
        for column in HISTORY_COLUMNS
        if column in historical_ai_df.columns
    ]
].copy()


historical_records = (
    historical_ai_df
    .fillna("")
    .to_dict(
        orient="records"
    )
)


# ============================================================
# AI PAYLOAD
# ============================================================

ai_payload = {

    "current_work_week":
        current_work_week,

    "current_week_statistics": {

        "total_findings":
            current_total,

        "open_findings":
            current_open,

        "closed_findings":
            current_closed,

        "area_counts":
            current_area_counts,

        "category_counts":
            current_category_counts,

        "shift_counts":
            current_shift_counts
    },

    "current_week_findings":
        current_records,

    "historical_findings":
        historical_records
}


payload_json = json.dumps(
    ai_payload,
    ensure_ascii=False,
    default=str
)


# ============================================================
# GENERATE AI SUMMARY
# ============================================================

def generate_new_ai_summary(
    data_payload
):

    from openai import OpenAI

    client = OpenAI(
        api_key=st.secrets[
            "OPENAI_API_KEY"
        ]
    )


    prompt = f"""
You are supporting an IPQC management dashboard for a semiconductor
assembly operation.

The current work week is {current_work_week}.

Analyze the supplied IPQC data and generate:

1. LOW LIGHT / KEY OBSERVATION
2. PAST OCCURRENCE
3. RECOMMENDATION
4. HIGHLIGHT

RULES:

- Observation must summarize only findings from the current work week.
- Highlight must summarize only positive from the current work week.
- Historical findings are provided only to determine whether a similar
  issue occurred previously.
- Do not summarize historical findings as current-week findings.
- Do not invent root causes.
- Do not invent corrective actions.
- Do not invent past occurrences.
- Do not consider two findings similar merely because they have the
  same broad category.
- When identifying a similar historical occurrence, consider the
  finding description, issue mechanism, process, station and equipment.
- If a reasonably similar historical occurrence exists, state the
  previous work week and relevant area/station.
- If there is no reasonably similar historical occurrence, state:
  "No similar historical occurrence identified."
- Recommendation must be practical for IPQC, Quality, Production
  or Process Engineering follow-up.
- Recommendations may include verification, investigation,
  recurrence review, containment verification, corrective-action
  review or effectiveness verification.
- Do not state that a previous corrective action failed unless the
  supplied records provide evidence for that conclusion.
- Zero findings means only "No findings recorded".
  Do not interpret zero findings as proof of good compliance or
  process performance.
- Use concise management-level wording.
- Do not use markdown.
- Return ONLY valid JSON.

Return exactly this structure:

{{
    "observation": "Maximum 70 words",
    "past_occurrence": "Maximum 50 words",
    "recommendation": "Maximum 60 words",
    "highlight": "Maximum 70 words"
}}

DATA:

{data_payload}
"""


    model_name = st.secrets.get(
        "OPENAI_MODEL",
        "gpt-5.6-luna"
    )


    response = (
        client.responses.create(
            model=model_name,
            input=prompt
        )
    )


    output_text = (
        response.output_text
        .strip()
    )


    if output_text.startswith(
        "```"
    ):

        output_text = (
            output_text
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )


    return json.loads(
        output_text
    )


# ============================================================
# SAFE HTML
# ============================================================

def safe_text(value):

    if value is None:
        return ""

    return html.escape(
        str(value)
    )


# ============================================================
# AI SECTION HEADER
# ============================================================

st.markdown(
    "<br>",
    unsafe_allow_html=True
)


ai_header_col1, ai_header_col2 = (
    st.columns(
        [4, 1]
    )
)


with ai_header_col1:

    st.markdown(
        f"""
<div style="
    color:{MUTED};
    font-size:14px;
    font-weight:700;
    padding-top:8px;
">
MANAGEMENT INSIGHTS — {current_work_week}
</div>
        """,
        unsafe_allow_html=True
    )


with ai_header_col2:

    generate_ai = st.button(
        "✨ Generate Summary",
        use_container_width=True,
        type="primary"
    )


# ============================================================
# GENERATE BUTTON
# ============================================================

if generate_ai:

    if current_total == 0:

        st.warning(
            f"No findings recorded for "
            f"{current_work_week}. "
            "Summary was not generated."
        )


    elif (
        "OPENAI_API_KEY"
        not in st.secrets
    ):

        st.warning(
            "OpenAI API is not configured. "
            "Add OPENAI_API_KEY to "
            "Streamlit Secrets when you "
            "want to generate an summary."
        )


    else:

        try:

            with st.spinner(
                f"Generating "
                f"{current_work_week} "
                "summary..."
            ):

                new_summary = (
                    generate_new_ai_summary(
                        payload_json
                    )
                )


                ai_summary_store[
                    "summary"
                ] = new_summary


                ai_summary_store[
                    "work_week"
                ] = current_work_week


                ai_summary_store[
                    "generated_at"
                ] = (
                    datetime.now(
                        ZoneInfo(
                            "Asia/Kuala_Lumpur"
                        )
                    )
                    .strftime(
                        "%d-%b-%Y %H:%M"
                    )
                )


            st.success(
                f"{current_work_week} "
                "summary generated."
            )


        except Exception as e:

            st.error(
                "Unable to generate "
                "summary."
            )

            st.caption(
                str(e)
            )


# ============================================================
# READ EXISTING AI SUMMARY
# ============================================================

cached_summary = (
    ai_summary_store.get(
        "summary"
    )
)


cached_week = (
    ai_summary_store.get(
        "work_week"
    )
)


generated_at = (
    ai_summary_store.get(
        "generated_at"
    )
)


# ============================================================
# DEFAULT SENTENCES
# ============================================================

if (
    cached_summary is None
    or
    cached_week != current_work_week
):

    observation = (
        f"{current_total} finding(s) "
        f"recorded in {current_work_week} "
        "for the selected scope."
    )


    past_occurrence = (
        "Summary has not been generated. "
        "Generate the summary to compare "
        "current findings with historical "
        "occurrences."
    )


    recommendation = (
        "Continue IPQC monitoring and "
        "follow up on the current "
        "open findings."
    )


    highlight = (
        f"Current {current_work_week}: "
        f"{current_total} finding(s)."
    )


    showing_ai = False


# ============================================================
# CACHED AI SUMMARY
# ============================================================

else:

    observation = (
        cached_summary.get(
            "observation",
            ""
        )
    )


    past_occurrence = (
        cached_summary.get(
            "past_occurrence",
            ""
        )
    )


    recommendation = (
        cached_summary.get(
            "recommendation",
            ""
        )
    )


    highlight = (
        cached_summary.get(
            "highlight",
            ""
        )
    )


    showing_ai = True


# ============================================================
# SAFE OUTPUT
# ============================================================

observation = safe_text(
    observation
)


past_occurrence = safe_text(
    past_occurrence
)


recommendation = safe_text(
    recommendation
)


highlight = safe_text(
    highlight
)


# ============================================================
# AI CARDS
# ============================================================

ai_col1, ai_col2 = st.columns(
    [1.35, 1]
)


# ============================================================
# KEY OBSERVATIONS / LOW LIGHT
# ============================================================

with ai_col1:

    st.markdown(
        f"""
<div class="ai-card">

<div class="ai-title">
<span style="color:{RED};">●</span>
KEY OBSERVATIONS / LOW LIGHT
</div>

<div class="lowlight-header">
⚠ Low Light — {current_work_week}
</div>

<div class="ai-label">
Observation
</div>

<div class="ai-text">
{observation}
</div>

<div class="ai-label">
Past Occurrence
</div>

<div class="ai-text">
{past_occurrence}
</div>

<div class="ai-label">
Recommendation
</div>

<div class="ai-text">
{recommendation}
</div>

</div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# HIGHLIGHTS
# ============================================================

with ai_col2:

    st.markdown(
        f"""
<div class="ai-card">

<div class="ai-title">
<span style="color:{GREEN};">●</span>
HIGHLIGHTS
</div>

<div class="highlight-header">
★ Highlight — {current_work_week}
</div>

<div class="ai-label">
Current Week
</div>

<div class="ai-text">
{highlight}
</div>

<div class="ai-label">
WW Summary
</div>

<div class="ai-text">

Total Findings:
<b style="color:{TEXT};">
{current_total}
</b>



</div>



</div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# AI GENERATION INFORMATION
# ============================================================

if (
    showing_ai
    and
    generated_at
):

    st.caption(
        f"Summary generated: "
        f"{generated_at} • "
        "Dashboard refresh does not "
        "regenerate the summary."
    )
