import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# ===================== LOAD DATA =====================
df = pd.read_excel("output.xlsx")

# Required Columns
required_cols = ["deviationTime", "systemName", "status", "currentAssignee"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}")
        st.stop()

# Convert date
df["deviationTime"] = pd.to_datetime(df["deviationTime"], errors="coerce")
df = df.dropna(subset=["deviationTime"])

# ===================== SIDEBAR FILTERS =====================
st.sidebar.header("Filters")

# Affiliate Filter
affiliates = ["ALL"] + sorted(df["systemName"].dropna().unique().tolist())
selected_affiliate = st.sidebar.selectbox("System", affiliates)

# Date Filter
min_date = df["deviationTime"].min().date()
max_date = df["deviationTime"].max().date()

start_date = st.sidebar.date_input("From", min_date)
end_date = st.sidebar.date_input("To", max_date)

# Apply Period Filter
df_filtered = df[
    (df["deviationTime"].dt.date >= start_date) &
    (df["deviationTime"].dt.date <= end_date)
]

# Apply Affiliate Filter
if selected_affiliate != "ALL":
    df_filtered = df_filtered[df_filtered["systemName"] == selected_affiliate]

# ===================== TABS =====================
tab1, tab2 = st.tabs(["Overview", "Alert Statistics"])

# ==========================================================
# ===================== OVERVIEW (FROZEN) ==================
# ==========================================================
with tab1:
    st.title("Overview Page (Frozen)")
    st.info("Overview remains unchanged as requested.")

# ==========================================================
# ================= ALERT STATISTICS =======================
# ==========================================================
with tab2:

    st.title("Alert Statistics")

    if df_filtered.empty:
        st.warning("No data available for selected filters.")
        st.stop()

    # ================= MONTH FILTER =================
    df_filtered["YearMonth"] = df_filtered["deviationTime"].dt.to_period("M").astype(str)
    months = sorted(df_filtered["YearMonth"].unique().tolist())

    month_options = ["All"] + months
    selected_month = st.selectbox("Select Month", month_options, index=0)

    if selected_month == "All":
        df_month = df_filtered.copy()
    else:
        df_month = df_filtered[df_filtered["YearMonth"] == selected_month]

    if df_month.empty:
        st.warning("No data for selected month.")
        st.stop()

    # ================= KPIs =================
    total_generated = len(df_month)

    active_mask = ~df_month["status"].str.lower().str.contains("closed", na=False)
    df_active = df_month[active_mask]

    total_active = len(df_active)
    total_closed = total_generated - total_active

    col1, col2, col3 = st.columns(3)

    col1.metric("Generated Alerts", total_generated)
    col2.metric("Active Alerts", total_active)
    col3.metric("Closed Alerts", total_closed)

    # ================= ACTIVE ALERTS BY ROLE =================
    st.markdown("### Active Alerts by Role")

    role_mapping = {
        'James Anderson': 'Process Engineer',
        'Ahmed El-Sayed': 'Process Manager',
        'Chen Wei': 'Operation Engineer',
        'Lucas Silva': 'Operation Manager',
        'Arjun Mehta': 'Operation Engineer'
    }

    df_active["Role"] = df_active["currentAssignee"].map(role_mapping)
    df_active["Role"] = df_active["Role"].fillna("Other")

    role_df = (
        df_active
        .groupby("Role")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    if role_df.empty:
        st.info("No active alerts in selected month.")
    else:
        fig_role = px.bar(
            role_df,
            x="Role",
            y="Count",
            text="Count"
        )

        fig_role.update_layout(
            xaxis_title="Role",
            yaxis_title="Active Alerts",
            xaxis=dict(type="category")
        )

        st.plotly_chart(fig_role, use_container_width=True)
