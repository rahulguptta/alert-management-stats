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

    # Remove all Closed variants for charts
    df_active = df[~df["status"].str.lower().str.contains("closed", na=False)]

    # ================= Sidebar =================
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

    df_active_filtered = df_active[
        (df_active["deviationTime"] >= pd.to_datetime(start_date)) &
        (df_active["deviationTime"] <= pd.to_datetime(end_date))
    ]

    if affiliate_selected != "All":
        df_filtered = df_filtered[df_filtered["systemName"] == affiliate_selected]
        df_active_filtered = df_active_filtered[
            df_active_filtered["systemName"] == affiliate_selected
        ]

    # ================= Tabs =================
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management"]
    )

    # ================= Overview =================
    with tab1:
        st.subheader("Active Alerts Overview")

        if affiliate_selected == "All":

            all_affiliates = sorted(df_filtered["systemName"].unique())
            active_statuses = sorted(df_active_filtered["status"].unique())

            chart_df = (
                df_active_filtered
                .groupby(["systemName", "status"])
                .size()
                .reset_index(name="Count")
            )

            complete_index = pd.MultiIndex.from_product(
                [all_affiliates, active_statuses],
                names=["systemName", "status"]
            )

            chart_df = (
                chart_df
                .set_index(["systemName", "status"])
                .reindex(complete_index, fill_value=0)
                .reset_index()
            )

            fig = px.bar(
                chart_df,
                x="systemName",
                y="Count",
                color="status",
                barmode="stack",
                text="Count"
            )

            fig.update_layout(xaxis_title="", yaxis_title="Active Alerts")
            st.plotly_chart(fig, use_container_width=True)

        else:
            chart_df = (
                df_active_filtered
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

            fig.update_layout(xaxis_title="", yaxis_title="Active Alerts")
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
        )

        pivot_table = affiliate_stats.pivot(
            index="systemName",
            columns="status",
            values="Count"
        ).fillna(0)

        st.dataframe(pivot_table, use_container_width=True)

    # ================= Alert Statistics =================
    with tab2:
        st.subheader("Alert Statistics")
        st.info("Placeholder for Alert Statistics")

    # ================= Alert Management =================
    with tab3:
        st.subheader("Alert Management")
        st.info("Placeholder for Alert Management")
