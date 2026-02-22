import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    required_cols = ["deviationTime", "systemName", "status"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    df["deviationTime"] = pd.to_datetime(df["deviationTime"])

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
        start_date = min_date
        end_date = max_date

    affiliates = sorted(df["systemName"].dropna().unique().tolist())
    affiliate_selected = st.sidebar.selectbox(
        "Select Affiliate",
        ["All"] + affiliates,
        index=0
    )

    df_filtered = df[
        (df["deviationTime"] >= pd.to_datetime(start_date)) &
        (df["deviationTime"] <= pd.to_datetime(end_date))
    ]

    if affiliate_selected != "All":
        df_filtered = df_filtered[df_filtered["systemName"] == affiliate_selected]

    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management"]
    )

    with tab1:
        st.subheader("Status Overview")

        if affiliate_selected == "All":
            chart_df = (
                df_filtered
                .groupby(["systemName", "status"])
                .size()
                .reset_index(name="Count")
            )

            fig = px.bar(
                chart_df,
                x="systemName",
                y="Count",
                color="status",
                barmode="stack",
                text="Count"
            )
            fig.update_layout(xaxis_title="", yaxis_title="Alerts")
            st.plotly_chart(fig, use_container_width=True)

        else:
            chart_df = (
                df_filtered
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
            fig.update_layout(xaxis_title="", yaxis_title="Alerts")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Overall Status Statistics")
        overall_stats = (
            df_filtered["status"]
            .value_counts()
            .reset_index()
        )
        overall_stats.columns = ["Status", "Count"]
        st.dataframe(overall_stats, use_container_width=True)

        st.markdown("### Status by Affiliate")

        affiliate_stats = (
            df_filtered
            .groupby(["systemName", "status"])
            .size()
            .reset_index(name="Count")
            .sort_values("systemName")
        )

        st.dataframe(affiliate_stats, use_container_width=True)

    with tab2:
        st.subheader("Alert Statistics")
        st.info("Placeholder for Alert Statistics")

    with tab3:
        st.subheader("Alert Management")
        st.info("Placeholder for Alert Management")
