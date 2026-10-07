import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
# HEADER
# ============================================================

header1, header2 = st.columns(
    [4, 1]
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
        use_container_width=True
    ):

        st.switch_page(
            "app.py"
        )


st.divider()


# ============================================================
# PLACEHOLDER
# ============================================================

st.info(
    "Inspection History is ready for record retrieval setup."
)
