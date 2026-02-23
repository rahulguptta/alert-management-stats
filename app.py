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
        "Select System",
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
    # ================= Alert Statistics =================
    with tab2:

        st.subheader("Alert Statistics")
    
        if df_filtered.empty:
            st.warning("No data available for selected filters.")
            st.stop()
    
        # ================= MONTH FILTER =================
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
    
        # ================= STATUS CLASSIFICATION =================
        status_lower = df_month["status"].str.lower()
    
        total_generated = len(df_month)
    
        total_closed = df_month[status_lower.str.contains("closed", na=False)].shape[0]
        total_active = total_generated - total_closed
    
        pending = df_month[status_lower.str.contains("pending", na=False)].shape[0]
        implemented = df_month[status_lower.str.contains("implemented", na=False)].shape[0]
        rejected = df_month[status_lower.str.contains("rejected", na=False)].shape[0]
        wip = df_month[status_lower.str.contains("progress", na=False)].shape[0]
        overdue = df_month[status_lower.str.contains("overdue", na=False)].shape[0]
    
        auto_closed = df_month[df_month["status"].str.contains("System", case=False, na=False)].shape[0]
    
        # Overdue > 3 days logic (based on deviationTime vs today)
        overdue_3 = df_month[
            (status_lower.str.contains("overdue", na=False)) &
            ((pd.Timestamp.today() - df_month["deviationTime"]).dt.days > 3)
        ].shape[0]
    
        # Placeholder logic
        target_revision = total_active
    
        # ================= KPI LAYOUT =================
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Alerts", total_generated)
        col2.metric("Total Active", total_active)
        col3.metric("Total Closed", total_closed)
    
        st.markdown("---")
    
        col1, col2 = st.columns(2)
        col1.metric("Pending", pending)
        col2.metric("Implemented", implemented)
    
        col1, col2 = st.columns(2)
        col1.metric("Work In Progress", wip)
        col2.metric("Rejected", rejected)
    
        col1, col2 = st.columns(2)
        col1.metric("Overdue", overdue)
        col2.metric("Auto Closed", auto_closed)
    
        col1, col2 = st.columns(2)
        col1.metric("No. of Overdue Alerts (>3 days)", overdue_3)
        col2.metric("Target Date Revision (Active Alerts)", target_revision)
    
        st.markdown("---")
    
        # ================= ACTIVE ALERTS BY ROLE =================
        st.markdown("### Active Alerts by Role")
    
        df_active_month = df_month[~status_lower.str.contains("closed", na=False)]
    
        role_mapping = {
            'James Anderson': 'Process Engineer',
            'Ahmed El-Sayed': 'Process Manager',
            'Chen Wei': 'Operation Engineer',
            'Lucas Silva': 'Operation Manager',
            'Arjun Mehta': 'Operation Engineer'
        }
    
        df_active_month["Role"] = df_active_month["currentAssignee"].map(role_mapping)
        df_active_month["Role"] = df_active_month["Role"].fillna("Other")
    
        role_df = (
            df_active_month
            .groupby("Role")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )
    
        if not role_df.empty:
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
        else:
            st.info("No active alerts in selected month.")

    # ================= Alert Management =================
    with tab3:
    
        st.subheader("Alert Management")
    
        if df_filtered.empty:
            st.warning("No data available for selected filters.")
            st.stop()
    
        # ================= FILTER ROW =================
        col1, col2 = st.columns(2)
    
        # -------- Category Filter --------
        category_options = ["All", "Energy", "Production", "Environment"]
        selected_category = col1.selectbox("Category", category_options)
    
        # -------- Deviation Filter --------
        deviation_options = ["All", "Pending"]
        selected_deviation = col2.selectbox("Deviation", deviation_options)
    
        df_mgmt = df_filtered.copy()
    
        # ================= CATEGORY LOGIC =================
        if selected_category == "Energy":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains("energy", case=False, na=False)
            ]
    
        elif selected_category == "Production":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains(
                    "production|throughput|rate|capacity|output",
                    case=False,
                    na=False
                )
            ]
    
        elif selected_category == "Environment":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains(
                    "environment|emission|flare|co2|pollution",
                    case=False,
                    na=False
                )
            ]
    
        # ================= DEVIATION LOGIC =================
        if selected_deviation == "Pending":
            df_mgmt = df_mgmt[
                df_mgmt["status"].str.contains("pending", case=False, na=False)
            ]
    
        if df_mgmt.empty:
            st.info("No records found.")
            st.stop()
    
        # ================= TABLE STRUCTURE =================
        display_df = pd.DataFrame({
            "Alert ID": df_mgmt["requestID"],
            "Category": df_mgmt["odsCauseTagName"],
            "Cause (System)": df_mgmt["causeMessage"].fillna("") + " | " + df_mgmt["systemName"].fillna(""),
            "KPI": df_mgmt["odsCauseTagName"],
            "Deviation": df_mgmt["status"],
            "Due Date": "",  # Blank as requested
            "Comments": df_mgmt["comments"].fillna("")
        })
    
        # Reset index for clean display
        display_df = display_df.reset_index(drop=True)
    
        # ================= DISPLAY TABLE =================
        st.dataframe(display_df, use_container_width=True)
