"""
Charts component for the AutoJobAgent Dashboard.

This module provides chart and visualization functionality for job data analysis,
including status distribution, experience levels, match scores, and timeline charts.
"""

from typing import Optional, Dict, Any, List
import streamlit as st
import pandas as pd

# Optional plotly import with fallback
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly not available. Install with: pip install plotly")


def render_charts(df: pd.DataFrame, chart_config: Optional[Dict[str, Any]] = None) -> None:
    """
    Render analytics charts for job data.
    
    Args:
        df: DataFrame containing job data
        chart_config: Optional configuration for chart customization
        
    Returns:
        None: Renders charts directly to Streamlit
        
    Note:
        Gracefully handles missing plotly dependency and missing data columns.
    """
    st.subheader("📈 Analytics")
    
    if df.empty:
        st.info("No job data available for charts")
        return
    
    if not PLOTLY_AVAILABLE:
        _render_fallback_charts(df)
        return
    
    # Create tabs for different chart types
    tab1, tab2, tab3, tab4 = st.tabs(["Job Status", "Experience Levels", "Match Scores", "Timeline"])
    
    with tab1:
        _render_status_chart(df, chart_config)
    
    with tab2:
        _render_experience_chart(df, chart_config)
    
    with tab3:
        _render_match_score_chart(df, chart_config)
    
    with tab4:
        _render_timeline_chart(df, chart_config)


def _render_status_chart(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Render job status distribution pie chart.
    
    Args:
        df: DataFrame containing job data
        config: Optional chart configuration
    """
    if 'status' not in df.columns:
        st.info("No status data available for chart")
        return
    
    try:
        status_counts = df['status'].value_counts()
        if status_counts.empty:
            st.info("No status data to display")
            return
        
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index, 
            title="Job Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering status chart: {str(e)}")


def _render_experience_chart(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Render experience level distribution bar chart.
    
    Args:
        df: DataFrame containing job data
        config: Optional chart configuration
    """
    if 'experience_level' not in df.columns:
        st.info("No experience level data available for chart")
        return
    
    try:
        exp_counts = df['experience_level'].value_counts()
        if exp_counts.empty:
            st.info("No experience level data to display")
            return
        
        fig = px.bar(
            x=exp_counts.index, 
            y=exp_counts.values, 
            title="Jobs by Experience Level",
            labels={'x': 'Experience Level', 'y': 'Number of Jobs'},
            color=exp_counts.values,
            color_continuous_scale='viridis'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering experience chart: {str(e)}")


def _render_match_score_chart(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Render match score distribution histogram.
    
    Args:
        df: DataFrame containing job data
        config: Optional chart configuration
    """
    if 'match_score' not in df.columns:
        st.info("No match score data available for chart")
        return
    
    try:
        # Convert to numeric and filter out invalid values
        numeric_scores = pd.to_numeric(df['match_score'], errors='coerce').dropna()
        
        if numeric_scores.empty:
            st.info("No valid match score data to display")
            return
        
        fig = px.histogram(
            x=numeric_scores, 
            nbins=20, 
            title="Match Score Distribution",
            labels={'x': 'Match Score (%)', 'y': 'Number of Jobs'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering match score chart: {str(e)}")


def _render_timeline_chart(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Render jobs created over time line chart.
    
    Args:
        df: DataFrame containing job data
        config: Optional chart configuration
    """
    if 'created_at' not in df.columns:
        st.info("No timeline data available for chart")
        return
    
    try:
        # Convert to datetime and handle errors
        df_copy = df.copy()
        df_copy['created_at'] = pd.to_datetime(df_copy['created_at'], errors='coerce')
        df_copy = df_copy.dropna(subset=['created_at'])
        
        if df_copy.empty:
            st.info("No valid date data to display")
            return
        
        # Group by date
        timeline_data = df_copy.groupby(df_copy['created_at'].dt.date).size().reset_index()
        timeline_data.columns = ['date', 'count']
        
        if timeline_data.empty:
            st.info("No timeline data to display")
            return
        
        fig = px.line(
            timeline_data, 
            x='date', 
            y='count', 
            title="Jobs Created Over Time", 
            markers=True,
            labels={'date': 'Date', 'count': 'Number of Jobs'}
        )
        fig.update_traces(line_color='#2E86AB', marker_color='#A23B72')
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering timeline chart: {str(e)}")


def _render_fallback_charts(df: pd.DataFrame) -> None:
    """
    Render simple text-based charts when Plotly is not available.
    
    Args:
        df: DataFrame containing job data
    """
    st.info("Using simplified charts (install plotly for enhanced visualizations)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'status' in df.columns:
            st.subheader("Job Status")
            status_counts = df['status'].value_counts()
            for status, count in status_counts.items():
                st.text(f"{status}: {count}")
    
    with col2:
        if 'experience_level' in df.columns:
            st.subheader("Experience Levels")
            exp_counts = df['experience_level'].value_counts()
            for level, count in exp_counts.items():
                st.text(f"{level}: {count}")


def get_chart_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary information about available chart data.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary containing data availability summary
    """
    summary = {
        "has_status": 'status' in df.columns and not df['status'].isna().all(),
        "has_experience": 'experience_level' in df.columns and not df['experience_level'].isna().all(),
        "has_match_score": 'match_score' in df.columns and not df['match_score'].isna().all(),
        "has_timeline": 'created_at' in df.columns and not df['created_at'].isna().all(),
        "total_rows": len(df),
        "plotly_available": PLOTLY_AVAILABLE
    }
    return summary
