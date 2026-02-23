import streamlit as st
import pandas as pd


def render(df, all_systems):

    st.subheader("Alert Configuration")

    # ================= NEXT REQUEST ID =================
    def get_next_request_id(dataframe):
        existing_ids = pd.to_numeric(dataframe["requestID"], errors="coerce").dropna()
        if existing_ids.empty:
            return 1
        return int(existing_ids.max()) + 1

    # ================= LOOKUP MAPS =================
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

    existing_stage_ids      = sorted(df["stageID"].dropna().unique().tolist())
    existing_assignees_list = sorted(df["currentAssignee"].dropna().unique().tolist())

    left_col, right_col = st.columns(2)

    # ==================================================
    # SECTION 1 — UPDATE ALERT
    # ==================================================
    with left_col:
        st.markdown("### Update Alert")

        upd_system = st.selectbox("System Name", all_systems, key="upd_system")

        upd_tags_for_system = sorted(
            df[df["systemName"] == upd_system]["odsCauseTagName"].dropna().unique().tolist()
        )
        upd_tag = st.selectbox("ODS Cause Tag Name", upd_tags_for_system, key="upd_tag")

        upd_alerts = df[
            (df["systemName"] == upd_system) &
            (df["odsCauseTagName"] == upd_tag)
        ]["requestID"].dropna().unique().tolist()

        upd_alert_id = st.selectbox("Select Alert ID", upd_alerts, key="upd_alert_id")

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

                st.session_state["df_master"].at[idx, "causeValueActual"]  = upd_cause_actual
                st.session_state["df_master"].at[idx, "causeValueOptimum"] = upd_cause_optimum
                st.session_state["df_master"].at[idx, "gap"]               = upd_gap
                st.session_state["df_master"].at[idx, "dueDate"]           = str(upd_due_date)
                st.session_state["df_master"].at[idx, "stageID"]           = upd_stage
                st.session_state["df_master"].at[idx, "currentAssignee"]   = upd_assignee
                st.session_state["df_master"].at[idx, "comments"]          = upd_comments

                st.success(f"Alert **{upd_alert_id}** updated successfully.")
                st.rerun()

    # ==================================================
    # SECTION 2 — CREATE ALERT
    # ==================================================
    with right_col:
        st.markdown("### Create Alert")

        new_system = st.selectbox("System Name", all_systems, key="new_system")

        tags_for_system = sorted(
            df[df["systemName"] == new_system]["odsCauseTagName"].dropna().unique().tolist()
        )
        new_tag = st.selectbox("ODS Cause Tag Name", tags_for_system, key="new_tag")

        auto_cause           = tag_to_cause.get(new_tag, "")
        auto_suggestion      = tag_to_suggestion.get(new_tag, "")
        auto_uom             = tag_to_uom.get(new_tag, "")
        auto_tag_id          = tag_to_id.get(new_tag, "")

        last_occ_df = df[
            (df["systemName"] == new_system) &
            (df["odsCauseTagName"] == new_tag)
        ]["deviationTime"].dropna()
        auto_last_occurrence = last_occ_df.max() if not last_occ_df.empty else "N/A"

        with st.expander("Show Auto-filled Fields", expanded=False):
            st.text_input("Cause Message",    value=auto_cause,                   disabled=True, key="new_cause_msg")
            st.text_input("Suggestion",        value=auto_suggestion,              disabled=True, key="new_suggestion")
            st.text_input("Cause UOM",         value=auto_uom,                     disabled=True, key="new_uom")
            st.text_input("ODS Cause Tag ID",  value=str(auto_tag_id),             disabled=True, key="new_tag_id")
            st.text_input("Last Occurrence",   value=str(auto_last_occurrence),    disabled=True, key="new_last_occ")

        st.markdown("**Fill In Fields**")

        new_cause_actual  = st.text_input("Cause Value Actual",  key="new_cause_actual")
        new_cause_optimum = st.text_input("Cause Value Optimum", key="new_cause_optimum")

        try:
            new_gap = abs(float(new_cause_actual) - float(new_cause_optimum))
            st.info(f"Gap (auto-calculated): **{new_gap}**")
        except:
            new_gap = ""
            st.info("Gap: enter numeric values above to calculate")

        new_due_date = st.date_input("Due Date",  key="new_due_date")

        new_stage = st.selectbox("Stage ID", existing_stage_ids, key="new_stage")

        new_assignee = st.selectbox("Current Assignee", existing_assignees_list, key="new_assignee")

        new_comments = st.text_area("Comments", key="new_comments")

        if st.button("Create Alert", key="create_alert_btn"):
            next_id = get_next_request_id(st.session_state["df_master"])

            new_row = {
                "requestID":         next_id,
                "systemName":        new_system,
                "odsCauseTagName":   new_tag,
                "odsCauseTagID":     auto_tag_id,
                "causeMessage":      auto_cause,
                "causeValueActual":  new_cause_actual,
                "causeValueOptimum": new_cause_optimum,
                "gap":               new_gap,
                "suggestion":        auto_suggestion,
                "causeUom":          auto_uom,
                "lastOccurrence":    auto_last_occurrence,
                "deviationTime":     pd.Timestamp.now(),
                "status":            "Pending",
                "dueDate":           str(new_due_date),
                "stageID":           new_stage,
                "currentAssignee":   new_assignee,
                "lastActionTakenBy": "",
                "comments":          new_comments
            }

            st.session_state["df_master"] = pd.concat(
                [st.session_state["df_master"], pd.DataFrame([new_row])],
                ignore_index=True
            )

            st.success(f"Alert created successfully. Request ID: **{next_id}**")
            st.rerun()
