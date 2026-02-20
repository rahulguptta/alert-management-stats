import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Status Statistics Dashboard", layout="wide")
st.title("Status Statistics Dashboard")

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

        # Sidebar Filters
        st.sidebar.header("Filters")

        min_date = df["deviationtime"].min()
        max_date = df["deviationtime"].max()

        date_range = st.sidebar.date_input(
            "Select Time Period",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        systems = ["All"] + sorted(df["systemname"].dropna().unique().tolist())
        selected_system = st.sidebar.selectbox("Select System", systems)

        # Apply date filter
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df = df[(df["deviationtime"] >= start_date) & (df["deviationtime"] <= end_date)]

        # ---- Visualization mapping (NO change to df) ----
        def map_status(series):
            return series.replace({
                "Closed (System)": "Closed",
                "Closed (Implemented)": "Implemented",
                "Closed(Implemented)": "Implemented",
                "Closed (Rejected)": "Rejected",
                "Closed(Rejected)": "Rejected"
            })

        overall_stats = map_status(df["status"]).value_counts()

        def plot_chart(stats, title):
            fig, ax = plt.subplots(figsize=(4, 1.5))
            bars = ax.bar(stats.index, stats.values, color="yellow")

            ymax = max(stats.values) if len(stats.values) > 0 else 1
            ax.set_ylim(0, ymax * 1.15)

            for bar in bars:
                height = bar.get_height()
                y_position = min(height + ymax * 0.03, ymax * 1.10)
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    y_position,
                    f"{int(height)}",
                    ha="center",
                    va="bottom",
                    fontsize=8
                )

            ax.set_xlabel("Status")
            ax.set_ylabel("Count")
            ax.set_title(title)
            plt.xticks(rotation=45)
            st.pyplot(fig)

        # Only Overall at start
        if selected_system == "All":
            plot_chart(overall_stats, "Overall")

        # Show side-by-side once system selected
        else:
            filtered_df = df[df["systemname"] == selected_system]
            system_stats = map_status(filtered_df["status"]).value_counts()

            col1, col2 = st.columns(2)

            with col1:
                plot_chart(overall_stats, "Overall")

            with col2:
                plot_chart(system_stats, selected_system)
