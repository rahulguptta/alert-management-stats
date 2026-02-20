import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Status Statistics Dashboard", layout="wide")

st.title("Status Statistics Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip().str.lower()

    # Required columns check
    required_cols = ["status", "affiliate", "date"]
    if not all(col in df.columns for col in required_cols):
        st.error("Excel must contain columns: status, affiliate, date")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Sidebar Filters
        st.sidebar.header("Filters")

        min_date = df["date"].min()
        max_date = df["date"].max()

        date_range = st.sidebar.date_input(
            "Select Time Period",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        affiliates = ["All"] + sorted(df["affiliate"].dropna().unique().tolist())
        selected_affiliate = st.sidebar.selectbox("Select Affiliate", affiliates)

        # Apply Filters
        if len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        if selected_affiliate != "All":
            df = df[df["affiliate"] == selected_affiliate]

        st.subheader("Overall Status Statistics")

        overall_stats = df["status"].value_counts().reset_index()
        overall_stats.columns = ["Status", "Count"]
        overall_stats["Percentage"] = (overall_stats["Count"] / overall_stats["Count"].sum()) * 100

        st.dataframe(overall_stats)

        st.markdown("---")
        st.subheader("Affiliate-wise Status Statistics")

        affiliate_list = sorted(df["affiliate"].dropna().unique())

        for aff in affiliate_list:
            st.markdown(f"### {aff}")
            aff_df = df[df["affiliate"] == aff]

            aff_stats = aff_df["status"].value_counts().reset_index()
            aff_stats.columns = ["Status", "Count"]
            aff_stats["Percentage"] = (aff_stats["Count"] / aff_stats["Count"].sum()) * 100

            st.dataframe(aff_stats)