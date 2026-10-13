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
            "finding_datetime_ts,"
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
            "dashboard_include,"
            "corrective_action,"
            "corrective_action_by,"
            "corrective_action_at,"
            "corrective_action_due_date,"
            "corrective_action_completed,"
            "corrective_action_completed_by,"
            "corrective_action_completed_at"
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

checklist_history_df["ca_status"] = "-"

# ============================================================
# NORMALIZE FINDING RECORDS
# ============================================================

if not findings_df.empty:

    findings_df["finding_datetime_ts"] = pd.to_datetime(
        findings_df["finding_datetime_ts"],
        format="mixed",
        errors="coerce",
        utc=True
    )

    findings_df["created_at"] = pd.to_datetime(
        findings_df["created_at"],
        format="mixed",
        errors="coerce",
        utc=True
    )


    # Canonical Finding timestamp.
    # created_at is retained only as fallback for older records
    # where finding_datetime_ts may be missing.
    findings_df["record_datetime"] = (
        findings_df["finding_datetime_ts"]
        .fillna(
            findings_df["created_at"]
        )
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
    # ========================================================
    # CORRECTIVE ACTION STATUS
    # ========================================================

    def get_ca_status(row):

        finding_status = str(
            row.get("status", "")
        ).strip().upper()

        # Corrective Action only starts after Tech Review.
        if finding_status != "CONFIRMED":
        
            return "-"
        
        
        # Completed CA takes priority over all other CA statuses.
        corrective_action_completed = row.get(
            "corrective_action_completed"
        )
        
        if (
            pd.notna(corrective_action_completed)
            and bool(corrective_action_completed)
        ):
        
            return "COMPLETED"
        
        
        corrective_action = row.get(
            "corrective_action"
        )
        
        # Tech Review completed, but no CA submitted.
        if (
            pd.isna(corrective_action)
            or not str(corrective_action).strip()
        ):
        
            return "PENDING CA"
        
        corrective_action = str(
            corrective_action
        ).strip()

        due_date = row.get(
            "corrective_action_due_date"
        )

        # CA exists but no committed completion date.
        if pd.isna(due_date) or not str(due_date).strip():

            return "ON-GOING"

        try:

            parsed_due_date = pd.to_datetime(
                due_date,
                errors="coerce"
            )

            if pd.isna(parsed_due_date):

                return "ON-GOING"

            due_date = parsed_due_date.date()

        except Exception:

            return "ON-GOING"

        # Due date itself is still ON-GOING.
        # It becomes OVERDUE starting the following day.
        if current_time.date() > due_date:

            return "OVERDUE"

        return "ON-GOING"


    finding_history_df["ca_status"] = (
        findings_df.apply(
            get_ca_status,
            axis=1
        )
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


filter5, filter6, filter7, filter8, filter9, filter10 = st.columns(
    6
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

    ca_status_options = [
        "All",
        "PENDING CA",
        "ON-GOING",
        "OVERDUE",
        "COMPLETED"
    ]

    selected_ca_status = st.selectbox(
        "CA Status",
        ca_status_options
    )


with filter9:

    dashboard_options = [
        "All",
        "Tick",
        "Untick"
    ]

    selected_dashboard = st.selectbox(
        "Dashboard",
        dashboard_options
    )


with filter10:

    inspector_search = st.text_input(
        "Inspector / Auditor",
        placeholder="6-digit badge"
    )


filter11, filter12, filter13 = st.columns(
    3
)


with filter11:

    lot_search = st.text_input(
        "Lot Number",
        placeholder="Search lot"
    )


with filter12:

    machine_search = st.text_input(
        "Machine / Workstation",
        placeholder="Search machine"
    )


with filter13:

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


if selected_ca_status != "All":

    filtered_df = filtered_df[
        filtered_df["ca_status"]
        == selected_ca_status
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
display_df["CA Status"] = (
    display_df["ca_status"]
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
    "CA Status",
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
            default=False,
            width="small"
        ),
    
        "Date / Time": st.column_config.TextColumn(
            "Date / Time",
            width=145
        ),
    
        "Record No.": st.column_config.TextColumn(
            "Record No.",
            width="small"
        ),
    
        "Record Type": st.column_config.TextColumn(
            "Record Type",
            width="small"
        ),
    
        "Factory": st.column_config.TextColumn(
            "Factory",
            width="small"
        ),
    
        "Area": st.column_config.TextColumn(
            "Area",
            width="small"
        ),
    
        "Process / Station": st.column_config.TextColumn(
            "Process / Station",
            width="medium"
        ),
    
        "Lot Number": st.column_config.TextColumn(
            "Lot Number",
            width="small"
        ),
    
        "Machine / Workstation": st.column_config.TextColumn(
            "Machine / Workstation",
            width="small"
        ),
    
        "Inspector / Auditor": st.column_config.TextColumn(
            "Inspector / Auditor",
            width="small"
        ),
    
        "Shift": st.column_config.TextColumn(
            "Shift",
            width="small"
        ),
    
        "Type / Status": st.column_config.TextColumn(
            "Type / Status",
            width="small"
        ),
    
        "CA Status": st.column_config.TextColumn(
            "CA Status",
            width=105
        ),
    
        "Dashboard": st.column_config.CheckboxColumn(
            "Dashboard",
            width="small"
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
        "Type / Status",
        "CA Status"
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
            margin-bottom:2px;
        ">
            {label}
        </div>

        <div style="
            color:{TEXT};
            font-size:16px;
            font-weight:500;
            line-height:1.3;
            margin-bottom:6px;
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
                
                    finding_datetime_display = (
                        finding_record.get(
                            "record_datetime"
                        )
                    )
                
                    if pd.isna(finding_datetime_display):
                
                        finding_datetime_display = "-"
                
                    else:
                
                        finding_datetime_display = (
                            finding_datetime_display.strftime(
                                "%d-%b-%Y %H:%M:%S"
                            )
                        )
                
                    st.write(
                        finding_datetime_display
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
                        "### Reviewed By"
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
                        "### Reviewed By"
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
                                            # ============================================
                    # CORRECTIVE ACTION
                    # ============================================

                    st.divider()

                    st.markdown(
                        "### Corrective Action"
                    )

                    existing_corrective_action = (
                        finding_record.get(
                            "corrective_action"
                        )
                    )

                    existing_corrective_action_by = (
                        finding_record.get(
                            "corrective_action_by"
                        )
                    )

                    ca_exists = (
                        pd.notna(existing_corrective_action)
                        and bool(
                            str(
                                existing_corrective_action
                            ).strip()
                        )
                    )


                    # ============================================
                    # CA NOT YET SUBMITTED
                    # ============================================

                    if not ca_exists:

                        corrective_action = st.text_area(
                            "Corrective Action",
                            placeholder=(
                                "Enter corrective action taken..."
                            ),
                            height=120,
                            key=f"corrective_action_{finding_id}"
                        )

                        corrective_col1, corrective_col2 = (
                            st.columns(2)
                        )


                        with corrective_col1:

                            corrective_action_by = st.text_input(
                                "Completed By",
                                placeholder="Enter name",
                                key=f"corrective_action_by_{finding_id}"
                            )


                        with corrective_col2:

                            corrective_action_due_date = st.date_input(
                                "Committed Completion Date",
                                value=current_time.date(),
                                key=(
                                    f"corrective_action_due_date_"
                                    f"{finding_id}"
                                )
                            )


                        save_corrective_action = st.button(
                            "Save Corrective Action",
                            type="primary",
                            width="stretch",
                            key=f"save_corrective_action_{finding_id}"
                        )


                        if save_corrective_action:

                            if not corrective_action.strip():

                                st.error(
                                    "Please enter the Corrective Action."
                                )

                            elif not corrective_action_by.strip():

                                st.error(
                                    "Please enter Completed By."
                                )

                            else:

                                corrective_action_datetime = (
                                    datetime.now(
                                        MALAYSIA_TZ
                                    )
                                )

                                try:

                                    (
                                        supabase
                                        .table("Findings")
                                        .update(
                                            {
                                                "corrective_action":
                                                    corrective_action.strip(),

                                                "corrective_action_by":
                                                    corrective_action_by.strip(),

                                                "corrective_action_due_date":
                                                    corrective_action_due_date.isoformat(),

                                                "corrective_action_at":
                                                    corrective_action_datetime.isoformat()
                                            }
                                        )
                                        .eq(
                                            "id",
                                            int(finding_id)
                                        )
                                        .execute()
                                    )

                                    st.success(
                                        "Corrective Action saved."
                                    )

                                    st.rerun()

                                except Exception as e:

                                    st.error(
                                        "Unable to save Corrective Action."
                                    )

                                    st.exception(e)


                    # ============================================
                    # CA ALREADY SUBMITTED
                    # ============================================

                    else:
                    
                        ca_completed_value = finding_record.get(
                            "corrective_action_completed"
                        )
                    
                        ca_completed = (
                            pd.notna(ca_completed_value)
                            and bool(ca_completed_value)
                        )
                    
                        ca_edit_key = (
                            f"edit_corrective_action_{finding_id}"
                        )
                        if ca_edit_key not in st.session_state:

                            st.session_state[
                                ca_edit_key
                            ] = False


                        # ========================================
                        # READ-ONLY CA
                        # ========================================

                        if not st.session_state[
                            ca_edit_key
                        ]:
                                                        # ========================================
                            # CONFIRM CA COMPLETION
                            # ========================================

                            confirm_ca_key = (
                                f"confirm_ca_mode_{finding_id}"
                            )

                            if confirm_ca_key not in st.session_state:

                                st.session_state[
                                    confirm_ca_key
                                ] = False


                            if st.session_state[
                                confirm_ca_key
                            ]:

                                st.markdown("")

                                st.markdown(
                                    "#### Confirm Corrective Action Completion"
                                )

                                st.caption(
                                    "Enter the technician badge to confirm "
                                    "that the Corrective Action is completed."
                                )


                                ca_confirmation_badge = st.text_input(
                                    "Confirmation By",
                                    placeholder="6-digit technician badge",
                                    max_chars=6,
                                    key=(
                                        f"ca_confirmation_badge_"
                                        f"{finding_id}"
                                    )
                                )


                                confirm_col1, confirm_col2 = (
                                    st.columns(2)
                                )


                                with confirm_col1:

                                    final_confirm_ca = st.button(
                                        "Confirm Completed",
                                        type="primary",
                                        width="stretch",
                                        key=(
                                            f"final_confirm_ca_"
                                            f"{finding_id}"
                                        )
                                    )


                                with confirm_col2:

                                    cancel_confirm_ca = st.button(
                                        "Cancel",
                                        width="stretch",
                                        key=(
                                            f"cancel_confirm_ca_"
                                            f"{finding_id}"
                                        )
                                    )


                                if cancel_confirm_ca:

                                    st.session_state[
                                        confirm_ca_key
                                    ] = False

                                    st.rerun()


                                if final_confirm_ca:

                                    confirmation_badge = (
                                        ca_confirmation_badge.strip()
                                    )


                                    if (
                                        not confirmation_badge.isdigit()
                                        or len(
                                            confirmation_badge
                                        ) != 6
                                    ):

                                        st.error(
                                            "Confirmation By must be "
                                            "six (6) numerical digits."
                                        )

                                    else:

                                        completed_datetime = (
                                            datetime.now(
                                                MALAYSIA_TZ
                                            )
                                        )

                                        try:

                                            (
                                                supabase
                                                .table("Findings")
                                                .update(
                                                    {
                                                        "corrective_action_completed":
                                                            True,

                                                        "corrective_action_completed_by":
                                                            confirmation_badge,

                                                        "corrective_action_completed_at":
                                                            completed_datetime.isoformat()
                                                    }
                                                )
                                                .eq(
                                                    "id",
                                                    int(finding_id)
                                                )
                                                .eq(
                                                    "status",
                                                    "CONFIRMED"
                                                )
                                                .execute()
                                            )


                                            st.session_state[
                                                confirm_ca_key
                                            ] = False

                                            st.success(
                                                "Corrective Action "
                                                "confirmed as completed."
                                            )

                                            st.rerun()


                                        except Exception as e:

                                            st.error(
                                                "Unable to confirm "
                                                "Corrective Action completion."
                                            )

                                            st.exception(e)

                            show_detail_value(
                                "Corrective Action",
                                existing_corrective_action
                            )

                            ca_detail1, ca_detail2 = (
                                st.columns(2)
                            )


                            with ca_detail1:

                                show_detail_value(
                                    "Completed By",
                                    existing_corrective_action_by
                                )


                            with ca_detail2:

                                existing_due_date = (
                                    finding_record.get(
                                        "corrective_action_due_date"
                                    )
                                )

                                if pd.isna(
                                    existing_due_date
                                ):

                                    due_date_display = "-"

                                else:

                                    try:

                                        due_date_display = (
                                            pd.to_datetime(
                                                existing_due_date
                                            )
                                            .strftime(
                                                "%d-%b-%Y"
                                            )
                                        )

                                    except Exception:

                                        due_date_display = (
                                            str(
                                                existing_due_date
                                            )
                                        )


                                show_detail_value(
                                    "Committed Completion Date",
                                    due_date_display
                                )


                            # ========================================
                            # COMPLETED CA
                            # ========================================

                            if ca_completed:

                                st.markdown(
                                    "#### CA Completion"
                                )

                                completed_by = finding_record.get(
                                    "corrective_action_completed_by"
                                )

                                completed_at = finding_record.get(
                                    "corrective_action_completed_at"
                                )


                                if (
                                    pd.isna(completed_by)
                                    or not str(completed_by).strip()
                                ):

                                    completed_by_display = "-"

                                else:

                                    completed_by_display = str(
                                        completed_by
                                    )


                                if (
                                    pd.isna(completed_at)
                                    or not str(completed_at).strip()
                                ):

                                    completed_at_display = "-"

                                else:

                                    try:

                                        completed_at_display = (
                                            pd.to_datetime(
                                                completed_at,
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

                                        completed_at_display = str(
                                            completed_at
                                        )


                                completion_col1, completion_col2 = (
                                    st.columns(2)
                                )


                                with completion_col1:

                                    show_detail_value(
                                        "Confirmed By",
                                        completed_by_display
                                    )


                                with completion_col2:

                                    show_detail_value(
                                        "Confirmed At",
                                        completed_at_display
                                    )


                            # ========================================
                            # OPEN CA
                            # ========================================

                            else:

                                ca_button1, ca_button2 = (
                                    st.columns(2)
                                )


                                with ca_button1:

                                    if st.button(
                                        "Edit Corrective Action",
                                        width="stretch",
                                        key=(
                                            f"edit_ca_button_"
                                            f"{finding_id}"
                                        )
                                    ):

                                        st.session_state[
                                            ca_edit_key
                                        ] = True

                                        st.rerun()


                                with ca_button2:

                                    if st.button(
                                        "Confirm CA Completed",
                                        type="primary",
                                        width="stretch",
                                        key=(
                                            f"confirm_ca_button_"
                                            f"{finding_id}"
                                        )
                                    ):

                                        st.session_state[
                                            f"confirm_ca_mode_{finding_id}"
                                        ] = True

                                        st.rerun()


                                # ====================================
                                # CONFIRM CA COMPLETION
                                # ====================================

                                confirm_ca_key = (
                                    f"confirm_ca_mode_{finding_id}"
                                )

                                if confirm_ca_key not in st.session_state:

                                    st.session_state[
                                        confirm_ca_key
                                    ] = False


                                if st.session_state[
                                    confirm_ca_key
                                ]:

                                    st.markdown("")

                                    st.markdown(
                                        "#### Confirm Corrective Action Completion"
                                    )

                                    st.caption(
                                        "Enter the technician badge to confirm "
                                        "that the Corrective Action is completed."
                                    )


                                    ca_confirmation_badge = st.text_input(
                                        "Confirmation By",
                                        placeholder="6-digit technician badge",
                                        max_chars=6,
                                        key=(
                                            f"ca_confirmation_badge_"
                                            f"{finding_id}"
                                        )
                                    )


                                    confirm_col1, confirm_col2 = (
                                        st.columns(2)
                                    )


                                    with confirm_col1:

                                        final_confirm_ca = st.button(
                                            "Confirm Completed",
                                            type="primary",
                                            width="stretch",
                                            key=(
                                                f"final_confirm_ca_"
                                                f"{finding_id}"
                                            )
                                        )


                                    with confirm_col2:

                                        cancel_confirm_ca = st.button(
                                            "Cancel",
                                            width="stretch",
                                            key=(
                                                f"cancel_confirm_ca_"
                                                f"{finding_id}"
                                            )
                                        )


                                    if cancel_confirm_ca:

                                        st.session_state[
                                            confirm_ca_key
                                        ] = False

                                        st.rerun()


                                    if final_confirm_ca:

                                        confirmation_badge = (
                                            ca_confirmation_badge.strip()
                                        )


                                        if (
                                            not confirmation_badge.isdigit()
                                            or len(
                                                confirmation_badge
                                            ) != 6
                                        ):

                                            st.error(
                                                "Confirmation By must be "
                                                "six (6) numerical digits."
                                            )

                                        else:

                                            completed_datetime = (
                                                datetime.now(
                                                    MALAYSIA_TZ
                                                )
                                            )

                                            try:

                                                (
                                                    supabase
                                                    .table("Findings")
                                                    .update(
                                                        {
                                                            "corrective_action_completed":
                                                                True,

                                                            "corrective_action_completed_by":
                                                                confirmation_badge,

                                                            "corrective_action_completed_at":
                                                                completed_datetime.isoformat()
                                                        }
                                                    )
                                                    .eq(
                                                        "id",
                                                        int(finding_id)
                                                    )
                                                    .eq(
                                                        "status",
                                                        "CONFIRMED"
                                                    )
                                                    .execute()
                                                )


                                                st.session_state[
                                                    confirm_ca_key
                                                ] = False

                                                st.success(
                                                    "Corrective Action "
                                                    "confirmed as completed."
                                                )

                                                st.rerun()


                                            except Exception as e:

                                                st.error(
                                                    "Unable to confirm "
                                                    "Corrective Action completion."
                                                )

                                                st.exception(e)

                        # ========================================
                        # EDIT EXISTING CA
                        # ========================================

                        else:

                            corrective_action = st.text_area(
                                "Corrective Action",
                                value=str(
                                    existing_corrective_action
                                ),
                                height=120,
                                key=(
                                    f"edit_corrective_action_text_"
                                    f"{finding_id}"
                                )
                            )


                            corrective_col1, corrective_col2 = (
                                st.columns(2)
                            )


                            with corrective_col1:

                                corrective_action_by = (
                                    st.text_input(
                                        "Completed By",
                                        value=(
                                            ""
                                            if pd.isna(
                                                existing_corrective_action_by
                                            )
                                            else str(
                                                existing_corrective_action_by
                                            )
                                        ),
                                        key=(
                                            f"edit_corrective_action_by_"
                                            f"{finding_id}"
                                        )
                                    )
                                )


                            with corrective_col2:

                                existing_due_date = (
                                    finding_record.get(
                                        "corrective_action_due_date"
                                    )
                                )

                                if (
                                    pd.isna(existing_due_date)
                                    or not str(
                                        existing_due_date
                                    ).strip()
                                ):

                                    existing_due_date = (
                                        current_time.date()
                                    )

                                else:

                                    parsed_due_date = (
                                        pd.to_datetime(
                                            existing_due_date,
                                            errors="coerce"
                                        )
                                    )

                                    if pd.isna(
                                        parsed_due_date
                                    ):

                                        existing_due_date = (
                                            current_time.date()
                                        )

                                    else:

                                        existing_due_date = (
                                            parsed_due_date.date()
                                        )


                                corrective_action_due_date = (
                                    st.date_input(
                                        "Committed Completion Date",
                                        value=existing_due_date,
                                        key=(
                                            f"edit_corrective_action_due_date_"
                                            f"{finding_id}"
                                        )
                                    )
                                )


                            edit_button1, edit_button2 = (
                                st.columns(2)
                            )


                            with edit_button1:

                                save_changes = st.button(
                                    "Save Changes",
                                    type="primary",
                                    width="stretch",
                                    key=(
                                        f"save_ca_changes_"
                                        f"{finding_id}"
                                    )
                                )


                            with edit_button2:

                                cancel_edit = st.button(
                                    "Cancel",
                                    width="stretch",
                                    key=(
                                        f"cancel_ca_edit_"
                                        f"{finding_id}"
                                    )
                                )


                            if cancel_edit:

                                st.session_state[
                                    ca_edit_key
                                ] = False

                                st.rerun()


                            if save_changes:

                                if not corrective_action.strip():

                                    st.error(
                                        "Please enter the Corrective Action."
                                    )

                                elif not corrective_action_by.strip():

                                    st.error(
                                        "Please enter Completed By."
                                    )

                                else:

                                    try:

                                        (
                                            supabase
                                            .table("Findings")
                                            .update(
                                                {
                                                    "corrective_action":
                                                        corrective_action.strip(),

                                                    "corrective_action_by":
                                                        corrective_action_by.strip(),

                                                    "corrective_action_due_date":
                                                        corrective_action_due_date.isoformat(),

                                                    "corrective_action_at":
                                                        datetime.now(
                                                            MALAYSIA_TZ
                                                        ).isoformat()
                                                }
                                            )
                                            .eq(
                                                "id",
                                                int(finding_id)
                                            )
                                            .execute()
                                        )

                                        st.session_state[
                                            ca_edit_key
                                        ] = False

                                        st.success(
                                            "Corrective Action updated."
                                        )

                                        st.rerun()

                                    except Exception as e:

                                        st.error(
                                            "Unable to update "
                                            "Corrective Action."
                                        )

                                        st.exception(e)
