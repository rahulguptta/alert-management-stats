import streamlit as st
import pandas as pd


def render(df_filtered):

    st.subheader("Alert Management")

    if df_filtered.empty:
        st.warning("No data available for selected filters.")
        st.stop()

    col1, col2 = st.columns(2)
    category_options  = ["All", "Energy", "Production", "Environment"]
    deviation_options = ["All", "Pending"]

    selected_category  = col1.selectbox("Category",  category_options,  key="category_select")
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
        "Alert ID":      df_mgmt["requestID"],
        "Category":      df_mgmt["odsCauseTagName"],
        "Cause (System)":df_mgmt["causeMessage"].fillna("") + " | " + df_mgmt["systemName"].fillna(""),
        "KPI":           df_mgmt["odsCauseTagName"],
        "Deviation":     df_mgmt["status"],
        "Due Date":      "",
        "Comments":      df_mgmt["comments"].fillna("")
    })

    display_df = display_df.reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)
