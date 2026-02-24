import streamlit as st
import pandas as pd
from io import BytesIO
import random

import tab_overview
import tab_alert_statistics
import tab_alert_management
import tab_admin
import tab_alert_config

st.set_page_config(layout="wide")
st.title("Alert Dashboard")

# ================= RANDOM NAME POOLS =================
RANDOM_SYSTEM_NAMES = [
    "Alpha_System", "Beta_Unit", "Gamma_Section", "Delta_Module",
    "Echo_Plant", "Foxtrot_Block", "Gulf_Station", "Hotel_Zone",
    "India_Circuit", "Juliet_Loop", "Kilo_Stage", "Lima_Tower",
    "Metro_Section", "Nova_Unit", "Omega_Block", "Prime_Module"
]

RANDOM_USER_NAMES = [
    "Lucy Lokavo", "Arjun Pandit", "Sara Henning", "Mohamed Khalil",
    "Nina Petrova", "David Okafor", "Lena Müller", "Carlos Vega",
    "Priya Sharma", "James Oduya", "Hana Suzuki", "Ali Hassan",
    "Elena Rossi", "Omar Farouq", "Sofia Andrade", "Ravi Nair"
]

DEFAULT_ROLES = [
    "Process Engineer",
    "Process Manager",
    "Operation Engineer",
    "Operation Manager"
]


def generate_system_mapping(raw_systems):
    """Generate random display names for systems not in default mapping."""
    default = {
        "COLD SECTIONS COLUMNS":           "Column Section",
        "QUENCH SYSTEM":                   "Quench Tower",
        "CHARGE GAS COMPRESSOR":           "CGC Section",
        "ACETYLENE REACTORS OPTIMIZATION": "Acetylene Reactors"
    }
    pool = RANDOM_SYSTEM_NAMES.copy()
    random.shuffle(pool)
    mapping = {}
    pool_idx = 0
    for s in raw_systems:
        if s in default:
            mapping[s] = default[s]
        else:
            mapping[s] = pool[pool_idx % len(pool)]
            pool_idx += 1
    return mapping


def generate_assignee_mapping(raw_assignees):
    """Generate random display names for assignees not in default mapping."""
    default = {
        "PAVLOV ANDRES ROMERO PEREZ":          "Parvaze Aalam",
        "Ahmed Hassan Ahmed Faqqas":           "Ashawani Arora",
        "Omer Ali Abdullah AlAli":             "John Doe Paul",
        "Talaal Salah Abdullah Alabdulkareem": "Rashmina Raj Kumari"
    }
    pool = RANDOM_USER_NAMES.copy()
    # Remove already used default names from pool to avoid duplicates
    used = set(default.values())
    pool = [p for p in pool if p not in used]
    random.shuffle(pool)
    mapping = {}
    pool_idx = 0
    for a in raw_assignees:
        if a in default:
            mapping[a] = default[a]
        else:
            mapping[a] = pool[pool_idx % len(pool)]
            pool_idx += 1
    return mapping


def generate_roles_mapping(mapped_assignees):
    """Assign default roles to all mapped assignee display names."""
    default = {
        "Parvaze Aalam":       "Process Engineer",
        "Ashawani Arora":      "Process Manager",
        "John Doe Paul":       "Operation Engineer",
        "Rashmina Raj Kumari": "Operation Manager"
    }
    roles_cycle = DEFAULT_ROLES.copy()
    mapping = {}
    role_idx = 0
    for name in mapped_assignees:
        if name in default:
            mapping[name] = default[name]
        else:
            mapping[name] = roles_cycle[role_idx % len(roles_cycle)]
            role_idx += 1
    return mapping


# ================= SESSION STATE INIT =================
if "people_roles" not in st.session_state:
    st.session_state["people_roles"] = {}

if "roles_initialized" not in st.session_state:
    st.session_state["roles_initialized"] = False

if "df_master" not in st.session_state:
    st.session_state["df_master"] = None

if "system_mapping" not in st.session_state:
    st.session_state["system_mapping"] = {}

if "assignee_mapping" not in st.session_state:
    st.session_state["assignee_mapping"] = {}

if "mapping_confirmed" not in st.session_state:
    st.session_state["mapping_confirmed"] = False

if "show_mapping_ui" not in st.session_state:
    st.session_state["show_mapping_ui"] = False

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="excel_uploader")

if uploaded_file is not None:

    # ================= READ FILE =================
    df_raw = pd.read_excel(uploaded_file, header=None)
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.iloc[0]
    df_raw = df_raw.iloc[1:].reset_index(drop=True)
    df_raw.columns = df_raw.columns.astype(str).str.strip()

    raw_systems   = sorted(df_raw["systemName"].dropna().unique().tolist())
    raw_assignees = sorted(df_raw["currentAssignee"].dropna().unique().tolist())

    # ================= GENERATE DEFAULT MAPPINGS IF NOT SET =================
    if not st.session_state["system_mapping"]:
        st.session_state["system_mapping"] = generate_system_mapping(raw_systems)

    if not st.session_state["assignee_mapping"]:
        st.session_state["assignee_mapping"] = generate_assignee_mapping(raw_assignees)

    # ================= PRE-LOAD UI =================
    if not st.session_state["mapping_confirmed"]:

        st.markdown("---")

        col_load, col_change = st.columns([1, 1])

        with col_load:
            if st.button("Load Dashboard", key="load_dashboard_btn"):
                # Apply current mappings and lock in
                st.session_state["mapping_confirmed"]  = True
                st.session_state["show_mapping_ui"]    = False
                st.rerun()

        with col_change:
            if st.button("Change Mapping", key="change_mapping_btn"):
                st.session_state["show_mapping_ui"] = True

        # ================= MAPPING UI (only if Change Mapping clicked) =================
        if st.session_state["show_mapping_ui"]:

            st.markdown("---")

            # -------- SECTION 1: System Mapping --------
            st.markdown("#### 1. System Name Mapping")
            updated_system_mapping = {}
            for raw, display in st.session_state["system_mapping"].items():
                updated_system_mapping[raw] = st.text_input(
                    f"`{raw}`",
                    value=display,
                    key=f"sysmap_{raw}"
                )

            st.markdown("---")

            # -------- SECTION 2: Assignee Mapping --------
            st.markdown("#### 2. Assignee Name Mapping")
            updated_assignee_mapping = {}
            for raw, display in st.session_state["assignee_mapping"].items():
                updated_assignee_mapping[raw] = st.text_input(
                    f"`{raw}`",
                    value=display,
                    key=f"assmap_{raw}"
                )

            st.markdown("---")

            # -------- SECTION 3: Roles Mapping --------
            # Roles are based on mapped assignee display names
            st.markdown("#### 3. Role Mapping")

            # Build current roles from mapped assignee names
            mapped_display_names = list(updated_assignee_mapping.values())
            if not st.session_state["people_roles"]:
                current_roles = generate_roles_mapping(mapped_display_names)
            else:
                current_roles = st.session_state["people_roles"]

            updated_roles = {}
            for name in mapped_display_names:
                current_role = current_roles.get(name, DEFAULT_ROLES[0])
                updated_roles[name] = st.selectbox(
                    f"{name}",
                    DEFAULT_ROLES,
                    index=DEFAULT_ROLES.index(current_role)
                          if current_role in DEFAULT_ROLES else 0,
                    key=f"rolemap_{name}"
                )

            st.markdown("---")

            if st.button("Save Mapping", key="save_mapping_btn"):
                st.session_state["system_mapping"]   = {
                    k: v.strip() for k, v in updated_system_mapping.items()
                }
                st.session_state["assignee_mapping"] = {
                    k: v.strip() for k, v in updated_assignee_mapping.items()
                }
                st.session_state["people_roles"]     = updated_roles
                st.session_state["roles_initialized"] = True
                st.success("Mapping saved. Click **Load Dashboard** to proceed.")

        st.stop()

    # ================= APPLY SYSTEM MAPPING =================
    df_raw["systemName"] = df_raw["systemName"].replace(
        st.session_state["system_mapping"]
    )

    # ================= APPLY ASSIGNEE MAPPING =================
    df_raw["currentAssignee"]   = df_raw["currentAssignee"].replace(
        st.session_state["assignee_mapping"]
    )
    df_raw["lastActionTakenBy"] = df_raw["lastActionTakenBy"].replace(
        st.session_state["assignee_mapping"]
    )

    # ================= DATETIME CONVERSION =================
    df_raw["deviationTime"] = pd.to_datetime(df_raw["deviationTime"], errors="coerce")

    # ================= LOAD INTO MASTER ONCE =================
    if st.session_state["df_master"] is None:
        st.session_state["df_master"] = df_raw.copy()

    # ================= INIT DEFAULT ROLES ONCE =================
    if not st.session_state["roles_initialized"]:
        mapped_names = list(st.session_state["assignee_mapping"].values())
        st.session_state["people_roles"]      = generate_roles_mapping(mapped_names)
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

    # ================= SIDEBAR — RESET =================
    st.sidebar.markdown("---")
    if st.sidebar.button("Re-upload / Reset", key="reset_mapping_btn"):
        for key in [
            "mapping_confirmed", "show_mapping_ui", "system_mapping",
            "assignee_mapping", "df_master", "roles_initialized", "people_roles"
        ]:
            st.session_state[key] = False if "confirmed" in key or "initialized" in key or "show" in key else None if key in ["df_master"] else {}
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
