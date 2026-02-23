import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import uuid
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

# ================= SESSION STATE INIT (outside file block) =================
if "people_roles" not in st.session_state:
    st.session_state["people_roles"] = {}

if "roles_initialized" not in st.session_state:
    st.session_state["roles_initialized"] = False

if "df_master" not in st.session_state:
    st.session_state["df_master"] = None

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="excel_uploader")

if uploaded_file is not None:

    # ================= READ FILE =================
    df_raw = pd.read_excel(uploaded_file, header=None)
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.iloc[0]
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.columns.astype(str).str.strip()

    # ================= SYSTEM NAME MAPPING =================
    system_mapping = {
        "COLD SECTIONS COLUMNS": "Column Section",
        "QUENCH SYSTEM": "Quench Tower",
        "CHARGE GAS COMPRESSOR": "CGC Section",
        "ACETYLENE REACTORS OPTIMIZATION": "Acetylene Reactors"
    }
    df_raw["systemName"] = df_raw["systemName"].replace(system_mapping)

    # ================= ASSIGNEE MAPPING =================
    assignee_mapping = {
        "PAVLOV ANDRES ROMERO PEREZ": "Parvaze Aalam",
        "Ahmed Hassan Ahmed Faqqas": "Ashawani Arora",
        "Omer Ali Abdullah AlAli": "John Doe Paul",
        "Talaal Salah Abdullah Alabdulkareem": "Rashmina Raj Kumari"
    }
    df_raw["currentAssignee"] = df_raw["currentAssignee"].replace(assignee_mapping)
    df_raw["lastActionTakenBy"] = df_raw["lastActionTakenBy"].replace(assignee_mapping)

    # ================= DATETIME CONVERSION =================
    df_raw["deviationTime"] = pd.to_datetime(df_raw["deviationTime"], errors="coerce")

    # ================= LOAD INTO MASTER ONCE =================
    if st.session_state["df_master"] is None:
        st.session_state["df_master"] = df_raw.copy()

    # ================= INIT DEFAULT ROLES ONCE AFTER MAPPING =================
    if not st.session_state["roles_initialized"]:
        st.session_state["people_roles"] = {
            'Parvaze Aalam': 'Process Engineer',
            'Ashawani Arora': 'Process Manager',
            'John Doe Paul': 'Operation Engineer',
            'Rashmina Raj Kumari': 'Operation Manager'
        }
        st.session_state["roles_initialized"] = True

    # ================= WORK FROM MASTER =================
    df = st.session_state["df_master"].copy()

    # ================= APPLY ROLE COLUMN =================
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

    # ================= ALL UNIQUE STATUSES (excluding closed) =================
    all_active_statuses = sorted(df_active["status"].dropna().unique().tolist())

    # ================= ALL UNIQUE SYSTEMS =================
    all_systems = sorted(df["systemName"].dropna().unique().tolist())

    # ================= SIDEBAR =================
    st.sidebar.header("Filters")

    min_date = df["deviationTime"].min()
    max_date = df["deviationTime"].max()

    period = st.sidebar.date_input(
        "Select Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_period"
    )

    start_date, end_date = period

    affiliates = sorted(df["systemName"].dropna().unique())
    affiliate_selected = st.sidebar.selectbox(
        "Select System",
        ["All"] + list(affiliates),
        index=0,
        key="system_select"
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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_excel"
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Alert Statistics", "Alert Management", "Admin Controlled", "Alert Configuration"]
    )

    # ================= OVERVIEW =================
    with tab1:

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

    # ================= ALERT STATISTICS =================
    with tab2:

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
        total_closed = df_month[status_lower.str.contains("closed", na=False)].shape[0]
        total_active = total_generated - total_closed
        pending = df_month[status_lower.str.contains("pending", na=False)].shape[0]
        implemented = df_month[status_lower.str.contains("implemented", na=False)].shape[0]
        rejected = df_month[status_lower.str.contains("rejected", na=False)].shape[0]
        wip = df_month[status_lower.str.contains("progress", na=False)].shape[0]
        overdue = df_month[status_lower.str.contains("overdue", na=False)].shape[0]
        auto_closed = df_month[df_month["status"].str.contains("System", case=False, na=False)].shape[0]
        overdue_3 = df_month[
            (status_lower.str.contains("overdue", na=False)) &
            ((pd.Timestamp.today() - df_month["deviationTime"]).dt.days > 3)
        ].shape[0]
        target_revision = total_active

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

    # ================= ALERT MANAGEMENT =================
    with tab3:

        st.subheader("Alert Management")

        if df_filtered.empty:
            st.warning("No data available for selected filters.")
            st.stop()

        col1, col2 = st.columns(2)
        category_options = ["All", "Energy", "Production", "Environment"]
        selected_category = col1.selectbox("Category", category_options, key="category_select")

        deviation_options = ["All", "Pending"]
        selected_deviation = col2.selectbox("Deviation", deviation_options, key="deviation_select")

        df_mgmt = df_filtered.copy()

        if selected_category == "Energy":
            df_mgmt = df_mgmt[df_mgmt["odsCauseTagName"].str.contains("energy", case=False, na=False)]
        elif selected_category == "Production":
            df_mgmt = df_mgmt[df_mgmt["odsCauseTagName"].str.contains(
                "production|throughput|rate|capacity|output", case=False, na=False)]
        elif selected_category == "Environment":
            df_mgmt = df_mgmt[df_mgmt["odsCauseTagName"].str.contains(
                "environment|emission|flare|co2|pollution", case=False, na=False)]

        if selected_deviation == "Pending":
            df_mgmt = df_mgmt[df_mgmt["status"].str.contains("pending", case=False, na=False)]

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
        selected_person = st.selectbox("Select Member", person_options, key="admin_person_select")

        if selected_person == "Add New Member":
            new_name = st.text_input("Enter Full Name", key="new_member_name")
            new_role = st.selectbox("Assign Role", DEFAULT_ROLES, key="new_member_role")

            if st.button("Add Member", key="add_member_btn"):
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
                index=DEFAULT_ROLES.index(current_role) if current_role in DEFAULT_ROLES else 0,
                key="update_member_role"
            )

            if st.button("Update Role", key="update_role_btn"):
                st.session_state["people_roles"][selected_person] = updated_role
                st.success(f"Role of '{selected_person}' updated to '{updated_role}'.")
                st.rerun()

        st.markdown("---")
        st.markdown("### Current Member Registry")
        registry_df = pd.DataFrame(
            list(st.session_state["people_roles"].items()),
            columns=["Name", "Role"]
        )
        st.dataframe(registry_df, use_container_width=True)

    # ================= ALERT CONFIGURATION =================
    with tab5:

        # ================= LOOKUP MAPS FROM FULL DF =================
        tag_to_cause = df.dropna(subset=["odsCauseTagName", "causeMessage"]) \
            .drop_duplicates("odsCauseTagName") \
            .set_index("odsCauseTagName")["causeMessage"].to_dict()

        tag_to_suggestion = df.dropna(subset=["odsCauseTagName", "suggestion"]) \
            .drop_duplicates("odsCauseTagName") \
            .set_index("odsCauseTagName")["suggestion"].to_dict() \
            if "suggestion" in df.columns else {}

        tag_to_uom = df.dropna(subset=["odsCauseTagName", "causeUom"]) \
            .drop_duplicates("odsCauseTagName") \
            .set_index("odsCauseTagName")["causeUom"].to_dict() \
            if "causeUom" in df.columns else {}

        tag_to_id = df.dropna(subset=["odsCauseTagName", "odsCauseTagID"]) \
            .drop_duplicates("odsCauseTagName") \
            .set_index("odsCauseTagName")["odsCauseTagID"].to_dict() \
            if "odsCauseTagID" in df.columns else {}

        existing_stage_ids = sorted(df["stageID"].dropna().unique().tolist())
        existing_assignees_list = sorted(df["currentAssignee"].dropna().unique().tolist())

        left_col, right_col = st.columns(2)

        # ==================================================
        # SECTION 1 — UPDATE ALERT
        # ==================================================
        with left_col:
            st.markdown("### Update Alert")

            upd_system = st.selectbox(
                "System Name",
                all_systems,
                key="upd_system"
            )

            upd_tags_for_system = sorted(
                df[df["systemName"] == upd_system]["odsCauseTagName"].dropna().unique().tolist()
            )
            upd_tag = st.selectbox(
                "ODS Cause Tag Name",
                upd_tags_for_system,
                key="upd_tag"
            )

            upd_alerts = df[
                (df["systemName"] == upd_system) &
                (df["odsCauseTagName"] == upd_tag)
            ]["requestID"].dropna().unique().tolist()

            upd_alert_id = st.selectbox(
                "Select Alert ID",
                upd_alerts,
                key="upd_alert_id"
            )

            upd_row = df[df["requestID"] == upd_alert_id]
            upd_row = upd_row.iloc[0] if not upd_row.empty else None

            if upd_row is not None:
                st.markdown("**Edit Fields**")

                upd_cause_actual = st.text_input(
                    "Cause Value Actual",
                    value=str(upd_row.get("causeValueActual", "")),
                    key="upd_cause_actual"
                )
                upd_cause_optimum = st.text_input(
                    "Cause Value Optimum",
                    value=str(upd_row.get("causeValueOptimum", "")),
                    key="upd_cause_optimum"
                )

                try:
                    upd_gap = abs(float(upd_cause_actual) - float(upd_cause_optimum))
                    st.info(f"Gap (auto-calculated): **{upd_gap}**")
                except:
                    upd_gap = ""
                    st.info("Gap: enter numeric values above to calculate")

                upd_due_date = st.date_input("Due Date", key="upd_due_date")

                upd_stage = st.selectbox(
                    "Stage ID",
                    existing_stage_ids,
                    index=existing_stage_ids.index(upd_row.get("stageID"))
                          if upd_row.get("stageID") in existing_stage_ids else 0,
                    key="upd_stage"
                )

                upd_assignee = st.selectbox(
                    "Current Assignee",
                    existing_assignees_list,
                    index=existing_assignees_list.index(upd_row.get("currentAssignee"))
                          if upd_row.get("currentAssignee") in existing_assignees_list else 0,
                    key="upd_assignee"
                )

                upd_comments = st.text_area(
                    "Comments",
                    value=str(upd_row.get("comments", "")),
                    key="upd_comments"
                )

                if st.button("Update Alert", key="update_alert_btn"):
                    idx = st.session_state["df_master"][
                        st.session_state["df_master"]["requestID"] == upd_alert_id
                    ].index[0]

                    st.session_state["df_master"].at[idx, "causeValueActual"] = upd_cause_actual
                    st.session_state["df_master"].at[idx, "causeValueOptimum"] = upd_cause_optimum
                    st.session_state["df_master"].at[idx, "gap"] = upd_gap
                    st.session_state["df_master"].at[idx, "dueDate"] = str(upd_due_date)
                    st.session_state["df_master"].at[idx, "stageID"] = upd_stage
                    st.session_state["df_master"].at[idx, "currentAssignee"] = upd_assignee
                    st.session_state["df_master"].at[idx, "comments"] = upd_comments

                    st.success(f"Alert **{upd_alert_id}** updated successfully.")
                    st.rerun()

        # ==================================================
        # SECTION 2 — CREATE ALERT
        # ==================================================
        with right_col:
            st.markdown("### Create Alert")

            new_system = st.selectbox(
                "System Name",
                all_systems,
                key="new_system"
            )

            tags_for_system = sorted(
                df[df["systemName"] == new_system]["odsCauseTagName"].dropna().unique().tolist()
            )
            new_tag = st.selectbox(
                "ODS Cause Tag Name",
                tags_for_system,
                key="new_tag"
            )

            # ================= AUTO FIELDS (collapsible) =================
            auto_cause   = tag_to_cause.get(new_tag, "")
            auto_suggestion = tag_to_suggestion.get(new_tag, "")
            auto_uom     = tag_to_uom.get(new_tag, "")
            auto_tag_id  = tag_to_id.get(new_tag, "")

            last_occ_df = df[
                (df["systemName"] == new_system) &
                (df["odsCauseTagName"] == new_tag)
            ]["deviationTime"].dropna()
            auto_last_occurrence = last_occ_df.max() if not last_occ_df.empty else "N/A"

            with st.expander("Show Auto-filled Fields", expanded=False):
                st.text_input("Cause Message",    value=auto_cause,          disabled=True, key="new_cause_msg")
                st.text_input("Suggestion",        value=auto_suggestion,     disabled=True, key="new_suggestion")
                st.text_input("Cause UOM",         value=auto_uom,            disabled=True, key="new_uom")
                st.text_input("ODS Cause Tag ID",  value=str(auto_tag_id),    disabled=True, key="new_tag_id")
                st.text_input("Last Occurrence",   value=str(auto_last_occurrence), disabled=True, key="new_last_occ")

            # ================= USER FIELDS =================
            st.markdown("**Fill In Fields**")

            new_cause_actual  = st.text_input("Cause Value Actual",  key="new_cause_actual")
            new_cause_optimum = st.text_input("Cause Value Optimum", key="new_cause_optimum")

            try:
                new_gap = abs(float(new_cause_actual) - float(new_cause_optimum))
                st.info(f"Gap (auto-calculated): **{new_gap}**")
            except:
                new_gap = ""
                st.info("Gap: enter numeric values above to calculate")

            new_due_date = st.date_input("Due Date", key="new_due_date")

            new_stage = st.selectbox(
                "Stage ID",
                existing_stage_ids,
                key="new_stage"
            )

            new_assignee = st.selectbox(
                "Current Assignee",
                existing_assignees_list,
                key="new_assignee"
            )

            new_comments = st.text_area("Comments", key="new_comments")

            if st.button("Create Alert", key="create_alert_btn"):
                next_id = get_next_request_id(st.session_state["df_master"])

                new_row = {
                    "requestID":        next_id,
                    "systemName":       new_system,
                    "odsCauseTagName":  new_tag,
                    "odsCauseTagID":    auto_tag_id,
                    "causeMessage":     auto_cause,
                    "causeValueActual": new_cause_actual,
                    "causeValueOptimum":new_cause_optimum,
                    "gap":              new_gap,
                    "suggestion":       auto_suggestion,
                    "causeUom":         auto_uom,
                    "lastOccurrence":   auto_last_occurrence,
                    "deviationTime":    pd.Timestamp.now(),
                    "status":           "Pending",
                    "dueDate":          str(new_due_date),
                    "stageID":          new_stage,
                    "currentAssignee":  new_assignee,
                    "lastActionTakenBy": "",
                    "comments":         new_comments
                }

                st.session_state["df_master"] = pd.concat(
                    [st.session_state["df_master"], pd.DataFrame([new_row])],
                    ignore_index=True
                )

                st.success(f"Alert created successfully. Request ID: **{next_id}**")
                st.rerun()
