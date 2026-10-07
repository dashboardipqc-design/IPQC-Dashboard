import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="IPQC Inspection History",
    page_icon="📋",
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
GREEN = "#22C55E"
ORANGE = "#F59E0B"
RED = "#EF4444"


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

    h1, h2, h3 {{
        color: {TEXT};
    }}

    p {{
        color: {MUTED};
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
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
# CURRENT TIME
# ============================================================

MALAYSIA_TZ = ZoneInfo(
    "Asia/Kuala_Lumpur"
)

current_time = datetime.now(
    MALAYSIA_TZ
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=60)
def load_inspection_headers():

    response = (
        supabase
        .table("inspection_header")
        .select(
            "id,"
            "inspection_no,"
            "checklist_id,"
            "version_id,"
            "lot_number,"
            "machine,"
            "inspector,"
            "shift,"
            "inspection_datetime,"
            "submitted_at,"
            "status,"
            "factory,"
            "submission_type,"
            "shift_date"
        )
        .eq(
            "status",
            "SUBMITTED"
        )
        .order(
            "inspection_datetime",
            desc=True
        )
        .execute()
    )

    return pd.DataFrame(
        response.data
    )


@st.cache_data(ttl=300)
def load_checklist_master():

    response = (
        supabase
        .table("checklist_master")
        .select(
            "id,"
            "checklist_code,"
            "area,"
            "process,"
            "checklist_name"
        )
        .execute()
    )

    return pd.DataFrame(
        response.data
    )
@st.cache_data(ttl=60)
def load_findings():

    response = (
        supabase
        .table("Findings")
        .select(
            "id,"
            "created_at,"
            "finding_datetime,"
            "shift,"
            "factory,"
            "area,"
            "station,"
            "equipment_id,"
            "lot_number,"
            "category,"
            "finding_description,"
            "auditee,"
            "auditor,"
            "status"
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    return pd.DataFrame(
        response.data
    )

# ============================================================
# HEADER
# ============================================================

header1, header2 = st.columns(
    [5, 1]
)


with header1:

    st.title(
        "📋 IPQC Inspection History"
    )

    st.caption(
        "Submitted Checklist Records"
    )


with header2:

    st.write("")

    if st.button(
        "← Back to Dashboard",
        width="stretch"
    ):

        st.switch_page(
            "app.py"
        )


st.divider()


# ============================================================
# GET DATA
# ============================================================

try:

    inspection_df = load_inspection_headers()
    checklist_df = load_checklist_master()
    findings_df = load_findings()

except Exception as e:

    st.error(
        "Unable to retrieve inspection history."
    )

    st.exception(e)

    st.stop()


if inspection_df.empty:

    st.info(
        "No submitted inspection records found."
    )

    st.stop()


# ============================================================
# MERGE CHECKLIST INFORMATION
# ============================================================

if not checklist_df.empty:

    checklist_lookup = checklist_df.rename(
        columns={
            "id": "checklist_id"
        }
    )

    inspection_df = inspection_df.merge(
        checklist_lookup[
            [
                "checklist_id",
                "checklist_code",
                "area",
                "process",
                "checklist_name"
            ]
        ],
        on="checklist_id",
        how="left"
    )

else:

    inspection_df["checklist_code"] = ""
    inspection_df["area"] = ""
    inspection_df["process"] = ""
    inspection_df["checklist_name"] = ""


# ============================================================
# CLEAN DATA
# ============================================================

inspection_df["inspection_datetime"] = pd.to_datetime(
    inspection_df["inspection_datetime"],
    errors="coerce",
    utc=True
)

inspection_df["inspection_datetime_myt"] = (
    inspection_df["inspection_datetime"]
    .dt.tz_convert(
        MALAYSIA_TZ
    )
)


inspection_df["inspection_date"] = (
    inspection_df["inspection_datetime_myt"]
    .dt.date
)


for column in [
    "factory",
    "area",
    "process",
    "submission_type",
    "inspector",
    "lot_number",
    "machine",
    "inspection_no",
    "shift"
]:

    if column in inspection_df.columns:

        inspection_df[column] = (
            inspection_df[column]
            .fillna("")
            .astype(str)
        )


# ============================================================
# FILTERS
# ============================================================

st.subheader(
    "Inspection Records"
)


filter1, filter2, filter3, filter4 = st.columns(
    4
)


with filter1:

    default_start_date = (
        current_time.date()
        - timedelta(days=30)
    )

    start_date = st.date_input(
        "Start Date",
        value=default_start_date
    )


with filter2:

    end_date = st.date_input(
        "End Date",
        value=current_time.date()
    )


with filter3:

    factory_options = [
        "All"
    ] + sorted(
        [
            x
            for x in inspection_df["factory"].unique()
            if x
        ]
    )

    selected_factory = st.selectbox(
        "Factory",
        factory_options
    )


with filter4:

    area_order = [
        "DP",
        "FOL",
        "MOL",
        "EOL"
    ]

    existing_areas = (
        inspection_df["area"]
        .dropna()
        .unique()
        .tolist()
    )

    area_options = [
        "All"
    ] + [
        area
        for area in area_order
        if area in existing_areas
    ]

    selected_area = st.selectbox(
        "Area",
        area_options
    )


filter5, filter6, filter7, filter8 = st.columns(
    4
)


with filter5:

    process_source = inspection_df.copy()

    if selected_area != "All":

        process_source = process_source[
            process_source["area"]
            == selected_area
        ]

    process_options = [
        "All"
    ] + sorted(
        [
            x
            for x in process_source["process"].unique()
            if x
        ]
    )

    selected_process = st.selectbox(
        "Process",
        process_options
    )


with filter6:

    submission_options = [
        "All"
    ] + sorted(
        [
            x
            for x in inspection_df["submission_type"].unique()
            if x
        ]
    )

    selected_submission_type = st.selectbox(
        "Submission Type",
        submission_options
    )


with filter7:

    inspector_search = st.text_input(
        "Inspector",
        placeholder="6-digit badge"
    )


with filter8:

    lot_search = st.text_input(
        "Lot Number",
        placeholder="Search lot"
    )


filter9, filter10 = st.columns(
    2
)


with filter9:

    machine_search = st.text_input(
        "Machine / Workstation",
        placeholder="Search machine"
    )


with filter10:

    inspection_no_search = st.text_input(
        "Inspection No.",
        placeholder="Search inspection number"
    )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = inspection_df.copy()


filtered_df = filtered_df[
    (
        filtered_df["inspection_date"]
        >= start_date
    )
    &
    (
        filtered_df["inspection_date"]
        <= end_date
    )
]


if selected_factory != "All":

    filtered_df = filtered_df[
        filtered_df["factory"]
        == selected_factory
    ]


if selected_area != "All":

    filtered_df = filtered_df[
        filtered_df["area"]
        == selected_area
    ]


if selected_process != "All":

    filtered_df = filtered_df[
        filtered_df["process"]
        == selected_process
    ]


if selected_submission_type != "All":

    filtered_df = filtered_df[
        filtered_df["submission_type"]
        == selected_submission_type
    ]


if inspector_search.strip():

    filtered_df = filtered_df[
        filtered_df["inspector"]
        .str.contains(
            inspector_search.strip(),
            case=False,
            na=False
        )
    ]


if lot_search.strip():

    filtered_df = filtered_df[
        filtered_df["lot_number"]
        .str.contains(
            lot_search.strip(),
            case=False,
            na=False
        )
    ]


if machine_search.strip():

    filtered_df = filtered_df[
        filtered_df["machine"]
        .str.contains(
            machine_search.strip(),
            case=False,
            na=False
        )
    ]


if inspection_no_search.strip():

    filtered_df = filtered_df[
        filtered_df["inspection_no"]
        .str.contains(
            inspection_no_search.strip(),
            case=False,
            na=False
        )
    ]


filtered_df = filtered_df.sort_values(
    "inspection_datetime_myt",
    ascending=False
)


# ============================================================
# RECORD COUNT
# ============================================================

st.markdown(
    f"""
    <div style="
        color:{MUTED};
        font-size:14px;
        margin-top:10px;
        margin-bottom:10px;
    ">
        Showing
        <b style="color:{TEXT};">
            {len(filtered_df):,}
        </b>
        inspection record(s)
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HISTORY TABLE
# ============================================================

if filtered_df.empty:

    st.info(
        "No inspection records match the selected filters."
    )

    st.stop()


display_df = filtered_df.copy()


display_df["Inspection Time"] = (
    display_df["inspection_datetime_myt"]
    .dt.strftime(
        "%d-%b-%Y %H:%M"
    )
)


display_df = display_df.rename(
    columns={
        "inspection_no": "Inspection No.",
        "factory": "Factory",
        "area": "Area",
        "process": "Process",
        "lot_number": "Lot Number",
        "machine": "Machine",
        "inspector": "Inspector",
        "shift": "Shift",
        "submission_type": "Type"
    }
)


display_columns = [
    "Inspection Time",
    "Inspection No.",
    "Factory",
    "Area",
    "Process",
    "Lot Number",
    "Machine",
    "Inspector",
    "Shift",
    "Type"
]


st.dataframe(
    display_df[
        display_columns
    ],
    width="stretch",
    hide_index=True,
    height=500
)
