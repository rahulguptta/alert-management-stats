import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Monthly Utilization Report", layout="wide")
st.title("Monthly Utilization Report")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()

    required_cols = ["status", "systemname", "deviationtime"]
    if not all(col in df.columns for col in required_cols):
        st.error("Excel must contain columns: status, systemName, deviationTime")
    else:
        df["deviationtime"] = pd.to_datetime(df["deviationtime"], errors="coerce")
        df = df.dropna(subset=["deviationtime"])

        # ---- Filters ----
        st.sidebar.header("Filters")

        min_date = df["deviationtime"].min()
        max_date = df["deviationtime"].max()

        date_range = st.sidebar.date_input(
            "Select Time Period",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        systems_available = sorted(df["systemname"].dropna().unique())
        selected_system = st.sidebar.selectbox(
            "Select System",
            ["All"] + systems_available
        )

        # Apply date filter
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df = df[(df["deviationtime"] >= start_date) & (df["deviationtime"] <= end_date)]

        # ---- Visualization Mapping (no permanent df change intent) ----
        def map_status(s):
            return s.replace({
                "Closed (System)": "Closed",
                "Closed (Implemented)": "Implemented",
                "Closed(Implemented)": "Implemented",
                "Closed (Rejected)": "Rejected",
                "Closed(Rejected)": "Rejected"
            })

        df_chart = df.copy()
        df_chart["status_viz"] = map_status(df_chart["status"])

        # Layout
        col1, col2 = st.columns([2, 1])

        with col1:

            if selected_system == "All":
                systems = sorted(df_chart["systemname"].dropna().unique())

                inprogress_counts = []
                overdue_counts = []
                pending_counts = []

                for system in systems:
                    temp = df_chart[df_chart["systemname"] == system]

                    inprogress_counts.append((temp["status_viz"] == "In-Progress").sum())
                    overdue_counts.append((temp["status_viz"] == "Overdue").sum())
                    pending_counts.append((temp["status_viz"] == "Pending").sum())

                fig, ax = plt.subplots(figsize=(8, 3))

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

            else:
                temp = df_chart[df_chart["systemname"] == selected_system]

                status_counts = [
                    (temp["status_viz"] == "In-Progress").sum(),
                    (temp["status_viz"] == "Overdue").sum(),
                    (temp["status_viz"] == "Pending").sum(),
                ]

                labels = ["In-Progress", "Overdue", "Pending"]

                fig, ax = plt.subplots(figsize=(6, 3))

                bars = ax.bar(labels, status_counts)

                ymax = max(status_counts) if len(status_counts) > 0 else 1
                ax.set_ylim(0, ymax * 1.1)

                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        ymax * 1.05,
                        str(int(height)),
                        ha="center",
                        va="top",
                        fontsize=8,
                    )

                ax.set_ylabel("Active Alerts")

                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)

                st.pyplot(fig)

        with col2:
            summary_data = []

            systems_for_summary = (
                [selected_system]
                if selected_system != "All"
                else sorted(df_chart["systemname"].dropna().unique())
            )

            for system in systems_for_summary:
                temp = df_chart[df_chart["systemname"] == system]

                closed_count = temp["status_viz"].isin(
                    ["Closed", "Implemented"]
                ).sum()
                open_count = len(temp) - closed_count
                overdue_3 = (temp["status_viz"] == "Overdue").sum()

                summary_data.append({
                    "System": system,
                    "Closed Alerts (Implemented)": closed_count,
                    "Open Alerts": open_count,
                    "Overdue > 3 Days": overdue_3
                })

            summary_df = pd.DataFrame(summary_data)
            st.markdown("### Summary")
            st.dataframe(summary_df.set_index("System"), use_container_width=True)
