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
    page_title="IPQC Quality Indicators",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# COLOR PALETTE
# ============================================================

BG_COLOR = "#080D16"
CARD_COLOR = "#111A2B"
CARD_BORDER = "#293B5A"
TEXT_COLOR = "#F4F7FB"
MUTED_TEXT = "#9FB0CC"
GRID_COLOR = "#344157"

CYAN = "#28C6E5"
GREEN = "#20D26B"
ORANGE = "#FFA20B"
RED = "#FF4747"
PURPLE = "#9A7CF4"
BLUE = "#5D64EE"
TEAL = "#087D9B"
DARK_BLUE = "#1C2739"

AREA_COLORS = {
    "DP": "#21D4E8",
    "FOL": "#5964F2",
    "MOL": "#15BFA5",
    "EOL": "#FFA20B"
}

SHIFT_COLORS = {
    "A": "#28C6E5",
    "B": "#5D64EE",
    "C": "#087D9B",
    "D": "#9A7CF4"
}

TIME_COLORS = {
    "DAY": "#FFA20B",
    "NIGHT": "#1C2739"
}

CATEGORY_COLORS = [
    "#28C6E5",
    "#FF4747",
    "#FFA20B",
    "#9A7CF4",
    "#15BFA5"
]


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       MAIN PAGE
       ====================================================== */

    .stApp {
        background-color: #080D16;
    }

    .block-container {
        max-width: 1800px;
        padding-top: 1rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        padding-bottom: 2rem;
    }

    header[data-testid="stHeader"] {
        background-color: transparent;
    }


    /* ======================================================
       DASHBOARD HEADER
       ====================================================== */

    .dashboard-header {
        background:
            linear-gradient(
                110deg,
                #F5F5F5 0%,
                #F5F5F5 68%,
                #E7E7E7 68%,
                #B80000 100%
            );

        padding: 20px 28px;
        border-bottom: 3px solid #D71920;
        margin-bottom: 22px;
    }

    .dashboard-title {
        color: #050505;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin: 0;
    }


    /* ======================================================
       SECTION / CARD TITLE
       ====================================================== */

    .card-title {
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 1.5px;
        color: #9FB0CC;
        margin-bottom: 5px;
    }

    .cyan-dot {
        color: #28C6E5;
    }

    .green-dot {
        color: #20D26B;
    }

    .orange-dot {
        color: #FFA20B;
    }

    .purple-dot {
        color: #9A7CF4;
    }

    .red-dot {
        color: #FF4747;
    }


    /* ======================================================
       TOTAL CASE CARD
       ====================================================== */

    .total-card {
        background-color: #111A2B;
        border: 1px solid #293B5A;
        border-radius: 12px;
        height: 330px;
        padding: 20px;
        box-sizing: border-box;
    }

    .total-case-number {
        text-align: center;
        color: #28C6E5;
        font-size: 72px;
        font-weight: 800;
        margin-top: 65px;
        line-height: 1;
    }

    .total-case-label {
        text-align: center;
        color: #9FB0CC;
        font-size: 13px;
        margin-top: 15px;
        letter-spacing: 1px;
    }


    /* ======================================================
       BOTTOM CARDS
       ====================================================== */

    .bottom-card {
        background-color: #111A2B;
        border: 1px solid #293B5A;
        border-radius: 12px;
        min-height: 260px;
        padding: 18px 20px;
        box-sizing: border-box;
    }

    .summary-big {
        color: #F4F7FB;
        font-size: 42px;
        font-weight: 800;
        line-height: 1;
    }

    .summary-label {
        color: #9FB0CC;
        font-size: 13px;
        margin-bottom: 17px;
    }

    .summary-open {
        color: #FFA20B;
        font-size: 25px;
        font-weight: 800;
    }

    .summary-closed {
        color: #20D26B;
        font-size: 25px;
        font-weight: 800;
    }

    .summary-rate {
        color: #28C6E5;
        font-size: 25px;
        font-weight: 800;
    }


    /* ======================================================
       OBSERVATION
       ====================================================== */

    .observation-box {
        background-color: #321719;
        border: 1px solid #853033;
        color: #FF4747;
        padding: 12px 15px;
        border-radius: 8px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 15px;
    }


    /* ======================================================
       HIGHLIGHT
       ====================================================== */

    .highlight-box {
        background-color: #10291C;
        border: 1px solid #23663C;
        color: #20D26B;
        padding: 12px 15px;
        border-radius: 8px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 15px;
    }


    /* ======================================================
       GENERAL TEXT
       ====================================================== */

    p, span, label {
        color: #DCE5F3;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #293B5A;
        border-radius: 10px;
    }


    /* ======================================================
       PLOTLY CONTAINER
       ====================================================== */

    div[data-testid="stPlotlyChart"] {
        background-color: #111A2B;
        border: 1px solid #293B5A;
        border-radius: 12px;
        overflow: hidden;
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

current_week = current_time.isocalendar().week

current_year_short = str(current_time.year)[-2:]


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown(
    f"""
    <div class="dashboard-header">

        <div class="dashboard-title">
            QUALITY INDICATORS : IPQC WW{current_week}’{current_year_short}
        </div>

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


# ============================================================
# SHIFT A/B/C/D
# ============================================================

df["shift_letter"] = (
    df["shift"]
    .fillna("")
    .astype(str)
    .str.split(" - ")
    .str[0]
    .str.strip()
)


# ============================================================
# DAY / NIGHT
# ============================================================

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
    df["week_number"]
    .astype(str)
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
    df["finding_datetime_parsed"]
    .dt
    .normalize()
).dt.days

df["aging_days"] = (
    df["aging_days"]
    .fillna(0)
    .clip(lower=0)
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.title(
    "Dashboard Filters"
)


# ------------------------------------------------------------
# AREA
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
# CATEGORY
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
# SHIFT
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
# DAY / NIGHT
# ------------------------------------------------------------

time_options = sorted(
    df["shift_type"]
    .dropna()
    .unique()
    .tolist()
)

selected_time = st.sidebar.multiselect(
    "Day / Night",
    time_options,
    default=time_options
)


# ------------------------------------------------------------
# STATUS
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
    df["shift_type"].isin(selected_time)
    &
    df["status_clean"].isin(selected_status)
].copy()


if filtered_df.empty:

    st.warning(
        "No findings match the selected filters."
    )

    st.stop()


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
        /
        total_findings
        *
        100
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
# COMMON PLOTLY THEME
# ============================================================

def apply_chart_theme(fig):

    fig.update_layout(

        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,

        font=dict(
            color=TEXT_COLOR,
            size=12
        ),

        title=dict(
            font=dict(
                color=MUTED_TEXT,
                size=15
            ),
            x=0.04,
            xanchor="left"
        ),

        margin=dict(
            l=30,
            r=30,
            t=60,
            b=30
        ),

        legend=dict(
            font=dict(
                color="#DCE5F3",
                size=11
            )
        )
    )

    return fig


# ============================================================
# TOP ROW
#
# TOTAL CASE
# SHIFT
# TIME
# CATEGORY
# ============================================================

top1, top2, top3, top4 = st.columns(
    [1, 1, 1, 1]
)


# ============================================================
# TOTAL CASE
# ============================================================

with top1:

    st.markdown(
        f"""
        <div class="total-card">

            <div class="card-title">
                <span class="green-dot">●</span>
                TOTAL CASE
            </div>

            <div class="total-case-number">
                {total_findings}
            </div>

            <div class="total-case-label">
                TOTAL FINDINGS
            </div>

        </div>
        """,
        unsafe_allow_html=True
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

    color="shift_letter",

    color_discrete_map=SHIFT_COLORS,

    title="● SHIFT DISTRIBUTION (%)"
)


shift_chart.update_traces(

    textinfo="none",

    marker=dict(
        line=dict(
            color=CARD_COLOR,
            width=0
        )
    )
)


shift_chart.update_layout(

    height=330,

    paper_bgcolor=CARD_COLOR,

    font=dict(
        color=TEXT_COLOR
    ),

    title=dict(
        font=dict(
            color=MUTED_TEXT,
            size=14
        ),
        x=0.04
    ),

    legend=dict(

        orientation="v",

        yanchor="middle",
        y=0.5,

        xanchor="left",
        x=0.72,

        font=dict(
            size=10
        )
    ),

    margin=dict(
        l=20,
        r=15,
        t=55,
        b=20
    )
)


with top2:

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

time_findings = (
    filtered_df
    .groupby("shift_type")
    .size()
    .reset_index(
        name="Findings"
    )
)


time_chart = px.pie(

    time_findings,

    names="shift_type",
    values="Findings",

    hole=0.55,

    color="shift_type",

    color_discrete_map=TIME_COLORS,

    title="● TIME DISTRIBUTION (%)"
)


time_chart.update_traces(
    textinfo="none"
)


time_chart.update_layout(

    height=330,

    paper_bgcolor=CARD_COLOR,

    font=dict(
        color=TEXT_COLOR
    ),

    title=dict(
        font=dict(
            color=MUTED_TEXT,
            size=14
        ),
        x=0.04
    ),

    legend=dict(

        orientation="v",

        yanchor="middle",
        y=0.5,

        xanchor="left",
        x=0.72,

        font=dict(
            size=10
        )
    ),

    margin=dict(
        l=20,
        r=15,
        t=55,
        b=20
    )
)


with top3:

    st.plotly_chart(
        time_chart,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
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

    color_discrete_sequence=CATEGORY_COLORS,

    title="● FINDING CATEGORY (%)"
)


category_chart.update_traces(
    textinfo="none"
)


category_chart.update_layout(

    height=330,

    paper_bgcolor=CARD_COLOR,

    font=dict(
        color=TEXT_COLOR
    ),

    title=dict(
        font=dict(
            color=MUTED_TEXT,
            size=14
        ),
        x=0.04
    ),

    legend=dict(

        orientation="v",

        yanchor="middle",
        y=0.5,

        xanchor="left",
        x=0.68,

        font=dict(
            size=9
        )
    ),

    margin=dict(
        l=15,
        r=10,
        t=55,
        b=20
    )
)


with top4:

    st.plotly_chart(
        category_chart,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )


# ============================================================
# MIDDLE ROW
#
# FINDING TREND
# FINDINGS BY AREA
# ============================================================

middle1, middle2 = st.columns(
    [1.7, 1]
)


# ============================================================
# WEEKLY FINDING TREND
# ============================================================

weekly_findings = (
    filtered_df
    .dropna(
        subset=["week_number"]
    )
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


trend_chart = go.Figure()


trend_chart.add_trace(

    go.Scatter(

        x=weekly_findings["work_week"],
        y=weekly_findings["Findings"],

        mode="lines+markers+text",

        name="Total Findings",

        line=dict(
            color=CYAN,
            width=4
        ),

        marker=dict(
            color=CYAN,
            size=8
        ),

        text=weekly_findings["Findings"],

        textposition="top center",

        textfont=dict(
            color=CYAN
        )
    )
)


trend_chart.update_layout(

    title="● FINDING TREND 2026",

    height=390,

    paper_bgcolor=CARD_COLOR,
    plot_bgcolor=CARD_COLOR,

    font=dict(
        color=TEXT_COLOR
    ),

    title_font=dict(
        color=MUTED_TEXT,
        size=15
    ),

    xaxis=dict(

        title="",

        gridcolor=GRID_COLOR,

        showgrid=False,

        tickfont=dict(
            color="#DCE5F3"
        )
    ),

    yaxis=dict(

        title="Total Findings",

        gridcolor=GRID_COLOR,

        rangemode="tozero",

        tickfont=dict(
            color="#DCE5F3"
        )
    ),

    margin=dict(
        l=50,
        r=30,
        t=65,
        b=40
    ),

    legend=dict(
        orientation="h",
        y=1.08,
        x=0.45
    )
)


with middle1:

    st.plotly_chart(
        trend_chart,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
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
)


# Keep area order consistent
area_order = [
    "DP",
    "FOL",
    "MOL",
    "EOL"
]


area_findings["area"] = pd.Categorical(
    area_findings["area"],
    categories=area_order,
    ordered=True
)

area_findings = (
    area_findings
    .sort_values("area")
)


area_chart = go.Figure()


for _, row in area_findings.iterrows():

    area_chart.add_trace(

        go.Bar(

            x=[row["Findings"]],

            y=[row["area"]],

            orientation="h",

            marker_color=AREA_COLORS.get(
                str(row["area"]),
                CYAN
            ),

            text=[row["Findings"]],

            textposition="outside",

            textfont=dict(
                color=TEXT_COLOR
            ),

            showlegend=False
        )
    )


area_chart.update_layout(

    title="● FINDINGS BY AREA",

    height=390,

    paper_bgcolor=CARD_COLOR,
    plot_bgcolor=CARD_COLOR,

    font=dict(
        color=TEXT_COLOR
    ),

    title_font=dict(
        color=MUTED_TEXT,
        size=15
    ),

    xaxis=dict(

        title="Number of Findings",

        gridcolor=GRID_COLOR,

        rangemode="tozero"
    ),

    yaxis=dict(

        title="",

        categoryorder="array",

        categoryarray=[
            "EOL",
            "MOL",
            "FOL",
            "DP"
        ]
    ),

    margin=dict(
        l=55,
        r=50,
        t=65,
        b=40
    ),

    bargap=0.25
)


with middle2:

    st.plotly_chart(
        area_chart,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )


# ============================================================
# AUTOMATIC OBSERVATIONS
# ============================================================

if not filtered_df.empty:

    area_counts = (
        filtered_df["area"]
        .value_counts()
    )

    highest_area = (
        area_counts.index[0]
        if not area_counts.empty
        else "-"
    )

    highest_area_count = (
        int(area_counts.iloc[0])
        if not area_counts.empty
        else 0
    )


    category_counts = (
        filtered_df["category"]
        .value_counts()
    )

    highest_category = (
        category_counts.index[0]
        if not category_counts.empty
        else "-"
    )

    highest_category_count = (
        int(category_counts.iloc[0])
        if not category_counts.empty
        else 0
    )

else:

    highest_area = "-"
    highest_area_count = 0

    highest_category = "-"
    highest_category_count = 0


# ============================================================
# BOTTOM ROW
#
# SUMMARY
# KEY OBSERVATIONS
# HIGHLIGHTS
# ============================================================

bottom1, bottom2, bottom3 = st.columns(
    [1, 1, 1]
)


# ============================================================
# SUMMARY
# ============================================================

with bottom1:

    st.markdown(
        f"""
        <div class="bottom-card">

            <div class="card-title">
                <span class="cyan-dot">●</span>
                SUMMARY
            </div>

            <div class="summary-big">
                {total_findings}
            </div>

            <div class="summary-label">
                Total Findings
            </div>


            <div class="summary-open">
                {open_findings}
            </div>

            <div class="summary-label">
                Open Findings
            </div>


            <div class="summary-closed">
                {closed_findings}
            </div>

            <div class="summary-label">
                Closed Findings
            </div>


            <div class="summary-rate">
                {closure_rate:.1f}%
            </div>

            <div class="summary-label">
                Closure Rate
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# KEY OBSERVATIONS
# ============================================================

with bottom2:

    st.markdown(
        f"""
        <div class="bottom-card">

            <div class="card-title">
                <span class="red-dot">●</span>
                KEY OBSERVATIONS
            </div>


            <div class="observation-box">
                ⚠ ATTENTION — WW{current_week}
            </div>


            <div style="
                color:#9FB0CC;
                font-size:14px;
                line-height:1.7;
            ">

                • Highest finding area:
                <b style="color:#F4F7FB;">
                    {highest_area}
                </b>
                ({highest_area_count} cases)

                <br><br>

                • Highest finding category:
                <b style="color:#F4F7FB;">
                    {highest_category}
                </b>
                ({highest_category_count} cases)

                <br><br>

                • Open findings >7 days:
                <b style="color:#FF4747;">
                    {overdue_findings}
                </b>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# HIGHLIGHTS
# ============================================================

with bottom3:

    if closed_findings > 0:

        highlight_message = (
            f"{closed_findings} finding(s) have been closed."
        )

    else:

        highlight_message = (
            "Closure tracking will appear once findings are closed."
        )


    st.markdown(
        f"""
        <div class="bottom-card">

            <div class="card-title">
                <span class="green-dot">●</span>
                HIGHLIGHTS
            </div>


            <div class="highlight-box">
                ★ HIGHLIGHT — WW{current_week}
            </div>


            <div style="
                color:#9FB0CC;
                font-size:14px;
                line-height:1.7;
            ">

                • {highlight_message}

                <br><br>

                • Current closure rate:
                <b style="color:#20D26B;">
                    {closure_rate:.1f}%
                </b>

                <br><br>

                • Total cases monitored:
                <b style="color:#F4F7FB;">
                    {total_findings}
                </b>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# OPEN FINDING DETAILS
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)


with st.expander(
    f"Open Finding Details ({open_findings})"
):

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
            "shift",
            "area",
            "station",
            "equipment_id",
            "category",
            "finding_description",
            "interview_result",
            "containment_action",
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

                    "id":
                        "ID",

                    "finding_datetime":
                        "Finding Date & Time",

                    "shift":
                        "Shift",

                    "area":
                        "Area",

                    "station":
                        "Station",

                    "equipment_id":
                        "Equipment ID",

                    "category":
                        "Category",

                    "finding_description":
                        "Finding Description",

                    "interview_result":
                        "Interview Result",

                    "containment_action":
                        "Containment Action",

                    "auditee":
                        "Auditee",

                    "auditor":
                        "Auditor",

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


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "IPQC Finding Monitoring Dashboard "
    f"• Last Updated: {current_time.strftime('%d-%b-%Y %H:%M')}"
)
