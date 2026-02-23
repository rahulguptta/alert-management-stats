import streamlit as st
import pandas as pd
import plotly.express as px


def render(df_filtered, df_active_filtered, all_systems, all_active_statuses, affiliate_selected):

    st.subheader("Active Alerts Overview")

    if affiliate_selected == "All":

        full_index = pd.MultiIndex.from_product(
            [all_systems, all_active_statuses],
            names=["systemName", "status"]
        )
        full_skeleton = pd.DataFrame(index=full_index).reset_index()
        full_skeleton["Count"] = 0

        chart_df = (
            df_active_filtered
            .groupby(["systemName", "status"])
            .size()
            .reset_index(name="Count")
        )

        chart_df_full = full_skeleton.merge(chart_df, on=["systemName", "status"], how="left")
        chart_df_full["Count"] = chart_df_full["Count_y"].fillna(chart_df_full["Count_x"])
        chart_df_full = chart_df_full[["systemName", "status", "Count"]]

        fig = px.bar(
            chart_df_full,
            x="systemName",
            y="Count",
            color="status",
            barmode="stack",
            text="Count"
        )
        fig.update_layout(xaxis_title="", yaxis_title="Active Alerts")
        st.plotly_chart(fig, use_container_width=True)

    else:

        system_skeleton = pd.DataFrame({"status": all_active_statuses, "Count": 0})

        chart_df_system = (
            df_active_filtered
            .groupby("status")
            .size()
            .reset_index(name="Count")
        )

        chart_df_system_full = system_skeleton.merge(chart_df_system, on="status", how="left")
        chart_df_system_full["Count"] = chart_df_system_full["Count_y"].fillna(
            chart_df_system_full["Count_x"]
        )
        chart_df_system_full = chart_df_system_full[["status", "Count"]]

        fig = px.bar(
            chart_df_system_full,
            x="status",
            y="Count",
            color="status",
            text="Count"
        )
        fig.update_layout(
            xaxis_title="Status",
            yaxis_title="Active Alerts",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Overall Status Statistics")
    overall_stats = df_filtered["status"].value_counts().reset_index()
    overall_stats.columns = ["Status", "Count"]
    st.dataframe(overall_stats, use_container_width=True)

    if affiliate_selected == "All":
        st.markdown("### Status by System")
        status_by_system = (
            df_filtered
            .groupby(["systemName", "status"])
            .size()
            .reset_index(name="Count")
        )
        pivot_table = status_by_system.pivot_table(
            index="systemName",
            columns="status",
            values="Count",
            aggfunc="sum",
            fill_value=0
        )
        pivot_table.index.name = "System"
        pivot_table.columns.name = None
        st.dataframe(pivot_table, use_container_width=True)
