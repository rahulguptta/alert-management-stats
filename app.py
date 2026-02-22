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

        # Apply system filter (for chart only)
        if selected_system != "All":
            df_chart = df[df["systemname"] == selected_system]
            systems = [selected_system]
        else:
            df_chart = df.copy()
            systems = sorted(df_chart["systemname"].dropna().unique())

        # ---- Visualization Mapping (NO change to original df logic) ----
        def map_status(s):
            return s.replace({
                "Closed (System)": "Closed",
                "Closed (Implemented)": "Implemented",
                "Closed(Implemented)": "Implemented",
                "Closed (Rejected)": "Rejected",
                "Closed(Rejected)": "Rejected"
            })

        df_chart["status_viz"] = map_status(df_chart["status"])

        inprogress_counts = []
        overdue_counts = []
        pending_counts = []
        summary_data = []

        for system in systems:
            temp = df_chart[df_chart["systemname"] == system]

            inprog = (temp["status_viz"] == "In-Progress").sum()
            overdue = (temp["status_viz"] == "Overdue").sum()
            pending = (temp["status_viz"] == "Pending").sum()

            inprogress_counts.append(inprog)
            overdue_counts.append(overdue)
            pending_counts.append(pending)

            closed_count = (temp["status_viz"].isin(["Closed", "Implemented"])).sum()
            open_count = len(temp) - closed_count
            overdue_3 = overdue

            summary_data.append({
                "System": system,
                "Closed Alerts (Implemented)": closed_count,
                "Open Alerts": open_count,
                "Overdue > 3 Days": overdue_3
            })

        # -------- Stacked Bar Chart --------
        fig, ax = plt.subplots(figsize=(10, 3))

        x = np.arange(len(systems))

        ax.bar(x, inprogress_counts)
        ax.bar(x, overdue_counts, bottom=inprogress_counts)
        ax.bar(x, pending_counts,
               bottom=np.array(inprogress_counts) + np.array(overdue_counts))

        totals = np.array(inprogress_counts) + np.array(overdue_counts) + np.array(pending_counts)
        ymax = max(totals) if len(totals) > 0 else 1
        ax.set_ylim(0, ymax * 1.1)

        # Numbers below top border
        for i, total in enumerate(totals):
            ax.text(
                x[i],
                ymax * 1.05,
                str(int(total)),
                ha='center',
                va='top',
                fontsize=8
            )

        ax.set_xticks(x)
        ax.set_xticklabels(systems, rotation=45)
        ax.set_ylabel("Active Alerts")

        # Remove border lines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Horizontal legend
        ax.legend(
            ["In-Progress", "Overdue", "Pending"],
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=3,
            frameon=False
        )

        st.pyplot(fig)

        # -------- Summary Table --------
        summary_df = pd.DataFrame(summary_data)
        st.markdown("### Summary")
        st.dataframe(summary_df.set_index("System"))
