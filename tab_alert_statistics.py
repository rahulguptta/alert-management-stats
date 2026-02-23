import streamlit as st
import pandas as pd
import plotly.express as px


def render(df_filtered):

    st.subheader("Alert Statistics")

    if df_filtered.empty:
        st.warning("No data available for selected filters.")
        st.stop()

    df_filtered["MonthDisplay"] = df_filtered["deviationTime"].dt.strftime("%B %Y")
    df_filtered["MonthSort"] = df_filtered["deviationTime"].dt.to_period("M")

    month_df = (
        df_filtered[["MonthDisplay", "MonthSort"]]
        .drop_duplicates()
        .sort_values("MonthSort")
    )

    month_options = ["All"] + month_df["MonthDisplay"].tolist()
    selected_month = st.selectbox("Select Month", month_options, index=0, key="month_select")

    if selected_month == "All":
        df_month = df_filtered.copy()
    else:
        df_month = df_filtered[df_filtered["MonthDisplay"] == selected_month]

    status_lower = df_month["status"].str.lower()

    total_generated = len(df_month)
    total_closed    = df_month[status_lower.str.contains("closed", na=False)].shape[0]
    total_active    = total_generated - total_closed
    pending         = df_month[status_lower.str.contains("pending", na=False)].shape[0]
    implemented     = df_month[status_lower.str.contains("implemented", na=False)].shape[0]
    rejected        = df_month[status_lower.str.contains("rejected", na=False)].shape[0]
    wip             = df_month[status_lower.str.contains("progress", na=False)].shape[0]
    overdue         = df_month[status_lower.str.contains("overdue", na=False)].shape[0]
    auto_closed     = df_month[df_month["status"].str.contains("System", case=False, na=False)].shape[0]
    overdue_3       = df_month[
        (status_lower.str.contains("overdue", na=False)) &
        ((pd.Timestamp.today() - df_month["deviationTime"]).dt.days > 3)
    ].shape[0]
    target_revision = total_active

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Generated Alerts", total_generated)
    col2.metric("Total Active",           total_active)
    col3.metric("Total Closed",           total_closed)

    st.markdown("---")

    col1, col2 = st.columns(2)
    col1.metric("Pending",     pending)
    col2.metric("Implemented", implemented)

    col1, col2 = st.columns(2)
    col1.metric("Work In Progress", wip)
    col2.metric("Rejected",         rejected)

    col1, col2 = st.columns(2)
    col1.metric("Overdue",     overdue)
    col2.metric("Auto Closed", auto_closed)

    col1, col2 = st.columns(2)
    col1.metric("No. of Overdue Alerts (>3 days)",    overdue_3)
    col2.metric("Target Date Revision (Active Alerts)", target_revision)

    st.markdown("---")
    st.markdown("### Active Alerts by Role")

    df_active_month = df_month[~status_lower.str.contains("closed", na=False)].copy()

    role_df = (
        df_active_month
        .groupby("Role")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    if not role_df.empty:
        fig_role = px.bar(role_df, x="Role", y="Count", text="Count")
        fig_role.update_layout(
            xaxis_title="Role",
            yaxis_title="Active Alerts",
            xaxis=dict(type="category")
        )
        st.plotly_chart(fig_role, use_container_width=True)
    else:
        st.info("No active alerts in selected month.")
