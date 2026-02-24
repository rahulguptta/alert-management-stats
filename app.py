import streamlit as st
import pandas as pd
from io import BytesIO

import tab_overview
import tab_alert_statistics
import tab_alert_management
import tab_admin
import tab_alert_config

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

# ================= SESSION STATE INIT =================
if "people_roles" not in st.session_state:
    st.session_state["people_roles"] = {}

if "roles_initialized" not in st.session_state:
    st.session_state["roles_initialized"] = False

if "df_master" not in st.session_state:
    st.session_state["df_master"] = None

if "system_mapping" not in st.session_state:
    st.session_state["system_mapping"] = {}

if "mapping_confirmed" not in st.session_state:
    st.session_state["mapping_confirmed"] = False

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="excel_uploader")

if uploaded_file is not None:

    # ================= READ FILE =================
    df_raw = pd.read_excel(uploaded_file, header=None)
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.iloc[0]
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.columns.astype(str).str.strip()

    # ================= SYSTEM MAPPING UI =================
    # Show mapping UI only once per file upload
    if not st.session_state["mapping_confirmed"]:

        st.markdown("---")
        st.markdown("### System Name Mapping")
        st.markdown(
            "You can provide custom display names for each system below. "
            "If left unchanged, the original names will be used."
        )

        raw_systems = sorted(df_raw["systemName"].dropna().unique().tolist())

        default_mapping = {
            "COLD SECTIONS COLUMNS":        "Column Section",
            "QUENCH SYSTEM":                "Quench Tower",
            "CHARGE GAS COMPRESSOR":        "CGC Section",
            "ACETYLENE REACTORS OPTIMIZATION": "Acetylene Reactors"
        }

        user_mapping = {}
        for system in raw_systems:
            default_val = default_mapping.get(system, system)
            user_mapping[system] = st.text_input(
                f"Display name for:  `{system}`",
                value=default_val,
                key=f"sysmap_{system}"
            )

        if st.button("Confirm Mapping & Load Dashboard", key="confirm_mapping_btn"):
            # Save only entries where user actually changed the name
            final_mapping = {k: v.strip() for k, v in user_mapping.items() if v.strip() != k}
            st.session_state["system_mapping"]   = final_mapping
            st.session_state["mapping_confirmed"] = True
            st.rerun()

        st.stop()

    # ================= APPLY SYSTEM MAPPING =================
    if st.session_state["system_mapping"]:
        df_raw["systemName"] = df_raw["systemName"].replace(st.session_state["system_mapping"])

    # ================= ASSIGNEE MAPPING =================
    assignee_mapping = {
        "PAVLOV ANDRES ROMERO PEREZ":           "Parvaze Aalam",
        "Ahmed Hassan Ahmed Faqqas":            "Ashawani Arora",
        "Omer Ali Abdullah AlAli":              "John Doe Paul",
        "Talaal Salah Abdullah Alabdulkareem":  "Rashmina Raj Kumari"
    }
    df_raw["currentAssignee"]    = df_raw["currentAssignee"].replace(assignee_mapping)
    df_raw["lastActionTakenBy"]  = df_raw["lastActionTakenBy"].replace(assignee_mapping)

    # ================= DATETIME CONVERSION =================
    df_raw["deviationTime"] = pd.to_datetime(df_raw["deviationTime"], errors="coerce")

    # ================= LOAD INTO MASTER ONCE =================
    if st.session_state["df_master"] is None:
        st.session_state["df_master"] = df_raw.copy()

    # ================= INIT DEFAULT ROLES ONCE =================
    if not st.session_state["roles_initialized"]:
        st.session_state["people_roles"] = {
            'Parvaze Aalam':      'Process Engineer',
            'Ashawani Arora':     'Process Manager',
            'John Doe Paul':      'Operation Engineer',
            'Rashmina Raj Kumari':'Operation Manager'
        }
        st.session_state["roles_initialized"] = True

    # ================= WORK FROM MASTER =================
    df = st.session_state["df_master"].copy()

    # ================= APPLY ROLE COLUMN =================
    df["Role"] = df["currentAssignee"].map(
        st.session_state["people_roles"]
    ).fillna("Other")

    # ================= REMOVE CLOSED =================
    df_active = df[~df["status"].str.lower().str.contains("closed", na=False)]

    # ================= EXISTING PEOPLE =================
    existing_assignees   = set(df["currentAssignee"].dropna().unique().tolist())
    existing_last_action = set(df["lastActionTakenBy"].dropna().unique().tolist())
    all_existing_people  = sorted(
        existing_assignees.union(existing_last_action) |
        set(st.session_state["people_roles"].keys())
    )

    all_active_statuses = sorted(df_active["status"].dropna().unique().tolist())
    all_systems         = sorted(df["systemName"].dropna().unique().tolist())

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

    # ================= SIDEBAR — RESET MAPPING =================
    st.sidebar.markdown("---")
    if st.sidebar.button("Re-upload / Reset Mapping", key="reset_mapping_btn"):
        st.session_state["mapping_confirmed"] = False
        st.session_state["system_mapping"]    = {}
        st.session_state["df_master"]         = None
        st.session_state["roles_initialized"] = False
        st.rerun()

    # ================= SIDEBAR DOWNLOAD =================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Download")

    def convert_df_to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Updated Data")
        return output.getvalue()

    st.sidebar.download_button(
        label="Download Updated Data (Excel)",
        data=convert_df_to_excel(df),
        file_name="updated_alert_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_excel"
    )

    # ================= FILTER =================
    df_filtered = df[
        (df["deviationTime"] >= pd.to_datetime(start_date)) &
        (df["deviationTime"] <= pd.to_datetime(end_date))
    ]

    df_active_filtered = df_active[
        (df_active["deviationTime"] >= pd.to_datetime(start_date)) &
        (df_active["deviationTime"] <= pd.to_datetime(end_date))
    ]

    if affiliate_selected != "All":
        df_filtered        = df_filtered[df_filtered["systemName"] == affiliate_selected]
        df_active_filtered = df_active_filtered[df_active_filtered["systemName"] == affiliate_selected]

    # ================= TABS =================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Alert Statistics", "Alert Management",
        "Admin Controlled", "Alert Configuration"
    ])

    with tab1:
        tab_overview.render(
            df_filtered, df_active_filtered,
            all_systems, all_active_statuses, affiliate_selected
        )

    with tab2:
        tab_alert_statistics.render(df_filtered)

    with tab3:
        tab_alert_management.render(df_filtered)

    with tab4:
        tab_admin.render(all_existing_people)

    with tab5:
        tab_alert_config.render(df, all_systems)
