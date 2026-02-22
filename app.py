import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    required_cols = ["deviationTime", "systemName", "status", "currentAssignee"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    df["deviationTime"] = pd.to_datetime(df["deviationTime"])

    # Remove all Closed variants for charts
    df_active = df[~df["status"].str.lower().str.contains("closed", na=False)]

    # ================= Sidebar =================
    st.sidebar.header("Filters")

    min_date = df["deviationTime"].min()
    max_date = df["deviationTime"].max()

    period = st.sidebar.date_input(
        "Select Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(period, tuple):
        start_date, end_date = period
    else:
        start_date = min_date
        end_date = max_date

    affiliates = sorted(df["systemName"].dropna().unique())
    affiliate_selected = st.sidebar.selectbox(
        "Select Affiliate",
        ["All"] + list(affiliates),
        index=0
    )

    # Apply filters
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

    # ================= Tabs =================
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management"]
    )

    # ================= Overview =================
    with tab1:

        st.subheader("Active Alerts Overview")

        if affiliate_selected == "All":

            all_affiliates = sorted(df_filtered["systemName"].unique())
            active_statuses = sorted(df_active_filtered["status"].unique())

            chart_df = (
                df_active_filtered
                .groupby(["systemName", "status"])
                .size()
                .reset_index(name="Count")
            )

            if len(active_statuses) > 0:
                complete_index = pd.MultiIndex.from_product(
                    [all_affiliates, active_statuses],
                    names=["systemName", "status"]
                )

                chart_df = (
                    chart_df
                    .set_index(["systemName", "status"])
                    .reindex(complete_index, fill_value=0)
                    .reset_index()
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

        else:
            chart_df = (
                df_active_filtered
                .groupby("status")
                .size()
                .reset_index(name="Count")
            )

            fig = px.bar(
                chart_df,
                x="status",
                y="Count",
                text="Count"
            )

            fig.update_layout(xaxis_title="", yaxis_title="Active Alerts")
            st.plotly_chart(fig, use_container_width=True)

        # ================= Overall Status =================
        st.markdown("### Overall Status Statistics")

        overall_stats = (
            df_filtered["status"]
            .value_counts()
            .reset_index()
        )
        overall_stats.columns = ["Status", "Count"]

        st.dataframe(overall_stats, use_container_width=True)

        # ================= Show table ONLY if All selected =================
        if affiliate_selected == "All":

            st.markdown("### Status by Affiliate")

            affiliate_stats = (
                df_filtered
                .groupby(["systemName", "status"])
                .size()
                .reset_index(name="Count")
            )

            pivot_table = affiliate_stats.pivot(
                index="systemName",
                columns="status",
                values="Count"
            ).fillna(0)

            st.dataframe(pivot_table, use_container_width=True)

    # ================= Alert Statistics =================
    with tab2:

        st.subheader("Alert Statistics")
    
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
        st.info("Alert Management module coming soon.")
