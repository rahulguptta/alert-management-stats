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

        # Apply Filters
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df = df[(df["deviationtime"] >= start_date) & (df["deviationtime"] <= end_date)]

        if selected_system != "All":
            df = df[df["systemname"] == selected_system]

        # ===== Overall Plot =====
        st.subheader("Overall Status Distribution")

        overall_stats = df["status"].value_counts()

        fig1, ax1 = plt.subplots(figsize=(4, 3))
        ax1.bar(overall_stats.index, overall_stats.values, color="yellow")
        ax1.set_xlabel("Status")
        ax1.set_ylabel("Count")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

        st.markdown("---")

        # ===== System-wise Plots =====
        st.subheader("System-wise Status Distribution")

        system_list = sorted(df["systemname"].dropna().unique())

        for system in system_list:
            st.markdown(f"### {system}")
            sys_df = df[df["systemname"] == system]
            sys_stats = sys_df["status"].value_counts()

            fig2, ax2 = plt.subplots(figsize=(4, 3))
            ax2.bar(sys_stats.index, sys_stats.values, color="yellow")
            ax2.set_xlabel("Status")
            ax2.set_ylabel("Count")
            plt.xticks(rotation=45)
            st.pyplot(fig2)
