"""
Enhanced Charts Utility with Caching Support
Provides cached chart generation for improved dashboard performance
"""
import logging
import pandas as pd
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# Import caching
try:
    from ..services.cache_service import cached_operation
    CACHING_AVAILABLE = True
except ImportError:
    logger.warning("Caching not available for charts")
    CACHING_AVAILABLE = False
    
    # Dummy decorator if caching not available
    def cached_operation(cache_key_func=None, ttl=300):
        def decorator(func):
            return func
        return decorator


def create_empty_chart(message: str = "No data available"):
    """Create empty chart with message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        font=dict(size=16, color="gray"),
        showarrow=False
    )
    fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        template='plotly_white',
        height=400
    )
    return fig


def company_cache_key(*args, **kwargs):
    """Generate cache key for company charts"""
    profile_name = kwargs.get('profile_name', 'default')
    top_n = kwargs.get('top_n', 15)
    data_hash = kwargs.get('data_hash', 'no_data')
    return f"company_chart_{profile_name}_{top_n}_{data_hash}"


def location_cache_key(*args, **kwargs):
    """Generate cache key for location charts"""
    profile_name = kwargs.get('profile_name', 'default')
    top_n = kwargs.get('top_n', 10)
    data_hash = kwargs.get('data_hash', 'no_data')
    return f"location_chart_{profile_name}_{top_n}_{data_hash}"


@cached_operation(cache_key_func=company_cache_key, ttl=300)
def create_cached_company_chart(
    jobs_data: List[Dict],
    profile_name: str = 'default',
    top_n: int = 15,
    data_hash: str = None
) -> go.Figure:
    """Create cached company distribution chart"""
    try:
        if not jobs_data:
            return create_empty_chart("No job data available")
        
        df = pd.DataFrame(jobs_data)
        
        if 'company' not in df.columns:
            return create_empty_chart("Company data not available")
        
        company_counts = df['company'].value_counts().head(top_n)
        
        fig = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            title=f'Top {top_n} Companies by Job Count',
            labels={'x': 'Number of Jobs', 'y': 'Company'},
            color=company_counts.values,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating company chart: {e}")
        return create_empty_chart("Error creating chart")


@cached_operation(cache_key_func=location_cache_key, ttl=300)
def create_cached_location_chart(
    jobs_data: List[Dict],
    profile_name: str = 'default',
    top_n: int = 10,
    data_hash: str = None
) -> go.Figure:
    """Create cached location distribution chart"""
    try:
        if not jobs_data:
            return create_empty_chart("No job data available")
        
        df = pd.DataFrame(jobs_data)
        
        if 'location' not in df.columns:
            return create_empty_chart("Location data not available")
        
        # Clean up location data
        df['location_clean'] = df['location'].str.strip()
        location_counts = df['location_clean'].value_counts().head(top_n)
        
        fig = px.bar(
            x=location_counts.index,
            y=location_counts.values,
            title=f'Top {top_n} Locations by Job Count',
            labels={'x': 'Location', 'y': 'Number of Jobs'},
            color=location_counts.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            xaxis={'tickangle': 45}
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating location chart: {e}")
        return create_empty_chart("Error creating chart")


def create_score_distribution_chart(
    score_data: Dict[str, Any],
    profile_name: str = 'default'
) -> go.Figure:
    """Create match score distribution chart"""
    try:
        ranges = score_data.get('ranges', [])
        counts = score_data.get('counts', [])
        
        if not ranges or not counts:
            return create_empty_chart("No score data available")
        
        fig = px.pie(
            values=counts,
            names=ranges,
            title='Match Score Distribution',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            margin=dict(t=40, b=40, l=40, r=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating score distribution chart: {e}")
        return create_empty_chart("Error creating chart")


def create_status_overview_chart(
    status_data: Dict[str, int],
    profile_name: str = 'default'
) -> go.Figure:
    """Create job status overview chart"""
    try:
        if not status_data:
            return create_empty_chart("No status data available")
        
        statuses = list(status_data.keys())
        counts = list(status_data.values())
        
        # Color mapping for statuses
        color_map = {
            'new': '#3498db',           # Blue
            'ready_to_apply': '#2ecc71',  # Green  
            'applied': '#f39c12',       # Orange
            'needs_review': '#e74c3c',  # Red
            'rejected': '#95a5a6',      # Gray
            'interview': '#9b59b6'      # Purple
        }
        
        colors = [color_map.get(status, '#34495e') for status in statuses]
        
        fig = go.Figure(data=[
            go.Bar(
                x=statuses,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Job Status Overview',
            xaxis_title='Status',
            yaxis_title='Number of Jobs',
            template='plotly_white',
            height=400,
            margin=dict(t=40, b=40, l=40, r=40)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating status overview chart: {e}")
        return create_empty_chart("Error creating chart")


def generate_data_hash(jobs_data: List[Dict]) -> str:
    """Generate a hash of the data for cache invalidation"""
    import hashlib
    
    if not jobs_data:
        return "empty_data"
    
    # Create a simple hash based on data size and first/last job IDs
    data_signature = f"{len(jobs_data)}"
    
    if jobs_data:
        first_job = jobs_data[0]
        last_job = jobs_data[-1]
        data_signature += f"_{first_job.get('id', 'no_id')}"
        data_signature += f"_{last_job.get('id', 'no_id')}"
    
    return hashlib.md5(data_signature.encode()).hexdigest()[:8]
