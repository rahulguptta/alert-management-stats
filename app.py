import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

# ================= SESSION STATE INIT (outside file block) =================
if "people_roles" not in st.session_state:
    st.session_state["people_roles"] = {}

if "roles_initialized" not in st.session_state:
    st.session_state["roles_initialized"] = False

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:

    # ================= READ FILE =================
    df_raw = pd.read_excel(uploaded_file, header=None)

    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.iloc[0]
    df = df_raw.iloc[1:].reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()

    # ================= SYSTEM NAME MAPPING =================
    system_mapping = {
        "COLD SECTIONS COLUMNS": "Column Section",
        "QUENCH SYSTEM": "Quench Tower",
        "CHARGE GAS COMPRESSOR": "CGC Section",
        "ACETYLENE REACTORS OPTIMIZATION": "Acetylene Reactors"
    }
    df["systemName"] = df["systemName"].replace(system_mapping)

    # ================= ASSIGNEE MAPPING =================
    assignee_mapping = {
        "PAVLOV ANDRES ROMERO PEREZ": "Parvaze Aalam",
        "Ahmed Hassan Ahmed Faqqas": "Ashawani Arora",
        "Omer Ali Abdullah AlAli": "John Doe Paul",
        "Talaal Salah Abdullah Alabdulkareem": "Rashmina Raj Kumari"
    }
    df["currentAssignee"] = df["currentAssignee"].replace(assignee_mapping)
    df["lastActionTakenBy"] = df["lastActionTakenBy"].replace(assignee_mapping)

    # ================= DATETIME CONVERSION =================
    df["deviationTime"] = pd.to_datetime(df["deviationTime"], errors="coerce")

    # ================= INIT DEFAULT ROLES ONCE AFTER MAPPING =================
    if not st.session_state["roles_initialized"]:
        st.session_state["people_roles"] = {
            'Parvaze Aalam': 'Process Engineer',
            'Ashawani Arora': 'Process Manager',
            'John Doe Paul': 'Operation Engineer',
            'Rashmina Raj Kumari': 'Operation Manager'
        }
        st.session_state["roles_initialized"] = True

    # ================= APPLY ROLE COLUMN TO FULL DATAFRAME =================
    df["Role"] = df["currentAssignee"].map(
        st.session_state["people_roles"]
    ).fillna("Other")

    # ================= REMOVE CLOSED FOR CHARTS =================
    df_active = df[~df["status"].str.lower().str.contains("closed", na=False)]

    # ================= COLLECT ALL EXISTING PEOPLE FROM DATA =================
    existing_assignees = set(df["currentAssignee"].dropna().unique().tolist())
    existing_last_action = set(df["lastActionTakenBy"].dropna().unique().tolist())
    all_existing_people = sorted(
        existing_assignees.union(existing_last_action) |
        set(st.session_state["people_roles"].keys())
    )

    # ================= SIDEBAR =================
    st.sidebar.header("Filters")

    min_date = df["deviationTime"].min()
    max_date = df["deviationTime"].max()

    period = st.sidebar.date_input(
        "Select Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    start_date, end_date = period

    affiliates = sorted(df["systemName"].dropna().unique())
    affiliate_selected = st.sidebar.selectbox(
        "Select System",
        ["All"] + list(affiliates),
        index=0
    )

    # ================= SIDEBAR DOWNLOAD =================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Download")

    def convert_df_to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Updated Data")
        return output.getvalue()

    excel_data = convert_df_to_excel(df)

    st.sidebar.download_button(
        label="Download Updated Data (Excel)",
        data=excel_data,
        file_name="updated_alert_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ================= FILTER DATAFRAME =================
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

    # ================= TABS =================
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management", "Admin Controlled"]
    )

    # ================= OVERVIEW =================
    with tab1:

        st.subheader("Active Alerts Overview")

        chart_df = (
            df_active_filtered
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

        # ================= STATUS BY SYSTEM TABLE =================
        # Only show when "All" systems selected
        if affiliate_selected == "All":
            st.markdown("### Status by System")

            # Use full date-filtered df (not active only) to include all statuses
            status_by_system = (
                df_filtered
                .groupby(["systemName", "status"])
                .size()
                .reset_index(name="Count")
            )

            # Pivot: systems as rows, statuses as columns
            pivot_table = status_by_system.pivot_table(
                index="systemName",
                columns="status",
                values="Count",
                aggfunc="sum",
                fill_value=0
            )

            # Clean up axis labels
            pivot_table.index.name = "System"
            pivot_table.columns.name = None

            st.dataframe(pivot_table, use_container_width=True)

    # ================= ALERT STATISTICS =================
    with tab2:

        st.subheader("Alert Statistics")

        if df_filtered.empty:
            st.warning("No data available for selected filters.")
            st.stop()

        # ================= MONTH FILTER =================
        df_filtered["MonthDisplay"] = df_filtered["deviationTime"].dt.strftime("%B %Y")
        df_filtered["MonthSort"] = df_filtered["deviationTime"].dt.to_period("M")

        month_df = (
            df_filtered[["MonthDisplay", "MonthSort"]]
            .drop_duplicates()
            .sort_values("MonthSort")
        )

        month_options = ["All"] + month_df["MonthDisplay"].tolist()
        selected_month = st.selectbox("Select Month", month_options, index=0)

        if selected_month == "All":
            df_month = df_filtered.copy()
        else:
            df_month = df_filtered[df_filtered["MonthDisplay"] == selected_month]

        # ================= STATUS CLASSIFICATION =================
        status_lower = df_month["status"].str.lower()

        total_generated = len(df_month)
        total_closed = df_month[status_lower.str.contains("closed", na=False)].shape[0]
        total_active = total_generated - total_closed

        pending = df_month[status_lower.str.contains("pending", na=False)].shape[0]
        implemented = df_month[status_lower.str.contains("implemented", na=False)].shape[0]
        rejected = df_month[status_lower.str.contains("rejected", na=False)].shape[0]
        wip = df_month[status_lower.str.contains("progress", na=False)].shape[0]
        overdue = df_month[status_lower.str.contains("overdue", na=False)].shape[0]

        auto_closed = df_month[
            df_month["status"].str.contains("System", case=False, na=False)
        ].shape[0]

        overdue_3 = df_month[
            (status_lower.str.contains("overdue", na=False)) &
            ((pd.Timestamp.today() - df_month["deviationTime"]).dt.days > 3)
        ].shape[0]

        target_revision = total_active

        # ================= KPI LAYOUT =================
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Generated Alerts", total_generated)
        col2.metric("Total Active", total_active)
        col3.metric("Total Closed", total_closed)

        st.markdown("---")

        col1, col2 = st.columns(2)
        col1.metric("Pending", pending)
        col2.metric("Implemented", implemented)

        col1, col2 = st.columns(2)
        col1.metric("Work In Progress", wip)
        col2.metric("Rejected", rejected)

        col1, col2 = st.columns(2)
        col1.metric("Overdue", overdue)
        col2.metric("Auto Closed", auto_closed)

        col1, col2 = st.columns(2)
        col1.metric("No. of Overdue Alerts (>3 days)", overdue_3)
        col2.metric("Target Date Revision (Active Alerts)", target_revision)

        st.markdown("---")

        # ================= ACTIVE ALERTS BY ROLE =================
        st.markdown("### Active Alerts by Role")

        df_active_month = df_month[
            ~status_lower.str.contains("closed", na=False)
        ].copy()

        role_df = (
            df_active_month
            .groupby("Role")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )

        if not role_df.empty:
            fig_role = px.bar(
                role_df,
                x="Role",
                y="Count",
                text="Count"
            )
            fig_role.update_layout(
                xaxis_title="Role",
                yaxis_title="Active Alerts",
                xaxis=dict(type="category")
            )
            st.plotly_chart(fig_role, use_container_width=True)
        else:
            st.info("No active alerts in selected month.")

    # ================= ALERT MANAGEMENT =================
    with tab3:

        st.subheader("Alert Management")

        if df_filtered.empty:
            st.warning("No data available for selected filters.")
            st.stop()

        col1, col2 = st.columns(2)

        category_options = ["All", "Energy", "Production", "Environment"]
        selected_category = col1.selectbox("Category", category_options)

        deviation_options = ["All", "Pending"]
        selected_deviation = col2.selectbox("Deviation", deviation_options)

        df_mgmt = df_filtered.copy()

        if selected_category == "Energy":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains("energy", case=False, na=False)
            ]
        elif selected_category == "Production":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains(
                    "production|throughput|rate|capacity|output",
                    case=False, na=False
                )
            ]
        elif selected_category == "Environment":
            df_mgmt = df_mgmt[
                df_mgmt["odsCauseTagName"].str.contains(
                    "environment|emission|flare|co2|pollution",
                    case=False, na=False
                )
            ]

        if selected_deviation == "Pending":
            df_mgmt = df_mgmt[
                df_mgmt["status"].str.contains("pending", case=False, na=False)
            ]

        if df_mgmt.empty:
            st.info("No records found.")
            st.stop()

        display_df = pd.DataFrame({
            "Alert ID": df_mgmt["requestID"],
            "Category": df_mgmt["odsCauseTagName"],
            "Cause (System)": df_mgmt["causeMessage"].fillna("") + " | " + df_mgmt["systemName"].fillna(""),
            "KPI": df_mgmt["odsCauseTagName"],
            "Deviation": df_mgmt["status"],
            "Due Date": "",
            "Comments": df_mgmt["comments"].fillna("")
        })

        display_df = display_df.reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)

    # ================= ADMIN CONTROLLED =================
    with tab4:

        st.subheader("Admin Controlled — Member Management")

        DEFAULT_ROLES = [
            "Process Engineer",
            "Process Manager",
            "Operation Engineer",
            "Operation Manager"
        ]

        person_options = ["Add New Member"] + all_existing_people
        selected_person = st.selectbox("Select Member", person_options)

        if selected_person == "Add New Member":
            new_name = st.text_input("Enter Full Name")
            new_role = st.selectbox("Assign Role", DEFAULT_ROLES)

            if st.button("Add Member"):
                if new_name.strip() == "":
                    st.warning("Please enter a valid name.")
                elif new_name.strip() in all_existing_people:
                    st.warning(
                        f"'{new_name.strip()}' already exists. "
                        f"Select them from the dropdown to change their role."
                    )
                else:
                    st.session_state["people_roles"][new_name.strip()] = new_role
                    st.success(f"'{new_name.strip()}' added as '{new_role}'.")
                    st.rerun()

        else:
            current_role = st.session_state["people_roles"].get(selected_person, "Not Assigned")
            st.info(f"Current Role: **{current_role}**")

            updated_role = st.selectbox(
                "Change Role To",
                DEFAULT_ROLES,
                index=DEFAULT_ROLES.index(current_role) if current_role in DEFAULT_ROLES else 0
            )

            if st.button("Update Role"):
                st.session_state["people_roles"][selected_person] = updated_role
                st.success(f"Role of '{selected_person}' updated to '{updated_role}'.")
                st.rerun()

        # ================= CURRENT MEMBERS TABLE =================
        st.markdown("---")
        st.markdown("### Current Member Registry")

        registry_df = pd.DataFrame(
            list(st.session_state["people_roles"].items()),
            columns=["Name", "Role"]
        )
        st.dataframe(registry_df, use_container_width=True)
