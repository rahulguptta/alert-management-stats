import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Alert Dashboard", layout="wide")
st.title("Alert Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()

    required_cols = ["status", "systemname", "deviationtime", "currentassignee"]
    if not all(col in df.columns for col in required_cols):
        st.error("Excel must contain: status, systemName, deviationTime, currentAssignee")
        st.stop()

    df["deviationtime"] = pd.to_datetime(df["deviationtime"], errors="coerce")
    df = df.dropna(subset=["deviationtime"])

    # -------- Tabs --------
    tab1, tab2 = st.tabs(["Alert Management", "Alert Statistics"])

    # ============================================================
    # TAB 1 - PLACEHOLDER
    # ============================================================
    with tab1:
        st.info("Alert Management section will be implemented later.")

    # ============================================================
    # TAB 2 - ALERT STATISTICS
    # ============================================================
    with tab2:

        # ---------- Month Filter ----------
        df["month_year"] = df["deviationtime"].dt.strftime("%B %Y")
        months = sorted(df["month_year"].unique())
        selected_month = st.selectbox("Select Month", months)

        df_month = df[df["month_year"] == selected_month].copy()

        # ---------- Status Mapping (Visualization Only) ----------
        def map_status(s):
            return s.replace({
                "Closed (System)": "Auto Closed",
                "Closed (Implemented)": "Implemented",
                "Closed(Implemented)": "Implemented",
                "Closed (Rejected)": "Rejected",
                "Closed(Rejected)": "Rejected"
            })

        df_month["status_viz"] = map_status(df_month["status"])

        # ---------- KPI Calculations ----------
        total_generated = len(df_month)

        implemented = (df_month["status_viz"] == "Implemented").sum()
        rejected = (df_month["status_viz"] == "Rejected").sum()
        auto_closed = (df_month["status_viz"] == "Auto Closed").sum()

        pending = (df_month["status_viz"] == "Pending").sum()
        wip = (df_month["status_viz"] == "In-Progress").sum()
        overdue = (df_month["status_viz"] == "Overdue").sum()

        total_closed = implemented + rejected + auto_closed
        total_active = total_generated - total_closed

        overdue_3 = overdue  # placeholder logic

        # ---------- KPI Cards Layout ----------
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Alerts", total_generated)
        col2.metric("Total Active", total_active)
        col3.metric("Total Closed", total_closed)

        st.divider()

        col4, col5, col6 = st.columns(3)
        col4.metric("Pending", pending)
        col5.metric("Work In Progress", wip)
        col6.metric("Overdue", overdue)

        col7, col8, col9 = st.columns(3)
        col7.metric("Implemented", implemented)
        col8.metric("Rejected", rejected)
        col9.metric("Auto Closed", auto_closed)

        col10, col11 = st.columns(2)
        col10.metric("No. of Overdue Alerts (>3 Days)", overdue_3)
        col11.metric("Target Date Revision", "—")

        st.divider()

        # ============================================================
        # ACTIVE ALERTS BY ROLE
        # ============================================================
        st.subheader("Active Alerts by Role")

        active_df = df_month[~df_month["status_viz"].isin(
            ["Implemented", "Rejected", "Auto Closed"]
        )]

        role_counts = (
            active_df.groupby("currentassignee")["status_viz"]
            .count()
            .sort_values(ascending=False)
        )

        fig_role, ax_role = plt.subplots(figsize=(8, 3))

        bars = ax_role.bar(role_counts.index, role_counts.values)

        ymax = max(role_counts.values) if len(role_counts.values) > 0 else 1
        ax_role.set_ylim(0, ymax * 1.1)

        for bar in bars:
            height = bar.get_height()
            ax_role.text(
                bar.get_x() + bar.get_width() / 2,
                ymax * 1.05,
                str(int(height)),
                ha="center",
                va="top",
                fontsize=8,
            )

        ax_role.spines["top"].set_visible(False)
        ax_role.spines["right"].set_visible(False)
        ax_role.set_ylabel("Active Alerts")
        plt.xticks(rotation=45)

        st.pyplot(fig_role)

        st.divider()

        # ============================================================
        # MONTHLY UTILIZATION REPORT (System-wise)
        # ============================================================
        st.subheader("Monthly Utilization Report")

        systems = sorted(df_month["systemname"].dropna().unique())

        inprogress_counts = []
        overdue_counts = []
        pending_counts = []

        for system in systems:
            temp = df_month[df_month["systemname"] == system]

            inprogress_counts.append((temp["status_viz"] == "In-Progress").sum())
            overdue_counts.append((temp["status_viz"] == "Overdue").sum())
            pending_counts.append((temp["status_viz"] == "Pending").sum())

        fig, ax = plt.subplots(figsize=(10, 3))

        x = np.arange(len(systems))

        ax.bar(x, inprogress_counts)
        ax.bar(x, overdue_counts, bottom=inprogress_counts)
        ax.bar(
            x,
            pending_counts,
            bottom=np.array(inprogress_counts) + np.array(overdue_counts),
        )

        totals = (
            np.array(inprogress_counts)
            + np.array(overdue_counts)
            + np.array(pending_counts)
        )

        ymax = max(totals) if len(totals) > 0 else 1
        ax.set_ylim(0, ymax * 1.1)

        for i, total in enumerate(totals):
            ax.text(
                x[i],
                ymax * 1.05,
                str(int(total)),
                ha="center",
                va="top",
                fontsize=8,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(systems, rotation=45)
        ax.set_ylabel("Active Alerts")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.legend(
            ["In-Progress", "Overdue", "Pending"],
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=3,
            frameon=False,
        )

        st.pyplot(fig)

        # Alert Utilization Rate
        utilization_rate = 0
        if total_generated > 0:
            utilization_rate = round((total_closed / total_generated) * 100, 2)

        st.metric("Alert Utilization Rate (%)", utilization_rate)
