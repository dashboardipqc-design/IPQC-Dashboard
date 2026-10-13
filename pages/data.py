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
            "status,"
            "severity,"
            "reviewed_by,"
            "reviewed_at,"
            "dashboard_include"
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

    st.markdown(
        "<div style='height: 28px;'></div>",
        unsafe_allow_html=True
    )

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

checklist_history_df["dashboard_include"] = True

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
        findings_df.apply(
            lambda row:
                row["severity"]
                if (
                    str(row["status"]).strip().upper()
                    == "CONFIRMED"
                    and
                    row.get("severity")
                )
                else row["status"],
            axis=1
        )
    )

    finding_history_df["dashboard_include"] = (
        findings_df["dashboard_include"]
        .fillna(True)
        .astype(bool)
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


filter5, filter6, filter7, filter8, filter9 = st.columns(
    5
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

    dashboard_options = [
        "All",
        "Tick",
        "Untick"
    ]

    selected_dashboard = st.selectbox(
        "Dashboard",
        dashboard_options
    )


with filter9:

    inspector_search = st.text_input(
        "Inspector / Auditor",
        placeholder="6-digit badge"
    )
filter10, filter11, filter12 = st.columns(
    3
)


with filter10:

    lot_search = st.text_input(
        "Lot Number",
        placeholder="Search lot"
    )


with filter11:

    machine_search = st.text_input(
        "Machine / Workstation",
        placeholder="Search machine"
    )


with filter12:

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


if selected_dashboard == "Tick":

    filtered_df = filtered_df[
        filtered_df["dashboard_include"]
        .fillna(False)
        .astype(bool)
    ]


elif selected_dashboard == "Untick":

    filtered_df = filtered_df[
        ~filtered_df["dashboard_include"]
        .fillna(False)
        .astype(bool)
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

# ============================================================
# SINGLE OPEN ROW STATE
# ============================================================

if "history_open_record" not in st.session_state:
    st.session_state.history_open_record = None

if "history_editor_version" not in st.session_state:
    st.session_state.history_editor_version = 0


# Clear the selection if the selected record is no longer
# visible on the current page.
visible_record_numbers = (
    page_df["record_no"]
    .astype(str)
    .tolist()
)

if (
    st.session_state.history_open_record is not None
    and st.session_state.history_open_record
    not in visible_record_numbers
):

    st.session_state.history_open_record = None


display_df = page_df.copy()


# Only one row can be Open at a time.
display_df["Open"] = (
    display_df["record_no"]
    .astype(str)
    == st.session_state.history_open_record
)


display_df["Date / Time"] = (
    display_df["record_datetime"]
    .dt.strftime(
        "%d-%b-%Y %H:%M"
    )
)

display_df["Dashboard"] = (
    display_df["dashboard_include"]
    .fillna(True)
    .astype(bool)
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
    "Open",
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
    "Type / Status",
    "Dashboard"
]


table_height = min(
    500,
    38 + (len(display_df) * 35)
)


edited_df = st.data_editor(
    display_df[
        display_columns
    ],
    width="stretch",
    hide_index=True,
    height=table_height,
    key=(
        "ipqc_history_editor_"
        f"{st.session_state.history_editor_version}"
    ),
    column_config={
        "Open": st.column_config.CheckboxColumn(
            "-",
            default=False
        ),
        "Dashboard": st.column_config.CheckboxColumn(
            "Dashboard"
        )
    },
    disabled=[
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
)


# ============================================================
# SINGLE OPEN ROW CONTROL
# ============================================================

original_open = (
    display_df["Open"]
    .fillna(False)
    .astype(bool)
    .reset_index(drop=True)
)

edited_open = (
    edited_df["Open"]
    .fillna(False)
    .astype(bool)
    .reset_index(drop=True)
)


open_changed_rows = [
    row_position
    for row_position in range(
        len(edited_df)
    )
    if (
        bool(
            edited_open.iloc[
                row_position
            ]
        )
        !=
        bool(
            original_open.iloc[
                row_position
            ]
        )
    )
]


if open_changed_rows:

    changed_row_position = (
        open_changed_rows[-1]
    )

    changed_record_no = str(
        page_df.iloc[
            changed_row_position
        ]["record_no"]
    )


    # User ticked a new row.
    if bool(
        edited_open.iloc[
            changed_row_position
        ]
    ):

        st.session_state.history_open_record = (
            changed_record_no
        )


    # User unticked the currently selected row.
    elif (
        st.session_state.history_open_record
        == changed_record_no
    ):

        st.session_state.history_open_record = None


    # Use a fresh editor instance so its displayed
    # checkbox state is rebuilt from history_open_record.
    st.session_state.history_editor_version += 1

    st.rerun()
# ============================================================
# DASHBOARD TABLE CONTROL
# ============================================================

for row_position in range(
    len(edited_df)
):

    original_record = page_df.iloc[
        row_position
    ]

    original_value = bool(
        original_record[
            "dashboard_include"
        ]
    )

    edited_value = bool(
        edited_df.iloc[
            row_position
        ]["Dashboard"]
    )


    # --------------------------------------------------------
    # CHECKLIST
    # Dashboard is permanently included
    # --------------------------------------------------------

    if (
        original_record["record_type"]
        == "Checklist"
    ):

        continue


    # --------------------------------------------------------
    # FINDING
    # Pending Review cannot be included in Dashboard.
    # After Tech confirmation, Dashboard remains manually
    # editable regardless of Major / Minor classification.
    # --------------------------------------------------------

    finding_id = int(
        original_record[
            "source_id"
        ]
    )

    finding_match = findings_df[
        findings_df["id"]
        == finding_id
    ]


    if finding_match.empty:

        continue


    finding_status = str(
        finding_match.iloc[0]["status"]
    ).strip().upper()


    # Pending Review must remain excluded from Dashboard.
    if finding_status == "PENDING REVIEW":

        if edited_value:

            st.warning(
                "Pending Review Finding cannot be included "
                "in Dashboard until Tech Review is completed."
            )

            st.session_state.history_editor_version += 1

            st.rerun()

        continue


    # Confirmed Finding:
    # Dashboard checkbox remains manually editable.
    if edited_value != original_value:

        try:

            (
                supabase
                .table("Findings")
                .update(
                    {
                        "dashboard_include":
                            edited_value
                    }
                )
                .eq(
                    "id",
                    finding_id
                )
                .execute()
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Unable to update Dashboard setting."
            )

            st.exception(e)
            
# ============================================================
# PAGE NAVIGATION
# ============================================================

if total_pages > 1:

    st.markdown("")

    nav_left, nav_pages, nav_right, nav_space = st.columns(
        [1.2, 1.8, 1.2, 6]
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


# ============================================================
# SELECTED OPEN RECORD
# ============================================================

selected_record_no = (
    st.session_state.history_open_record
)


if selected_record_no is not None:

    selected_records = page_df[
        page_df["record_no"]
        .astype(str)
        == selected_record_no
    ]


    if not selected_records.empty:

        selected_record = (
            selected_records.iloc[0]
        )


        # ----------------------------------------------------
        # FINDING RECORD ONLY
        # ----------------------------------------------------

        if (
            selected_record["record_type"]
            == "Finding"
        ):

            finding_id = selected_record[
                "source_id"
            ]


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


                # ============================================
                # FINDING INFORMATION
                # ============================================

                st.markdown(
                    "### Finding Information"
                )


                info1, info2, info3, info4 = (
                    st.columns(4)
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


                info5, info6, info7, info8 = (
                    st.columns(4)
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


                # ============================================
                # FINDING DETAILS
                # ============================================

                st.markdown(
                    "### Finding Details"
                )


                show_detail_value(
                    "Category",
                    finding_record["category"]
                )


                show_detail_value(
                    "Finding Description",
                    finding_record[
                        "finding_description"
                    ]
                )


                show_detail_value(
                    "Interview Result",
                    finding_record[
                        "interview_result"
                    ]
                )


                show_detail_value(
                    "Containment Action",
                    finding_record[
                        "containment_action"
                    ]
                )


                detail1, detail2 = st.columns(
                    2
                )


                with detail1:

                    show_detail_value(
                        "Auditee",
                        finding_record[
                            "auditee"
                        ]
                    )


                with detail2:

                    show_detail_value(
                        "Auditor",
                        finding_record[
                            "auditor"
                        ]
                    )
                
                # ============================================
                # TECH REVIEW
                # ============================================

                finding_status = str(
                    finding_record.get(
                        "status",
                        ""
                    )
                ).strip().upper()


                if finding_status == "PENDING REVIEW":

                    st.divider()

                    st.markdown(
                        "### Tech Review"
                    )

                    st.caption(
                        "Confirm whether this Finding is "
                        "Minor or Major."
                    )


                    review_col1, review_col2 = st.columns(
                        2
                    )


                    with review_col1:

                        review_severity = st.radio(
                            "Severity",
                            [
                                "MINOR",
                                "MAJOR"
                            ],
                            index=None,
                            horizontal=True,
                            key=f"review_severity_{finding_id}"
                        )


                    with review_col2:

                        reviewer_badge = st.text_input(
                            "Technician Badge",
                            placeholder="6-digit badge",
                            max_chars=6,
                            key=f"reviewed_by_{finding_id}"
                        )


                    confirm_review = st.button(
                        "Confirm Review",
                        type="primary",
                        width="stretch",
                        key=f"confirm_review_{finding_id}"
                    )


                    if confirm_review:

                        # ------------------------------------
                        # VALIDATE SEVERITY
                        # ------------------------------------

                        if review_severity is None:

                            st.error(
                                "Please select Minor or Major."
                            )


                        # ------------------------------------
                        # VALIDATE TECHNICIAN BADGE
                        # ------------------------------------

                        elif (
                            not reviewer_badge.strip().isdigit()
                            or
                            len(
                                reviewer_badge.strip()
                            ) != 6
                        ):

                            st.error(
                                "Technician Badge must be "
                                "six (6) numerical digits."
                            )


                        else:

                            reviewed_datetime = datetime.now(
                                MALAYSIA_TZ
                            )


                            # --------------------------------
                            # DEFAULT DASHBOARD SETTING
                            # Minor = unticked
                            # Major = ticked
                            # --------------------------------

                            dashboard_include = (
                                review_severity
                                == "MAJOR"
                            )


                            try:

                                (
                                    supabase
                                    .table("Findings")
                                    .update(
                                        {
                                            "status":
                                                "CONFIRMED",

                                            "severity":
                                                review_severity,

                                            "reviewed_by":
                                                reviewer_badge.strip(),

                                            "reviewed_at":
                                                reviewed_datetime.isoformat(),

                                            "dashboard_include":
                                                dashboard_include
                                        }
                                    )
                                    .eq(
                                        "id",
                                        int(finding_id)
                                    )
                                    .eq(
                                        "status",
                                        "PENDING REVIEW"
                                    )
                                    .execute()
                                )


                                st.session_state.history_editor_version += 1

                                st.success(
                                    "Tech Review confirmed."
                                )

                                st.rerun()


                            except Exception as e:

                                st.error(
                                    "Unable to confirm Tech Review."
                                )

                                st.exception(e)


                # ============================================
                # COMPLETED TECH REVIEW
                # ============================================

                elif finding_status == "CONFIRMED":

                    st.divider()

                    st.markdown(
                        "### Tech Review"
                    )


                    review1, review2, review3 = st.columns(
                        3
                    )


                    with review1:

                        show_detail_value(
                            "Severity",
                            finding_record.get(
                                "severity"
                            )
                        )


                    with review2:

                        show_detail_value(
                            "Reviewed By",
                            finding_record.get(
                                "reviewed_by"
                            )
                        )


                    with review3:

                        reviewed_at = finding_record.get(
                            "reviewed_at"
                        )

                        if reviewed_at:

                            try:

                                reviewed_at_display = (
                                    pd.to_datetime(
                                        reviewed_at,
                                        utc=True
                                    )
                                    .tz_convert(
                                        MALAYSIA_TZ
                                    )
                                    .strftime(
                                        "%d-%b-%Y %H:%M"
                                    )
                                )

                            except Exception:

                                reviewed_at_display = (
                                    reviewed_at
                                )

                        else:

                            reviewed_at_display = "-"


                        show_detail_value(
                            "Reviewed At",
                            reviewed_at_display
                        )
