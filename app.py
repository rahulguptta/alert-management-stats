import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Alert Dashboard")

# ==========================================================
# FILE UPLOAD
# ==========================================================
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df["deviationTime"] = pd.to_datetime(df["deviationTime"])

    # ==========================================================
    # SIDEBAR FILTERS (Used by Overview Only)
    # ==========================================================
    st.sidebar.header("Filters")

    min_date = df["deviationTime"].min()
    max_date = df["deviationTime"].max()

    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date]
    )

    system_list = ["All"] + sorted(df["systemName"].dropna().unique())
    selected_system_sidebar = st.sidebar.selectbox(
        "Select Affiliate",
        system_list
    )

    # Apply sidebar filters
    df_filtered = df[
        (df["deviationTime"] >= pd.to_datetime(start_date)) &
        (df["deviationTime"] <= pd.to_datetime(end_date))
    ]

    if selected_system_sidebar != "All":
        df_filtered = df_filtered[
            df_filtered["systemName"] == selected_system_sidebar
        ]

    # ==========================================================
    # TABS
    # ==========================================================
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Management", "Alert Statistics"]
    )

    # ==========================================================
    # TAB 1 - OVERVIEW (ONLY ACTIVE ALERTS)
    # ==========================================================
    with tab1:

        st.markdown("## Active Alerts Overview")

        # Only Active Status
        active_status = ["Pending", "Work In Progress", "Overdue"]

        df_active = df_filtered[
            df_filtered["status"].isin(active_status)
        ]

        fig1, ax1 = plt.subplots(figsize=(8, 3))

        if selected_system_sidebar == "All":
            # Stacked Active Alerts
            stacked = df_active.groupby(
                ["systemName", "status"]
            ).size().unstack(fill_value=0)

            bottom = None

            for status in stacked.columns:
                bars = ax1.bar(
                    stacked.index,
                    stacked[status],
                    bottom=bottom,
                    label=status
                )

                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax1.text(
                            bar.get_x() + bar.get_width()/2,
                            bar.get_y() + height - 0.1,
                            int(height),
                            ha="center",
                            va="top",
                            fontsize=8
                        )

                if bottom is None:
                    bottom = stacked[status].values
                else:
                    bottom = bottom + stacked[status].values

            ax1.legend(ncol=len(stacked.columns))

        else:
            # Normal Bar for selected affiliate
            counts = df_active["status"].value_counts()
            bars = ax1.bar(counts.index, counts.values)

            for bar in bars:
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width()/2,
                    height - 0.1,
                    int(height),
                    ha="center",
                    va="top",
                    fontsize=8
                )

        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_visible(False)

        st.pyplot(fig1)

        # Table only filtered affiliate data
        st.dataframe(df_filtered, use_container_width=True)

    # ==========================================================
    # TAB 2 - ALERT MANAGEMENT (PLACEHOLDER)
    # ==========================================================
    with tab2:
        st.info("Alert Management section will be implemented later.")

    # ==========================================================
    # TAB 3 - ALERT STATISTICS (MONTH ONLY)
    # ==========================================================
    with tab3:

        df["month_year"] = df["deviationTime"].dt.strftime("%B %Y")
        months = sorted(df["month_year"].unique())

        selected_month = st.selectbox("Select Month", months)

        df_month = df[df["month_year"] == selected_month].copy()

        df_month["status_viz"] = df_month["status"].replace({
            "Closed (System)": "Auto Closed",
            "Closed (Implemented)": "Implemented",
            "Closed (Rejected)": "Rejected"
        })

        # KPI Calculations
        total_generated = len(df_month)
        pending = (df_month["status_viz"] == "Pending").sum()
        wip = (df_month["status_viz"] == "Work In Progress").sum()
        overdue = (df_month["status_viz"] == "Overdue").sum()
        implemented = (df_month["status_viz"] == "Implemented").sum()
        rejected = (df_month["status_viz"] == "Rejected").sum()
        auto_closed = (df_month["status_viz"] == "Auto Closed").sum()

        total_active = pending + wip + overdue
        total_closed = implemented + rejected + auto_closed

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Alerts", total_generated)
        col2.metric("Total Active", total_active)
        col3.metric("Total Closed", total_closed)

        col4, col5, col6 = st.columns(3)
        col4.metric("Pending", pending)
        col5.metric("Work In Progress", wip)
        col6.metric("Overdue", overdue)

        col7, col8, col9 = st.columns(3)
        col7.metric("Implemented", implemented)
        col8.metric("Rejected", rejected)
        col9.metric("Auto Closed", auto_closed)

        st.metric("Target Date Revision", "—")

        # Active Alerts by Role
        st.markdown("### Active Alerts by Role")

        df_active_month = df_month[
            df_month["status_viz"].isin(
                ["Pending", "Work In Progress", "Overdue"]
            )
        ]

        role_counts = df_active_month["currentAssignee"].value_counts()

        fig2, ax2 = plt.subplots(figsize=(6, 2.5))
        bars = ax2.bar(role_counts.index, role_counts.values)

        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width()/2,
                height - 0.1,
                int(height),
                ha="center",
                va="top",
                fontsize=8
            )

        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)

        plt.xticks(rotation=45)
        st.pyplot(fig2)

        # Utilization Rate
        if total_generated > 0:
            utilization_rate = round(
                (total_closed / total_generated) * 100, 2
            )
        else:
            utilization_rate = 0

        st.metric("Alert Utilization Rate (%)", f"{utilization_rate}%")
