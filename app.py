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
    # ===================== FIRST PAGE =========================
    # ==========================================================

    st.markdown("## Alert Overview")

    # Status mapping ONLY for visualization (df unchanged)
    df["status_viz"] = df["status"].replace({
        "Closed (System)": "Closed",
        "Closed (Implemented)": "Implemented",
        "Closed (Rejected)": "Rejected"
    })

    system_list = ["All"] + sorted(df["systemName"].dropna().unique())
    selected_system = st.selectbox("Select System", system_list)

    if selected_system != "All":
        df_view = df[df["systemName"] == selected_system]
    else:
        df_view = df.copy()

    status_counts = df_view["status_viz"].value_counts()

    fig1, ax1 = plt.subplots(figsize=(8, 3))

    if selected_system == "All":
        # STACKED BAR
        stacked = df_view.groupby(["systemName", "status_viz"]).size().unstack(fill_value=0)
        bottom = None

        for status in stacked.columns:
            bars = ax1.bar(stacked.index, stacked[status], bottom=bottom, label=status)

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
        # NORMAL BAR
        bars = ax1.bar(status_counts.index, status_counts.values)

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

    st.dataframe(df_view.head(20), use_container_width=True)

    # ==========================================================
    # ===================== TABS SECTION =======================
    # ==========================================================

    st.markdown("---")
    st.header("Advanced Alert Section")

    tab1, tab2 = st.tabs(["Alert Management", "Alert Statistics"])

    # ==========================================================
    # TAB 1 - PLACEHOLDER
    # ==========================================================
    with tab1:
        st.info("Alert Management section will be implemented later.")

    # ==========================================================
    # TAB 2 - ALERT STATISTICS (MONTH ONLY)
    # ==========================================================
    with tab2:

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

        # =====================================================
        # ACTIVE ALERTS BY ROLE
        # =====================================================
        st.markdown("### Active Alerts by Role")

        df_active = df_month[df_month["status_viz"].isin(
            ["Pending", "Work In Progress", "Overdue"]
        )]

        role_counts = df_active["currentAssignee"].value_counts()

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

        # =====================================================
        # MONTHLY UTILIZATION REPORT
        # =====================================================
        st.markdown("### Monthly Utilization Report")

        system_group = df_month.groupby(["systemName", "status_viz"]).size().unstack(fill_value=0)

        fig3, ax3 = plt.subplots(figsize=(7, 3))

        bottom = None

        for status in system_group.columns:
            bars = ax3.bar(
                system_group.index,
                system_group[status],
                bottom=bottom,
                label=status
            )

            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax3.text(
                        bar.get_x() + bar.get_width()/2,
                        bar.get_y() + height - 0.1,
                        int(height),
                        ha="center",
                        va="top",
                        fontsize=8
                    )

            if bottom is None:
                bottom = system_group[status].values
            else:
                bottom = bottom + system_group[status].values

        ax3.legend(ncol=len(system_group.columns))
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.spines['left'].set_visible(False)

        plt.xticks(rotation=45)
        st.pyplot(fig3)

        # =====================================================
        # UTILIZATION RATE
        # =====================================================
        if total_generated > 0:
            utilization_rate = round((total_closed / total_generated) * 100, 2)
        else:
            utilization_rate = 0

        st.metric("Alert Utilization Rate (%)", f"{utilization_rate}%")
