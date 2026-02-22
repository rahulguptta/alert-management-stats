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

    # Apply sidebar filters
    df_filtered = df[
        (df["deviationTime"] >= pd.to_datetime(start_date)) &
        (df["deviationTime"] <= pd.to_datetime(end_date))
    ]

    if affiliate_selected != "All":
        df_filtered = df_filtered[df_filtered["systemName"] == affiliate_selected]

    df_active_filtered = df_filtered[
        ~df_filtered["status"].str.lower().str.contains("closed", na=False)
    ]

    # ================= Tabs =================
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management"]
    )

    # =========================================================
    # ===================== OVERVIEW (UNCHANGED) ===============
    # =========================================================
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

        st.markdown("### Overall Status Statistics")

        overall_stats = (
            df_filtered["status"]
            .value_counts()
            .reset_index()
        )
        overall_stats.columns = ["Status", "Count"]

        st.dataframe(overall_stats, use_container_width=True)

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

    # =========================================================
    # ================= ALERT STATISTICS ======================
    # =========================================================
    with tab2:

        st.subheader("Monthly Utilization Report")

        df_filtered["Month"] = df_filtered["deviationTime"].dt.to_period("M")
        months_available = sorted(df_filtered["Month"].astype(str).unique())

        if len(months_available) == 0:
            st.warning("No data available for selected period.")
        else:
            selected_month = st.selectbox(
                "Select Month",
                months_available,
                index=len(months_available) - 1
            )

            df_month = df_filtered[
                df_filtered["Month"].astype(str) == selected_month
            ]

            # ================= KPIs =================
            total_generated = len(df_month)

            pending = df_month["status"].str.contains("pending", case=False, na=False).sum()
            auto_closed = df_month["status"].str.contains("system", case=False, na=False).sum()
            implemented = df_month["status"].str.contains("implemented", case=False, na=False).sum()
            rejected = df_month["status"].str.contains("rejected", case=False, na=False).sum()
            wip = df_month["status"].str.contains("work", case=False, na=False).sum()
            overdue = df_month["status"].str.contains("overdue", case=False, na=False).sum()

            col1, col2, col3 = st.columns(3)
            col1.metric("Generated Alerts", total_generated)
            col2.metric("Pending", pending)
            col3.metric("Auto Closed", auto_closed)

            st.markdown("### Closed by Team")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Implemented", implemented)
            c2.metric("Rejected", rejected)
            c3.metric("Work In Progress", wip)
            c4.metric("Overdue", overdue)

            # ================= Active Alerts by Role =================
            st.markdown("### Active Alerts by Role")

            df_month_active = df_month[
                ~df_month["status"].str.lower().str.contains("closed", na=False)
            ].copy()

            df_month_active["currentAssignee"] = (
                df_month_active["currentAssignee"]
                .fillna("Unassigned")
                .astype(str)
            )

            role_df = (
                df_month_active
                .groupby("currentAssignee")
                .size()
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
            )

            fig_role = px.bar(
                role_df,
                x="currentAssignee",
                y="Count",
                text="Count"
            )

            fig_role.update_layout(
                xaxis_title="Role",
                yaxis_title="Active Alerts",
                xaxis=dict(type="category")
            )

            st.plotly_chart(fig_role, use_container_width=True)

    # =========================================================
    # ================= ALERT MANAGEMENT ======================
    # =========================================================
    with tab3:
        st.subheader("Alert Management")
        st.info("Placeholder")
