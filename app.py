import streamlit as st
import pandas as pd
from supabase import create_client


# ==========================================
# PAGE SETUP
# ==========================================

st.set_page_config(
    page_title="IPQC Finding Monitoring Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("IPQC Finding Monitoring Dashboard")
st.caption("IPQC Finding Trend & Closure Monitoring")


# ==========================================
# SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


supabase = init_supabase()


# ==========================================
# LOAD FINDINGS
# ==========================================

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


# ==========================================
# KPI CALCULATION
# ==========================================

total_findings = len(df)

if not df.empty and "status" in df.columns:

    status_clean = (
        df["status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    open_findings = (
        status_clean == "open"
    ).sum()

    closed_findings = (
        status_clean == "closed"
    ).sum()

else:

    open_findings = 0
    closed_findings = 0


if total_findings > 0:

    closure_rate = (
        closed_findings
        / total_findings
        * 100
    )

else:

    closure_rate = 0


# ==========================================
# KPI CARDS
# ==========================================

st.subheader("Finding Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Findings",
        total_findings
    )

with col2:
    st.metric(
        "Open Findings",
        int(open_findings)
    )

with col3:
    st.metric(
        "Closed Findings",
        int(closed_findings)
    )

with col4:
    st.metric(
        "Closure Rate",
        f"{closure_rate:.1f}%"
    )


# ==========================================
# DATABASE STATUS
# ==========================================

st.divider()

if df.empty:

    st.info(
        "No findings recorded yet."
    )

else:

    st.success(
        f"Successfully loaded {total_findings} finding(s) from Supabase."
    )


# ==========================================
# FINDING DATA
# ==========================================

st.subheader("Finding Records")

if not df.empty:

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.write(
        "Finding records will appear here once IPQC submits findings."
    )
