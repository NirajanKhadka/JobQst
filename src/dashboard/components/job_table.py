import streamlit as st
import pandas as pd


def render_job_table(df: pd.DataFrame):
    st.subheader("📋 Job Details")
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("No jobs found for this profile")
        return
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + list(df["status"].unique()) if "status" in df.columns else ["All"],
        )
    with col2:
        experience_filter = st.selectbox(
            "Filter by Experience",
            (
                ["All"] + list(df["experience_level"].unique())
                if "experience_level" in df.columns
                else ["All"]
            ),
        )
    with col3:
        search_term = st.text_input("Search jobs", placeholder="Enter keywords...")
    filtered_df = df.copy()
    if status_filter != "All" and "status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["status"] == status_filter]
    if experience_filter != "All" and "experience_level" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["experience_level"] == experience_filter]
    if search_term:
        if "title" in filtered_df.columns and "company" in filtered_df.columns:
            mask = filtered_df["title"].astype(str).str.contains(
                search_term, case=False, na=False
            ) | filtered_df["company"].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = filtered_df[mask]
    if not filtered_df.empty:
        display_columns = [
            "title",
            "company",
            "location",
            "experience_level",
            "match_score",
            "status",
            "created_at",
        ]
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        st.dataframe(
            filtered_df[available_columns].head(50), use_container_width=True, hide_index=True
        )
        st.caption(f"Showing {len(filtered_df)} of {len(df)} jobs")
    else:
        st.info("No jobs match the current filters")
