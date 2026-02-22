# ==========================================================
# ADD BELOW YOUR EXISTING FIRST PAGE (DO NOT REMOVE IT)
# ==========================================================

st.markdown("---")
st.header("Advanced Alert Section")

tab1, tab2 = st.tabs(["Alert Management", "Alert Statistics"])


# ==========================================================
# TAB 1 - PLACEHOLDER
# ==========================================================
with tab1:
    st.info("Alert Management section will be implemented later.")


# ==========================================================
# TAB 2 - ALERT STATISTICS (MONTHLY VIEW)
# ==========================================================
with tab2:

    # Month Filter (only inside this tab)
    df["month_year"] = df["deviationTime"].dt.strftime("%B %Y")
    months = sorted(df["month_year"].unique())
    selected_month = st.selectbox("Select Month", months)

    df_month = df[df["month_year"] == selected_month].copy()

    # ================================
    # Status Mapping for Visualization Only
    # ================================
    df_month["status_viz"] = df_month["status"].replace({
        "Closed (System)": "Auto Closed",
        "Closed (Implemented)": "Implemented",
        "Closed (Rejected)": "Rejected"
    })

    # ================================
    # KPI Calculations
    # ================================
    total_generated = len(df_month)
    pending = (df_month["status_viz"] == "Pending").sum()
    wip = (df_month["status_viz"] == "Work In Progress").sum()
    overdue = (df_month["status_viz"] == "Overdue").sum()
    implemented = (df_month["status_viz"] == "Implemented").sum()
    rejected = (df_month["status_viz"] == "Rejected").sum()
    auto_closed = (df_month["status_viz"] == "Auto Closed").sum()

    total_active = pending + wip + overdue
    total_closed = implemented + rejected + auto_closed

    # ================================
    # KPI Layout
    # ================================
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Generated Alerts", total_generated)
    col2.metric("Total Active", total_active)
    col3.metric("Total Closed", total_closed)

    col4, col5, col6 = st.columns(3)
    col4.metric("Pending", pending)
    col5.metric("Work In Progress", wip)
    col6.metric("Overdue", overdue)

    col7, col8, col9 = st.columns(3)
    col7.metric("Implemented", implemented)
    col8.metric("Rejected", rejected)
    col9.metric("Auto Closed", auto_closed)

    st.metric("Target Date Revision", "—")  # Placeholder as requested


    # =====================================================
    # ACTIVE ALERTS BY ROLE (currentAssignee)
    # =====================================================
    st.markdown("### Active Alerts by Role")

    df_active = df_month[df_month["status_viz"].isin(
        ["Pending", "Work In Progress", "Overdue"]
    )]

    role_counts = df_active["currentAssignee"].value_counts()

    fig_role, ax_role = plt.subplots(figsize=(6, 2.8))

    bars = ax_role.bar(role_counts.index, role_counts.values)

    for bar in bars:
        height = bar.get_height()
        ax_role.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            int(height),
            ha='center',
            va='bottom',
            fontsize=9
        )

    ax_role.set_xlabel("")
    ax_role.set_ylabel("")
    ax_role.spines['top'].set_visible(False)
    ax_role.spines['right'].set_visible(False)
    ax_role.spines['left'].set_visible(False)

    plt.xticks(rotation=45)
    st.pyplot(fig_role)


    # =====================================================
    # MONTHLY UTILIZATION REPORT (System Wise - Stacked)
    # =====================================================
    st.markdown("### Monthly Utilization Report")

    system_group = df_month.groupby(["systemName", "status_viz"]).size().unstack(fill_value=0)

    fig_util, ax_util = plt.subplots(figsize=(7, 3))

    bottom = None

    for status in system_group.columns:
        bars = ax_util.bar(
            system_group.index,
            system_group[status],
            bottom=bottom,
            label=status
        )

        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:
                ax_util.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height,
                    int(height),
                    ha='center',
                    va='bottom',
                    fontsize=8
                )

        if bottom is None:
            bottom = system_group[status].values
        else:
            bottom = bottom + system_group[status].values

    ax_util.legend(ncol=len(system_group.columns))
    ax_util.spines['top'].set_visible(False)
    ax_util.spines['right'].set_visible(False)
    ax_util.spines['left'].set_visible(False)

    plt.xticks(rotation=45)
    st.pyplot(fig_util)


    # =====================================================
    # ALERT UTILIZATION RATE
    # =====================================================
    st.markdown("### Alert Utilization Rate")

    if total_generated > 0:
        utilization_rate = round((total_closed / total_generated) * 100, 2)
    else:
        utilization_rate = 0

    st.metric("Utilization Rate (%)", f"{utilization_rate}%")
