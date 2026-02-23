import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:

    # ================= INITIAL DATA MANIPULATION =================
    df = pd.read_excel(uploaded_file, header=None)

    # Remove first row and use second row as header
    df.columns = df.iloc[1]
    df = df[2:].reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()

    # Convert datetime
    df["deviationTime"] = pd.to_datetime(df["deviationTime"], errors="coerce")

    # -------- systemName Mapping --------
    system_mapping = {
        "COLD SECTIONS COLUMNS": "Column Section",
        "QUENCH SYSTEM": "Quench Tower",
        "CHARGE GAS COMPRESSOR": "CGC Section",
        "ACETYLENE REACTORS OPTIMIZATION": "Acetylene Reactors",
    }
    df["systemName"] = df["systemName"].replace(system_mapping)

    # -------- Assignee Mapping --------
    assignee_mapping = {
        "PAVLOV ANDRES ROMERO PEREZ": "Parvaze Aalam",
        "Ahmed Hassan Ahmed Faqqas": "Ashawani Arora",
        "Omer Ali Abdullah AlAli": "John Doe Paul",
        "Talaal Salah Abdullah Alabdulkareem": "Rashmina Raj Kumari",
    }
    df["currentAssignee"] = df["currentAssignee"].replace(assignee_mapping)
    df["lastActionTakenBy"] = df["lastActionTakenBy"].replace(assignee_mapping)

    # -------- Role Creation from stageID --------
    role_mapping = {
        1: "Process Engineer",
        2: "Process Manager",
        3: "Operation Engineer",
        4: "Operation Engineer",
    }
    df["stageID"] = pd.to_numeric(df["stageID"], errors="coerce")
    df["Role"] = df["stageID"].map(role_mapping)

    # Remove closed alerts for charts
    df_active = df[~df["status"].str.lower().str.contains("closed", na=False)]

    # ================= Sidebar Filters =================
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
        start_date, end_date = min_date, max_date

    affiliates = sorted(df["systemName"].dropna().unique())
    affiliate_selected = st.sidebar.selectbox(
        "Select Affiliate",
        ["All"] + affiliates,
        index=0,
    )

    # Apply period filter
    df_filtered = df[
        (df["deviationTime"] >= pd.to_datetime(start_date)) &
        (df["deviationTime"] <= pd.to_datetime(end_date))
    ]

    df_active_filtered = df_active[
        (df_active["deviationTime"] >= pd.to_datetime(start_date)) &
        (df_active["deviationTime"] <= pd.to_datetime(end_date))
    ]

    # Apply affiliate filter
    if affiliate_selected != "All":
        df_filtered = df_filtered[df_filtered["systemName"] == affiliate_selected]
        df_active_filtered = df_active_filtered[
            df_active_filtered["systemName"] == affiliate_selected
        ]

    # ================= Tabs =================
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management"]
    )

    # ================= OVERVIEW =================
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
                    chart_df.set_index(["systemName", "status"])
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
        overall_stats = df_filtered["status"].value_counts().reset_index()
        overall_stats.columns = ["Status", "Count"]
        st.dataframe(overall_stats, use_container_width=True)

        if affiliate_selected == "All":
            st.markdown("### Status by Affiliate")
            affiliate_stats = (
                df_filtered.groupby(["systemName", "status"])
                .size()
                .reset_index(name="Count")
            )
            pivot_table = affiliate_stats.pivot(
                index="systemName",
                columns="status",
                values="Count"
            ).fillna(0)
            st.dataframe(pivot_table, use_container_width=True)

    # ================= ALERT STATISTICS =================
    with tab2:

        st.subheader("Alert Statistics")

        if df_filtered.empty:
            st.warning("No data available for selected filters.")
            st.stop()

        total_generated = len(df_filtered)
        total_closed = df_filtered[
            df_filtered["status"].str.lower().str.contains("closed", na=False)
        ].shape[0]
        total_active = total_generated - total_closed

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Alerts", total_generated)
        col2.metric("Total Active", total_active)
        col3.metric("Total Closed", total_closed)

        st.markdown("---")
        st.markdown("### Active Alerts by Role")

        df_active_month = df_filtered[
            ~df_filtered["status"].str.lower().str.contains("closed", na=False)
        ]

        role_df = (
            df_active_month.groupby("Role")
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
            fig_role.update_layout(xaxis=dict(type="category"))
            st.plotly_chart(fig_role, use_container_width=True)
        else:
            st.info("No active alerts available.")

    # ================= ALERT MANAGEMENT =================
    with tab3:

        st.subheader("Alert Management")

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox(
                "Category",
                ["All", "Energy", "Production", "Environment"]
            )

        with col2:
            deviation = st.selectbox(
                "Deviation",
                ["All", "Pending"]
            )

        df_mgmt = df_filtered.copy()

        if category == "Energy":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains("energy", case=False, na=False)
            ]

        elif category == "Production":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains(
                    "production|pressure|flow|temperature|stage",
                    case=False,
                    na=False
                )
            ]

        elif category == "Environment":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains(
                    "environment|emission|co2|pollution",
                    case=False,
                    na=False
                )
            ]

        if deviation == "Pending":
            df_mgmt = df_mgmt[
                df_mgmt["status"].str.contains("pending", case=False, na=False)
            ]

        if df_mgmt.empty:
            st.info("No records found.")
        else:
            header_cols = st.columns([3, 2, 2, 1.5, 1.5, 1])
            header_cols[0].markdown("**Cause (System)**")
            header_cols[1].markdown("**KPI (Alert ID)**")
            header_cols[2].markdown("**Assignee**")
            header_cols[3].markdown("**Due Date**")
            header_cols[4].markdown("**Status**")
            header_cols[5].markdown("**Comments**")

            st.markdown("---")

            for _, row in df_mgmt.iterrows():

                cols = st.columns([3, 2, 2, 1.5, 1.5, 1])

                cols[0].markdown(
                    f"{row['causeMessage']}  \n({row['systemName']})"
                )

                cols[1].markdown(
                    f"{row['odsCauseTagName']}  \n(Alert ID: {row['requestID']})"
                )

                cols[2].write(row["currentAssignee"])
                cols[3].write("")  # Due Date blank
                cols[4].write(row["status"])

                with cols[5]:
                    with st.expander("View Comments"):
                        st.write(row["comments"])

                st.markdown("---")
