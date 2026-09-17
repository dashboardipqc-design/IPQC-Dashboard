import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="IPQC Finding Monitoring Dashboard",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }

    [data-testid="stMetric"] {
        background-color: #131c2e;
        border: 1px solid #2d3d59;
        padding: 18px 20px;
        border-radius: 10px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 15px;
        color: #aebbd0;
    }

    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
    }

    div[data-testid="stPlotlyChart"] {
        background-color: #131c2e;
        border: 1px solid #2d3d59;
        border-radius: 10px;
        padding: 8px;
    }

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
# LOAD DATA
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
# HEADER
# ============================================================

current_time = datetime.now(
    ZoneInfo("Asia/Kuala_Lumpur")
)

st.title(
    "IPQC Finding Monitoring Dashboard"
)

st.caption(
    "Finding Trend • Gap Monitoring • Closure Tracking"
)

st.caption(
    f"Last Updated: {current_time.strftime('%d-%b-%Y %H:%M')}"
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
# DATA CLEANING
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


# ------------------------------------------------------------
# Shift separation
#
# Example:
# B - DAY
#
# becomes:
# Shift = B
# Time = DAY
# ------------------------------------------------------------

df["shift_letter"] = (
    df["shift"]
    .fillna("")
    .astype(str)
    .str.split(" - ")
    .str[0]
)

df["shift_type"] = (
    df["shift"]
    .fillna("")
    .astype(str)
    .str.split(" - ")
    .str[-1]
)


# ============================================================
# FINDING AGING
# ============================================================

today = pd.Timestamp(
    current_time.date()
)

df["aging_days"] = (
    today -
    df["finding_datetime_parsed"].dt.normalize()
).dt.days

df["aging_days"] = (
    df["aging_days"]
    .fillna(0)
    .clip(lower=0)
)


def aging_group(days):

    if days <= 3:
        return "0-3 Days"

    elif days <= 7:
        return "4-7 Days"

    else:
        return ">7 Days"


df["aging_group"] = (
    df["aging_days"]
    .apply(aging_group)
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header(
    "Dashboard Filters"
)


# ------------------------------------------------------------
# AREA FILTER
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# CATEGORY FILTER
# ------------------------------------------------------------

category_options = sorted(
    df["category"]
    .dropna()
    .unique()
    .tolist()
)

selected_category = st.sidebar.multiselect(
    "Category",
    category_options,
    default=category_options
)


# ------------------------------------------------------------
# SHIFT FILTER
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# STATUS FILTER
# ------------------------------------------------------------

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
    df["category"].isin(selected_category)
    &
    df["shift_letter"].isin(selected_shift)
    &
    df["status_clean"].isin(selected_status)
].copy()


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_findings = len(
    filtered_df
)

open_findings = len(
    filtered_df[
        filtered_df["status_clean"] == "Open"
    ]
)

closed_findings = len(
    filtered_df[
        filtered_df["status_clean"] == "Closed"
    ]
)


if total_findings > 0:

    closure_rate = (
        closed_findings
        / total_findings
        * 100
    )

else:

    closure_rate = 0


overdue_findings = len(
    filtered_df[
        (filtered_df["status_clean"] == "Open")
        &
        (filtered_df["aging_days"] > 7)
    ]
)


# ============================================================
# KPI CARDS
# ============================================================

st.subheader(
    "Finding Summary"
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


with kpi1:

    st.metric(
        "Total Findings",
        total_findings
    )


with kpi2:

    st.metric(
        "Open Findings",
        open_findings
    )


with kpi3:

    st.metric(
        "Closed Findings",
        closed_findings
    )


with kpi4:

    st.metric(
        "Closure Rate",
        f"{closure_rate:.1f}%"
    )


with kpi5:

    st.metric(
        "Open >7 Days",
        overdue_findings
    )


st.divider()


# ============================================================
# CHECK FILTER RESULT
# ============================================================

if filtered_df.empty:

    st.warning(
        "No findings match the selected filters."
    )

    st.stop()


# ============================================================
# WEEK NUMBER
# ============================================================

filtered_df["week_number"] = (
    filtered_df[
        "finding_datetime_parsed"
    ]
    .dt
    .isocalendar()
    .week
)

filtered_df["work_week"] = (
    "WW"
    +
    filtered_df[
        "week_number"
    ]
    .astype(str)
)


# ============================================================
# WEEKLY FINDING TREND
# ============================================================

weekly_findings = (
    filtered_df
    .groupby(
        ["week_number", "work_week"]
    )
    .size()
    .reset_index(
        name="Findings"
    )
    .sort_values(
        "week_number"
    )
)


weekly_chart = px.bar(
    weekly_findings,
    x="work_week",
    y="Findings",
    text="Findings",
    title="Weekly Finding Trend"
)

weekly_chart.update_traces(
    textposition="outside"
)

weekly_chart.update_layout(
    height=420,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    ),
    xaxis_title="Work Week",
    yaxis_title="Number of Findings"
)


# ============================================================
# FINDINGS BY AREA
# ============================================================

area_findings = (
    filtered_df
    .groupby("area")
    .size()
    .reset_index(
        name="Findings"
    )
    .sort_values(
        "Findings",
        ascending=True
    )
)


area_chart = px.bar(
    area_findings,
    x="Findings",
    y="area",
    orientation="h",
    text="Findings",
    title="Findings by Area"
)

area_chart.update_traces(
    textposition="outside"
)

area_chart.update_layout(
    height=420,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    ),
    xaxis_title="Number of Findings",
    yaxis_title=""
)


# ============================================================
# MAIN CHART ROW
# ============================================================

chart1, chart2 = st.columns(
    [1.7, 1]
)


with chart1:

    st.plotly_chart(
        weekly_chart,
        use_container_width=True
    )


with chart2:

    st.plotly_chart(
        area_chart,
        use_container_width=True
    )


# ============================================================
# CATEGORY DISTRIBUTION
# ============================================================

category_findings = (
    filtered_df
    .groupby("category")
    .size()
    .reset_index(
        name="Findings"
    )
)


category_chart = px.pie(
    category_findings,
    names="category",
    values="Findings",
    hole=0.55,
    title="Findings by Category"
)

category_chart.update_layout(
    height=400,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ============================================================
# SHIFT DISTRIBUTION
# ============================================================

shift_findings = (
    filtered_df
    .groupby("shift_letter")
    .size()
    .reset_index(
        name="Findings"
    )
)


shift_chart = px.pie(
    shift_findings,
    names="shift_letter",
    values="Findings",
    hole=0.55,
    title="Findings by Shift"
)

shift_chart.update_layout(
    height=400,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ============================================================
# OPEN AGING
# ============================================================

open_df = filtered_df[
    filtered_df["status_clean"] == "Open"
].copy()


aging_order = [
    "0-3 Days",
    "4-7 Days",
    ">7 Days"
]


if not open_df.empty:

    aging_findings = (
        open_df
        .groupby("aging_group")
        .size()
        .reindex(
            aging_order,
            fill_value=0
        )
        .reset_index(
            name="Findings"
        )
    )

else:

    aging_findings = pd.DataFrame(
        {
            "aging_group": aging_order,
            "Findings": [0, 0, 0]
        }
    )


aging_chart = px.bar(
    aging_findings,
    x="aging_group",
    y="Findings",
    text="Findings",
    title="Open Finding Aging"
)

aging_chart.update_traces(
    textposition="outside"
)

aging_chart.update_layout(
    height=400,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    ),
    xaxis_title="Aging",
    yaxis_title="Open Findings"
)


# ============================================================
# SECOND CHART ROW
# ============================================================

chart3, chart4, chart5 = st.columns(3)


with chart3:

    st.plotly_chart(
        category_chart,
        use_container_width=True
    )


with chart4:

    st.plotly_chart(
        shift_chart,
        use_container_width=True
    )


with chart5:

    st.plotly_chart(
        aging_chart,
        use_container_width=True
    )


# ============================================================
# OPEN FINDING DETAILS
# ============================================================

st.divider()

st.subheader(
    "Open Finding Details"
)


open_table = filtered_df[
    filtered_df["status_clean"] == "Open"
].copy()


if open_table.empty:

    st.success(
        "No open findings for the selected filters."
    )

else:

    display_columns = [
        "id",
        "finding_datetime",
        "area",
        "station",
        "equipment_id",
        "category",
        "finding_description",
        "auditee",
        "auditor",
        "aging_days",
        "status_clean"
    ]

    display_columns = [
        column
        for column in display_columns
        if column in open_table.columns
    ]


    display_table = (
        open_table[
            display_columns
        ]
        .sort_values(
            "aging_days",
            ascending=False
        )
        .rename(
            columns={
                "id": "ID",
                "finding_datetime":
                    "Finding Date & Time",
                "area": "Area",
                "station": "Station",
                "equipment_id":
                    "Equipment ID",
                "category": "Category",
                "finding_description":
                    "Finding Description",
                "auditee": "Auditee",
                "auditor": "Auditor",
                "aging_days":
                    "Aging (Days)",
                "status_clean":
                    "Status"
            }
        )
    )


    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True
    )
