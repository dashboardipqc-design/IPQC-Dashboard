import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


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

DARK_RING = "#1E293B"


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
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 2rem;
    }}

    h1 {{
        color: {TEXT};
        font-size: 28px !important;
        margin-bottom: 0 !important;
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
# CURRENT TIME
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
        "Finding Trend • Gap Monitoring • Closure Tracking"
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
# WORK WEEK
# ============================================================

df["week_number"] = (
    df["finding_datetime_parsed"]
    .dt
    .isocalendar()
    .week
)


df["work_week"] = (
    "WW"
    +
    df["week_number"].astype(str)
)


# ============================================================
# SHORT CATEGORY NAME
#
# Database value remains unchanged.
# This is only used for dashboard display.
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


# AREA FILTER

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


# CATEGORY FILTER

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


# SHIFT FILTER

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


# STATUS FILTER

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


# ============================================================
# COMMON BOTTOM LEGEND
# ============================================================

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
#
# TOTAL CASES
# SHIFT DISTRIBUTION
# TIME DISTRIBUTION
# FINDING CATEGORY
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

            labels=[
                "Total Cases"
            ],

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
    title="● TOTAL CASES",

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

        config={
            "displayModeBar": False
        }
    )


# ============================================================
# SHIFT DISTRIBUTION
# ============================================================

shift_data = (
    filtered_df
    .groupby("shift_letter")
    .size()
    .reset_index(
        name="Cases"
    )
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
    title="● SHIFT DISTRIBUTION (%)",

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

        config={
            "displayModeBar": False
        }
    )


# ============================================================
# TIME DISTRIBUTION
# ============================================================

time_data = (
    filtered_df
    .groupby("shift_type")
    .size()
    .reset_index(
        name="Cases"
    )
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
    title="● TIME DISTRIBUTION (%)",

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

        config={
            "displayModeBar": False
        }
    )


# ============================================================
# FINDING CATEGORY
# ============================================================

category_data = (
    filtered_df
    .groupby("category_short")
    .size()
    .reset_index(
        name="Cases"
    )
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
    title="● FINDING CATEGORY (%)",

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

        config={
            "displayModeBar": False
        }
    )


# ============================================================
# ROW 2
#
# WEEKLY FINDING TREND
# FINDINGS BY AREA
# ============================================================

row2_col1, row2_col2 = st.columns(
    [1.65, 1]
)


# ============================================================
# WEEKLY FINDING TREND
# ============================================================

weekly_data = (
    filtered_df
    .dropna(
        subset=["week_number"]
    )
    .groupby(
        [
            "week_number",
            "work_week"
        ]
    )
    .size()
    .reset_index(
        name="Cases"
    )
    .sort_values(
        "week_number"
    )
)


weekly_chart = go.Figure()


# BAR

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


# TREND LINE

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
    title="● WEEKLY FINDING TREND",

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
        gridcolor="#334155"
    ),

    yaxis=dict(
        gridcolor="#475569",
        rangemode="tozero"
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
    title="● FINDINGS BY AREA",

    height=315,

    xaxis_title="Cases",
    yaxis_title="",

    showlegend=False,

    xaxis=dict(
        gridcolor="#475569",
        rangemode="tozero"
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
