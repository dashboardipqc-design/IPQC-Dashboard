import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from supabase import create_client


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="IPQC Data",
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
        padding-top: 1.5rem !important;
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
            "interview_result,"
            "containment_action,"
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
        "IPQC Data"
    )

    st.caption(
        "Checklist & Finding Records"
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


st.markdown(
    "<div style='height: 8px;'></div>",
    unsafe_allow_html=True
)


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
# NORMALIZE CHECKLIST RECORDS
# ============================================================

checklist_history_df = pd.DataFrame()

checklist_history_df["record_datetime"] = (
    inspection_df["inspection_datetime_myt"]
)

checklist_history_df["record_date"] = (
    inspection_df["inspection_date"]
)

checklist_history_df["record_no"] = (
    inspection_df["inspection_no"]
)

checklist_history_df["record_type"] = "Checklist"
checklist_history_df["source_id"] = None

checklist_history_df["factory"] = (
    inspection_df["factory"]
)

checklist_history_df["area"] = (
    inspection_df["area"]
)

checklist_history_df["process_station"] = (
    inspection_df["process"]
)

checklist_history_df["lot_number"] = (
    inspection_df["lot_number"]
)

checklist_history_df["machine"] = (
    inspection_df["machine"]
)

checklist_history_df["inspector_auditor"] = (
    inspection_df["inspector"]
)

checklist_history_df["shift"] = (
    inspection_df["shift"]
)

checklist_history_df["type_status"] = (
    inspection_df["submission_type"]
)


# ============================================================
# NORMALIZE FINDING RECORDS
# ============================================================

if not findings_df.empty:

    findings_df["created_at"] = pd.to_datetime(
        findings_df["created_at"],
        errors="coerce",
        utc=True
    )

    findings_df["record_datetime"] = (
        findings_df["created_at"]
        .dt.tz_convert(
            MALAYSIA_TZ
        )
    )

    findings_df["record_date"] = (
        findings_df["record_datetime"]
        .dt.date
    )

    for column in [
        "factory",
        "area",
        "station",
        "equipment_id",
        "lot_number",
        "auditor",
        "shift",
        "status"
    ]:

        findings_df[column] = (
            findings_df[column]
            .fillna("")
            .astype(str)
        )


    finding_history_df = pd.DataFrame()

    finding_history_df["record_datetime"] = (
        findings_df["record_datetime"]
    )

    finding_history_df["record_date"] = (
        findings_df["record_date"]
    )

    finding_history_df["record_no"] = (
        "FIND-"
        + findings_df["id"].astype(str)
    )

    finding_history_df["record_type"] = "Finding"
    finding_history_df["source_id"] = (
    findings_df["id"]
)

    finding_history_df["factory"] = (
        findings_df["factory"]
    )

    finding_history_df["area"] = (
        findings_df["area"]
    )

    finding_history_df["process_station"] = (
        findings_df["station"]
    )

    finding_history_df["lot_number"] = (
        findings_df["lot_number"]
    )

    finding_history_df["machine"] = (
        findings_df["equipment_id"]
    )

    finding_history_df["inspector_auditor"] = (
        findings_df["auditor"]
    )

    finding_history_df["shift"] = (
        findings_df["shift"]
    )

    finding_history_df["type_status"] = (
        findings_df["status"]
    )

else:

    finding_history_df = pd.DataFrame(
        columns=checklist_history_df.columns
    )


# ============================================================
# COMBINE IPQC HISTORY
# ============================================================

history_df = pd.concat(
    [
        checklist_history_df,
        finding_history_df
    ],
    ignore_index=True
)

history_df = history_df.sort_values(
    "record_datetime",
    ascending=False
).reset_index(
    drop=True
)

# ============================================================
# FILTERS
# ============================================================

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

    record_type_options = [
        "All",
        "Checklist",
        "Finding"
    ]

    selected_record_type = st.selectbox(
        "Record Type",
        record_type_options
    )


with filter4:

    factory_options = [
        "All"
    ] + sorted(
        [
            x
            for x in history_df["factory"].unique()
            if x
        ]
    )

    selected_factory = st.selectbox(
        "Factory",
        factory_options
    )


filter5, filter6, filter7, filter8 = st.columns(
    4
)


with filter5:

    area_order = [
        "DP",
        "FOL",
        "MOL",
        "EOL"
    ]

    existing_areas = (
        history_df["area"]
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


with filter6:

    process_source = history_df.copy()

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
            for x in process_source[
                "process_station"
            ].unique()
            if x
        ]
    )

    selected_process = st.selectbox(
        "Process / Station",
        process_options
    )


with filter7:

    type_status_options = [
        "All"
    ] + sorted(
        [
            x
            for x in history_df[
                "type_status"
            ].unique()
            if x
        ]
    )

    selected_type_status = st.selectbox(
        "Type / Status",
        type_status_options
    )


with filter8:

    inspector_search = st.text_input(
        "Inspector / Auditor",
        placeholder="6-digit badge"
    )


filter9, filter10, filter11 = st.columns(
    3
)


with filter9:

    lot_search = st.text_input(
        "Lot Number",
        placeholder="Search lot"
    )


with filter10:

    machine_search = st.text_input(
        "Machine / Workstation",
        placeholder="Search machine"
    )


with filter11:

    record_no_search = st.text_input(
        "Record No.",
        placeholder="Search record number"
    )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = history_df.copy()


filtered_df = filtered_df[
    (
        filtered_df["record_date"]
        >= start_date
    )
    &
    (
        filtered_df["record_date"]
        <= end_date
    )
]


if selected_record_type != "All":

    filtered_df = filtered_df[
        filtered_df["record_type"]
        == selected_record_type
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
        filtered_df["process_station"]
        == selected_process
    ]


if selected_type_status != "All":

    filtered_df = filtered_df[
        filtered_df["type_status"]
        == selected_type_status
    ]


if inspector_search.strip():

    filtered_df = filtered_df[
        filtered_df["inspector_auditor"]
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


if record_no_search.strip():

    filtered_df = filtered_df[
        filtered_df["record_no"]
        .str.contains(
            record_no_search.strip(),
            case=False,
            na=False
        )
    ]


filtered_df = filtered_df.sort_values(
    "record_datetime",
    ascending=False
)

# ============================================================
# RECORD COUNT / PAGINATION
# ============================================================

count_col, limit_col = st.columns(
    [5, 1]
)


with count_col:

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
            IPQC record(s)
        </div>
        """,
        unsafe_allow_html=True
    )


with limit_col:

    display_limit = st.selectbox(
        "Rows",
        [10, 20, 50, 100],
        index=0,
        key="history_display_limit"
    )


total_records = len(filtered_df)

total_pages = max(
    1,
    (
        total_records
        + display_limit
        - 1
    )
    // display_limit
)


if "history_page" not in st.session_state:

    st.session_state.history_page = 1


if (
    st.session_state.history_page
    > total_pages
):

    st.session_state.history_page = total_pages


current_page = (
    st.session_state.history_page
)


start_index = (
    current_page - 1
) * display_limit

end_index = min(
    start_index + display_limit,
    total_records
)

# ============================================================
# HISTORY TABLE
# ============================================================

if filtered_df.empty:

    st.info(
        "No IPQC records match the selected filters."
    )

    st.stop()


page_df = (
    filtered_df
    .iloc[
        start_index:end_index
    ]
    .copy()
    .reset_index(
        drop=True
    )
)


display_df = page_df.copy()

display_df["Date / Time"] = (
    display_df["record_datetime"]
    .dt.strftime(
        "%d-%b-%Y %H:%M"
    )
)


display_df = display_df.rename(
    columns={
        "record_no": "Record No.",
        "record_type": "Record Type",
        "factory": "Factory",
        "area": "Area",
        "process_station": "Process / Station",
        "lot_number": "Lot Number",
        "machine": "Machine / Workstation",
        "inspector_auditor": "Inspector / Auditor",
        "shift": "Shift",
        "type_status": "Type / Status"
    }
)


display_columns = [
    "Date / Time",
    "Record No.",
    "Record Type",
    "Factory",
    "Area",
    "Process / Station",
    "Lot Number",
    "Machine / Workstation",
    "Inspector / Auditor",
    "Shift",
    "Type / Status"
]

table_height = min(
    500,
    38 + (len(display_df) * 35)
)


table_event = st.dataframe(
    display_df[
        display_columns
    ],
    width="stretch",
    hide_index=True,
    height=table_height,
    on_select="rerun",
    selection_mode="single-row"
)

# ============================================================
# PAGE NAVIGATION
# ============================================================

if total_pages > 1:

    st.markdown("")

    nav_left, nav_pages, nav_right = st.columns(
        [1, 6, 1]
    )


    with nav_left:

        if st.button(
            "◀ Previous",
            disabled=(
                current_page == 1
            ),
            width="stretch"
        ):

            st.session_state.history_page -= 1

            st.rerun()


    with nav_pages:

        page_options = list(
            range(
                1,
                total_pages + 1
            )
        )

        selected_page = st.selectbox(
            "Page",
            page_options,
            index=current_page - 1,
            format_func=lambda x: (
                f"Page {x} of {total_pages}"
            ),
            label_visibility="collapsed"
        )


        if (
            selected_page
            != current_page
        ):

            st.session_state.history_page = (
                selected_page
            )

            st.rerun()


    with nav_right:

        if st.button(
            "Next ▶",
            disabled=(
                current_page
                == total_pages
            ),
            width="stretch"
        ):

            st.session_state.history_page += 1

            st.rerun()


# ============================================================
# FINDING DETAIL VIEWER
# ============================================================
def show_detail_value(
    label,
    value
):

    display_value = (
        str(value)
        if value not in [
            None,
            ""
        ]
        else "-"
    )

    st.markdown(
        f"""
        <div style="
            color:{MUTED};
            font-size:14px;
            font-weight:600;
            margin-bottom:6px;
        ">
            {label}
        </div>

        <div style="
            color:{TEXT};
            font-size:17px;
            font-weight:500;
            line-height:1.55;
            margin-bottom:22px;
        ">
            {display_value}
        </div>
        """,
        unsafe_allow_html=True
    )
selected_rows = table_event.selection.rows


if selected_rows:

    selected_row_position = selected_rows[0]

    selected_record = filtered_df.iloc[
        selected_row_position
    ]


    # --------------------------------------------------------
    # FINDING RECORD ONLY
    # --------------------------------------------------------

    if selected_record["record_type"] == "Finding":

        finding_id = selected_record["source_id"]

        selected_finding_df = findings_df[
            findings_df["id"]
            == finding_id
        ]


        if not selected_finding_df.empty:

            finding_record = (
                selected_finding_df.iloc[0]
            )


            st.divider()

            st.subheader(
                f"🔍 Finding Detail — FIND-{finding_id}"
            )


            # ====================================================
            # FINDING INFORMATION
            # ====================================================

            st.markdown(
                "### Finding Information"
            )


            info1, info2, info3, info4 = st.columns(
                4
            )


            with info1:

                st.markdown(
                    "**Finding Date / Time**"
                )

                st.write(
                    finding_record[
                        "finding_datetime"
                    ]
                    or "-"
                )


            with info2:

                st.markdown(
                    "**Factory**"
                )

                st.write(
                    finding_record["factory"]
                    or "-"
                )


            with info3:

                st.markdown(
                    "**Area**"
                )

                st.write(
                    finding_record["area"]
                    or "-"
                )


            with info4:

                st.markdown(
                    "**Station**"
                )

                st.write(
                    finding_record["station"]
                    or "-"
                )


            info5, info6, info7, info8 = st.columns(
                4
            )


            with info5:

                st.markdown(
                    "**Equipment / Station ID**"
                )

                st.write(
                    finding_record[
                        "equipment_id"
                    ]
                    or "-"
                )


            with info6:

                st.markdown(
                    "**Lot Number**"
                )

                st.write(
                    finding_record[
                        "lot_number"
                    ]
                    or "-"
                )


            with info7:

                st.markdown(
                    "**Shift**"
                )

                st.write(
                    finding_record["shift"]
                    or "-"
                )


            with info8:

                st.markdown(
                    "**Status**"
                )

                st.write(
                    finding_record["status"]
                    or "-"
                )


            st.divider()


            # ====================================================
            # FINDING DETAILS
            # ====================================================

            st.markdown(
                "### Finding Details"
            )


            show_detail_value(
                "Category",
                finding_record["category"]
            )


            show_detail_value(
                "Finding Description",
                finding_record["finding_description"]
            )


            show_detail_value(
                "Interview Result",
                finding_record["interview_result"]
            )


            show_detail_value(
                "Containment Action",
                finding_record["containment_action"]
            )


            detail1, detail2 = st.columns(
                2
            )


            with detail1:

                show_detail_value(
                    "Auditee",
                    finding_record["auditee"]
                )


            with detail2:

                show_detail_value(
                    "Auditor",
                    finding_record["auditor"]
                )
