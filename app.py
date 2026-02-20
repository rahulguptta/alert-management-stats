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

        # Merge Closed (System) + Closed (Implemented) → Closed
        df["status"] = df["status"].astype(str).str.strip()
        df["status"] = df["status"].replace({
            "Closed (System)": "Closed",
            "Closed (Implemented)": "Closed"
        })

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

        overall_stats = df["status"].value_counts()

        # Only Overall at start
        if selected_system == "All":
            fig, ax = plt.subplots(figsize=(4, 1.5))
            bars = ax.bar(overall_stats.index, overall_stats.values, color="yellow")

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=8)

            ax.set_xlabel("Status")
            ax.set_ylabel("Count")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        # Show side-by-side once system selected
        else:
            filtered_df = df[df["systemname"] == selected_system]
            system_stats = filtered_df["status"].value_counts()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Overall**")
                fig1, ax1 = plt.subplots(figsize=(4, 1.5))
                bars1 = ax1.bar(overall_stats.index, overall_stats.values, color="yellow")

                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2, height,
                             f'{int(height)}',
                             ha='center', va='bottom', fontsize=8)

                ax1.set_xlabel("Status")
                ax1.set_ylabel("Count")
                plt.xticks(rotation=45)
                st.pyplot(fig1)

            with col2:
                st.markdown(f"**{selected_system}**")
                fig2, ax2 = plt.subplots(figsize=(4, 1.5))
                bars2 = ax2.bar(system_stats.index, system_stats.values, color="yellow")

                for bar in bars2:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2, height,
                             f'{int(height)}',
                             ha='center', va='bottom', fontsize=8)

                ax2.set_xlabel("Status")
                ax2.set_ylabel("Count")
                plt.xticks(rotation=45)
                st.pyplot(fig2)
