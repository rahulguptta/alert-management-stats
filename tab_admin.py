import streamlit as st
import pandas as pd


def render(all_existing_people):

    st.subheader("Admin Controlled — Member Management")

    DEFAULT_ROLES = [
        "Process Engineer",
        "Process Manager",
        "Operation Engineer",
        "Operation Manager"
    ]

    person_options  = ["Add New Member"] + all_existing_people
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
