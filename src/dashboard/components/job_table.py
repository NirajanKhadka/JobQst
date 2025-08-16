"""
Enhanced Job Table Component for AutoJobAgent Dashboard

This module provides comprehensive job table display functionality with AI analysis,
detailed job information, and Improved filtering capabilities.
"""

from typing import List, Optional, Dict, Any
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def render_job_table(df: pd.DataFrame, max_rows: int = 50) -> None:
    """
    Render an Improved filterable job table with AI analysis and detailed information.
    
    Args:
        df: DataFrame containing job data with AI analysis
        max_rows: Maximum number of rows to display (default: 50)
        
    Returns:
        None: Renders table directly to Streamlit
    """
    st.subheader("📋 Enhanced Job Details with AI Analysis")
    
    # Validate input data
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("No jobs found for this profile")
        return
    
    # Render Improved filter controls
    filters = _render_Improved_filter_controls(df)
    
    # Apply filters to data
    filtered_df = _apply_Improved_filters(df, filters)
    
    # Display filtered results with Improved information
    _display_Improved_job_results(filtered_df, df, max_rows)


def get_available_columns(df: pd.DataFrame) -> List[str]:
    """
    Get available columns from job DataFrame.
    
    Args:
        df: DataFrame containing job data
        
    Returns:
        List of available column names
    """
    if df is None or df.empty:
        return []
    return list(df.columns)


def _render_Improved_filter_controls(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Render Improved filter controls for job table.
    
    Args:
        df: DataFrame containing job data
        
    Returns:
        Dictionary containing filter values
    """
    st.markdown("### 🔍 Improved Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Status filter
        status_options = ["All"] + sorted(df["status"].unique().tolist()) if "status" in df.columns else ["All"]
        status_filter = st.selectbox(
            "📊 Status",
            status_options,
            help="Filter jobs by their current status"
        )
        
        # AI Score filter
        ai_score_filter = st.slider(
            "🎯 AI Compatibility Score",
            min_value=0.0,
            max_value=1.0,
            value=(0.0, 1.0),
            step=0.1,
            help="Filter by AI-generated compatibility score"
        )
    
    with col2:
        # Experience level filter
        experience_options = ["All"] + sorted(df["experience_level"].unique().tolist()) if "experience_level" in df.columns else ["All"]
        experience_filter = st.selectbox(
            "👨‍💼 Experience Level",
            experience_options,
            help="Filter jobs by required experience level"
        )
        
        # Location filter
        location_options = ["All"] + sorted(df["location"].unique().tolist()) if "location" in df.columns else ["All"]
        location_filter = st.selectbox(
            "📍 Location",
            location_options,
            help="Filter jobs by location"
        )
    
    with col3:
        # Company filter
        company_options = ["All"] + sorted(df["company"].unique().tolist()) if "company" in df.columns else ["All"]
        company_filter = st.selectbox(
            "🏢 Company",
            company_options,
            help="Filter jobs by company"
        )
        
        # Salary range filter
        salary_filter = st.selectbox(
            "💰 Salary Range",
            ["All", "Under $50k", "$50k-$75k", "$75k-$100k", "$100k+"],
            help="Filter by salary range"
        )
    
    with col4:
        # Search functionality
        search_term = st.text_input(
            "🔍 Search Jobs",
            placeholder="Enter keywords...",
            help="Search in job titles, descriptions, and company names"
        )
        
        # Sort options
        sort_by = st.selectbox(
            "📈 Sort By",
            ["AI Score (High to Low)", "Date Posted", "Company", "Title", "Location"],
            help="Sort jobs by different criteria"
        )
    
    return {
        "status": status_filter,
        "ai_score_min": ai_score_filter[0],
        "ai_score_max": ai_score_filter[1],
        "experience": experience_filter,
        "location": location_filter,
        "company": company_filter,
        "salary": salary_filter,
        "search": search_term,
        "sort_by": sort_by
    }


def _apply_Improved_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply Improved filters to the DataFrame.
    
    Args:
        df: Original DataFrame
        filters: Filter values dictionary
        
    Returns:
        Filtered DataFrame
    """
    filtered_df = df.copy()
    
    # Status filter
    if filters["status"] != "All" and "status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["status"] == filters["status"]]
    
    # AI Score filter
    if "compatibility_score" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["compatibility_score"] >= filters["ai_score_min"]) &
            (filtered_df["compatibility_score"] <= filters["ai_score_max"])
        ]
    
    # Experience filter
    if filters["experience"] != "All" and "experience_level" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["experience_level"] == filters["experience"]]
    
    # Location filter
    if filters["location"] != "All" and "location" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["location"] == filters["location"]]
    
    # Company filter
    if filters["company"] != "All" and "company" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["company"] == filters["company"]]
    
    # Salary filter
    if filters["salary"] != "All" and "salary_range" in filtered_df.columns:
        salary_mapping = {
            "Under $50k": lambda x: x.astype(str).str.contains(r'\$[0-4][0-9],?[0-9]{3}', na=False),
            "$50k-$75k": lambda x: x.astype(str).str.contains(r'\$[5-7][0-9],?[0-9]{3}', na=False),
            "$75k-$100k": lambda x: x.astype(str).str.contains(r'\$[7-9][0-9],?[0-9]{3}', na=False),
            "$100k+": lambda x: x.astype(str).str.contains(r'\$[1-9][0-9]{2},?[0-9]{3}', na=False)
        }
        if filters["salary"] in salary_mapping:
            filtered_df = filtered_df[salary_mapping[filters["salary"]](filtered_df["salary_range"])]
    
    # Search filter
    if filters["search"]:
        search_mask = (
            filtered_df["title"].str.contains(filters["search"], case=False, na=False) |
            filtered_df["company"].str.contains(filters["search"], case=False, na=False) |
            filtered_df["location"].str.contains(filters["search"], case=False, na=False) |
            filtered_df["description"].str.contains(filters["search"], case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    # Sort results
    filtered_df = _sort_dataframe(filtered_df, filters["sort_by"])
    
    return filtered_df


def _sort_dataframe(df: pd.DataFrame, sort_by: str) -> pd.DataFrame:
    """
    Sort DataFrame based on specified criteria.
    
    Args:
        df: DataFrame to sort
        sort_by: Sorting criteria
        
    Returns:
        Sorted DataFrame
    """
    if sort_by == "AI Score (High to Low)" and "compatibility_score" in df.columns:
        return df.sort_values("compatibility_score", ascending=False)
    elif sort_by == "Date Posted" and "created_at" in df.columns:
        return df.sort_values("created_at", ascending=False)
    elif sort_by == "Company" and "company" in df.columns:
        return df.sort_values("company")
    elif sort_by == "Title" and "title" in df.columns:
        return df.sort_values("title")
    elif sort_by == "Location" and "location" in df.columns:
        return df.sort_values("location")
    else:
        return df


def _display_Improved_job_results(filtered_df: pd.DataFrame, original_df: pd.DataFrame, max_rows: int) -> None:
    """
    Display enhanced job results with detailed information and AI analysis.
    
    Args:
        filtered_df: Filtered DataFrame to display
        original_df: Original DataFrame for comparison
        max_rows: Maximum number of rows to display
    """
    if filtered_df.empty:
        st.info("No jobs match the current filters")
        return
    
    # Show summary statistics
    _display_job_summary_stats(filtered_df, original_df)
    
    # Display jobs in expandable sections
    st.markdown("### 📋 Job Details")
    
    for idx, row in filtered_df.head(max_rows).iterrows():
        _display_job_card(row, idx)


def _display_job_summary_stats(filtered_df: pd.DataFrame, original_df: pd.DataFrame) -> None:
    """
    Display summary statistics for the filtered jobs.
    
    Args:
        filtered_df: Filtered DataFrame
        original_df: Original DataFrame
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", len(original_df))
    
    with col2:
        st.metric("Filtered Jobs", len(filtered_df))
    
    with col3:
        if "compatibility_score" in filtered_df.columns:
            avg_score = filtered_df["compatibility_score"].mean()
            st.metric("Avg AI Score", f"{avg_score:.1%}")
    
    with col4:
        if "company" in filtered_df.columns:
            unique_companies = filtered_df["company"].nunique()
            st.metric("Companies", unique_companies)


def _display_job_card(job: pd.Series, job_idx: int) -> None:
    """
    Display a detailed job card with AI analysis.
    
    Args:
        job: Job data as pandas Series
        job_idx: Job index for unique keys
    """
    with st.expander(f"🎯 {job.get('title', 'Unknown Title')} at {job.get('company', 'Unknown Company')}", expanded=False):
        
        # Main job information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**🏢 Company:** {job.get('company', 'N/A')}")
            st.markdown(f"**📍 Location:** {job.get('location', 'N/A')}")
            st.markdown(f"**👨‍💼 Experience:** {job.get('experience_level', 'N/A')}")
            st.markdown(f"**💰 Salary:** {job.get('salary_range', 'N/A')}")
            st.markdown(f"**📅 Posted:** {job.get('created_at', 'N/A')}")
        
        with col2:
            # AI Analysis Summary
            if "compatibility_score" in job:
                score = job["compatibility_score"]
                score_color = _get_score_color(score)
                st.markdown(f"**🎯 AI Compatibility:** <span style='color: {score_color}; font-weight: bold;'>{score:.1%}</span>", unsafe_allow_html=True)
            
            if "confidence" in job:
                confidence = job["confidence"]
                st.markdown(f"**🤖 AI Confidence:** {confidence:.1%}")
        
        # AI Analysis Details
        if "llm_analysis" in job and job["llm_analysis"]:
            _display_ai_analysis_details(job["llm_analysis"])
        
        # Skill Analysis
        _display_skill_analysis(job)
        
        # Job Description
        if "description" in job and job["description"]:
            st.markdown("**📄 Job Description:**")
            st.text_area("", value=job["description"], height=150, key=f"desc_{job_idx}", disabled=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔗 View Job", key=f"view_{job_idx}"):
                if "url" in job and job["url"]:
                    st.markdown(f"[Open Job Posting]({job['url']})")
        
        with col2:
            if st.button("📄 Generate Documents", key=f"docs_{job_idx}"):
                st.info("Document generation feature coming soon!")
        
        with col3:
            if st.button("✅ Apply", key=f"apply_{job_idx}"):
                st.success("Application feature coming soon!")


def _display_ai_analysis_details(analysis: Dict) -> None:
    """
    Display detailed AI analysis results.
    
    Args:
        analysis: AI analysis dictionary
    """
    st.markdown("### 🤖 AI Analysis Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "skill_matches" in analysis and analysis["skill_matches"]:
            st.markdown("**✅ Matching Skills:**")
            for skill in analysis["skill_matches"][:5]:  # Show top 5
                st.markdown(f"• {skill}")
        
        if "experience_match" in analysis:
            st.markdown(f"**👨‍💼 Experience Match:** {analysis['experience_match'].title()}")
        
        if "location_match" in analysis:
            st.markdown(f"**📍 Location Match:** {analysis['location_match'].title()}")
    
    with col2:
        if "skill_gaps" in analysis and analysis["skill_gaps"]:
            st.markdown("**⚠️ Skill Gaps:**")
            for skill in analysis["skill_gaps"][:3]:  # Show top 3
                st.markdown(f"• {skill}")
        
        if "cultural_fit" in analysis:
            st.markdown(f"**🏢 Cultural Fit:** {analysis['cultural_fit']:.1%}")
        
        if "growth_potential" in analysis:
            st.markdown(f"**📈 Growth Potential:** {analysis['growth_potential']:.1%}")
    
    if "reasoning" in analysis:
        st.markdown("**💡 AI Reasoning:**")
        st.info(analysis["reasoning"])


def _display_skill_analysis(job: pd.Series) -> None:
    """
    Display skill analysis for the job.
    
    Args:
        job: Job data as pandas Series
    """
    st.markdown("### 🛠️ Skills Analysis")
    
    # Extract skills from job description
    if "description" in job and job["description"]:
        from src.core.text_utils import extract_keywords
        skills = extract_keywords(job["description"], max_keywords=10)
        
        if skills:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🔍 Detected Skills:**")
                for skill in skills[:5]:
                    st.markdown(f"• {skill}")
            
            with col2:
                if len(skills) > 5:
                    st.markdown("**More Skills:**")
                    for skill in skills[5:10]:
                        st.markdown(f"• {skill}")
            
            with col3:
                if "extracted_skills" in job and job["extracted_skills"]:
                    st.markdown("**📋 Required Skills:**")
                    for skill in job["extracted_skills"][:5]:
                        st.markdown(f"• {skill}")


def _get_score_color(score: float) -> str:
    """
    Get color for score display.
    
    Args:
        score: Score value (0.0 to 1.0)
        
    Returns:
        Color string
    """
    if score >= 0.8:
        return "#28a745"  # Green
    elif score >= 0.6:
        return "#ffc107"  # Yellow
    elif score >= 0.4:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red
