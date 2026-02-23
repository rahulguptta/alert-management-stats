import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:

    # ================= READ FILE =================
    # ================= READ FILE =================
    df_raw = pd.read_excel(uploaded_file, header=None)
    
    # Remove first row
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    
    # Second row becomes header
    df_raw.columns = df_raw.iloc[0]
    
    # Remove that header row from data
    df = df_raw.iloc[1:].reset_index(drop=True)
    
    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    # ================= SYSTEM NAME MAPPING =================
    system_mapping = {
        "COLD SECTIONS COLUMNS": "Column Section",
        "QUENCH SYSTEM": "Quench Tower",
        "CHARGE GAS COMPRESSOR": "CGC Section",
        "ACETYLENE REACTORS OPTIMIZATION": "Acetylene Reactors"
    }
    df["systemName"] = df["systemName"].replace(system_mapping)

    # ================= ASSIGNEE MAPPING =================
    assignee_mapping = {
        "PAVLOV ANDRES ROMERO PEREZ": "Parvaze Aalam",
        "Ahmed Hassan Ahmed Faqqas": "Ashawani Arora",
        "Omer Ali Abdullah AlAli": "John Doe Paul",
        "Talaal Salah Abdullah Alabdulkareem": "Rashmina Raj Kumari"
    }
    df["currentAssignee"] = df["currentAssignee"].replace(assignee_mapping)
    df["lastActionTakenBy"] = df["lastActionTakenBy"].replace(assignee_mapping)

    # ================= ROLE CREATION FROM stageID =================
    role_mapping = {
        1: "Process Engineer",
        2: "Process Manager",
        3: "Operation Engineer",
        4: "Operation Engineer",
    }
    df["stageID"] = pd.to_numeric(df["stageID"], errors="coerce")
    df["Role"] = df["stageID"].map(role_mapping)

    # ================= DATETIME CONVERSION =================
    df["deviationTime"] = pd.to_datetime(df["deviationTime"], errors="coerce")

    # ================= REMOVE CLOSED FOR CHARTS =================
    df_active = df[~df["status"].str.lower().str.contains("closed", na=False)]

    # ================= SIDEBAR =================
    st.sidebar.header("Filters")

    min_date = df["deviationTime"].min()
    max_date = df["deviationTime"].max()

    period = st.sidebar.date_input(
        "Select Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    start_date, end_date = period

    affiliates = sorted(df["systemName"].dropna().unique())
    affiliate_selected = st.sidebar.selectbox(
        "Select Affiliate",
        ["All"] + list(affiliates),
        index=0
    )

    df_filtered = df[
        (df["deviationTime"] >= pd.to_datetime(start_date)) &
        (df["deviationTime"] <= pd.to_datetime(end_date))
    ]

    df_active_filtered = df_active[
        (df_active["deviationTime"] >= pd.to_datetime(start_date)) &
        (df_active["deviationTime"] <= pd.to_datetime(end_date))
    ]

    if affiliate_selected != "All":
        df_filtered = df_filtered[df_filtered["systemName"] == affiliate_selected]
        df_active_filtered = df_active_filtered[
            df_active_filtered["systemName"] == affiliate_selected
        ]

    # ================= TABS =================
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management"]
    )

    # ================= OVERVIEW =================
    with tab1:

        st.subheader("Active Alerts Overview")

        chart_df = (
            df_active_filtered
            .groupby(["systemName", "status"])
            .size()
            .reset_index(name="Count")
        )

        fig = px.bar(
            chart_df,
            x="systemName",
            y="Count",
            color="status",
            barmode="stack",
            text="Count"
        )

        fig.update_layout(xaxis_title="", yaxis_title="Active Alerts")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Overall Status Statistics")

        overall_stats = (
            df_filtered["status"]
            .value_counts()
            .reset_index()
        )
        overall_stats.columns = ["Status", "Count"]
        st.dataframe(overall_stats, use_container_width=True)

    # ================= ALERT STATISTICS =================
    with tab2:

        st.subheader("Alert Statistics")

        df_filtered["MonthDisplay"] = df_filtered["deviationTime"].dt.strftime("%B %Y")
        df_filtered["MonthSort"] = df_filtered["deviationTime"].dt.to_period("M")

        month_df = (
            df_filtered[["MonthDisplay", "MonthSort"]]
            .drop_duplicates()
            .sort_values("MonthSort")
        )

        month_options = ["All"] + month_df["MonthDisplay"].tolist()
        selected_month = st.selectbox("Select Month", month_options, index=0)

        if selected_month == "All":
            df_month = df_filtered.copy()
        else:
            df_month = df_filtered[df_filtered["MonthDisplay"] == selected_month]

        status_lower = df_month["status"].str.lower()

        total_generated = len(df_month)
        total_closed = df_month[status_lower.str.contains("closed", na=False)].shape[0]
        total_active = total_generated - total_closed

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Alerts", total_generated)
        col2.metric("Total Active", total_active)
        col3.metric("Total Closed", total_closed)

        st.markdown("---")

        st.markdown("### Active Alerts by Role")

        df_active_month = df_month[~status_lower.str.contains("closed", na=False)]

        role_df = (
            df_active_month
            .groupby("Role")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )

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

    # ================= ALERT MANAGEMENT =================
    with tab3:

        st.subheader("Alert Management")

        category = st.selectbox(
            "Category",
            ["All", "Energy", "Production", "Environment"]
        )

        deviation = st.selectbox(
            "Deviation",
            ["All", "Pending"]
        )

        df_manage = df_filtered.copy()

        if category == "Energy":
            df_manage = df_manage[
                df_manage["odsCauseTagName"].str.contains("energy", case=False, na=False)
            ]
        elif category == "Production":
            df_manage = df_manage[
                df_manage["odsCauseTagName"].str.contains(
                    "production|output|throughput|rate",
                    case=False,
                    na=False
                )
            ]
        elif category == "Environment":
            df_manage = df_manage[
                df_manage["odsCauseTagName"].str.contains(
                    "environment|emission|waste|pollution",
                    case=False,
                    na=False
                )
            ]

        if deviation == "Pending":
            df_manage = df_manage[
                df_manage["status"].str.contains("pending", case=False, na=False)
            ]

        display_cols = [
            "requestID",
            "systemName",
            "causeMessage",
            "odsCauseTagName",
            "status"
        ]

        df_display = df_manage[display_cols].copy()
        df_display.columns = [
            "Alert ID",
            "System",
            "Cause",
            "KPI (Request ID)",
            "Status"
        ]

        st.dataframe(df_display, use_container_width=True)

        st.markdown("### Comments")

        for _, row in df_manage.iterrows():
            with st.expander(f"View Comments - Alert {row['requestID']}"):
                st.write(row.get("comments", "No Comments"))
