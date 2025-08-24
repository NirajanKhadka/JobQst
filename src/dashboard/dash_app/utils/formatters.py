"""
Utility functions for formatting and data processing
"""
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def format_job_data_for_table(jobs_data):
    """Format job data for display in DataTable"""
    try:
        if not jobs_data:
            return []
        
        df = pd.DataFrame(jobs_data)
        
        # Format dates
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
        
        # Format match score
        if 'match_score' in df.columns:
            df['match_score'] = df['match_score'].round(0).astype(int)
        
        # Add action buttons (markdown format for DataTable)
        df['actions'] = df.apply(lambda row: 
            f"[View]({row.get('url', '#')}) | [Apply](#) | [Notes](#)", axis=1)
        
        return df.to_dict('records')
        
    except Exception as e:
        logger.error(f"Error formatting job data: {e}")
        return []

def calculate_job_metrics(jobs_data):
    """Calculate various job metrics"""
    try:
        if not jobs_data:
            return {}
        
        df = pd.DataFrame(jobs_data)
        
        metrics = {
            'total_jobs': len(df),
            'new_jobs': len(df[df['status'] == 'new']) if 'status' in df.columns else 0,
            'ready_to_apply': len(df[df['status'] == 'ready_to_apply']) if 'status' in df.columns else 0,
            'applied_jobs': len(df[df['status'] == 'applied']) if 'status' in df.columns else 0,
            'needs_review': len(df[df['status'] == 'needs_review']) if 'status' in df.columns else 0,
            'avg_match_score': df['match_score'].mean() if 'match_score' in df.columns else 0,
            'total_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'remote_jobs': len(df[df['location'].str.contains('Remote', case=False, na=False)]) if 'location' in df.columns else 0
        }
        
        # Calculate success rate
        if metrics['total_jobs'] > 0:
            metrics['success_rate'] = (metrics['applied_jobs'] / metrics['total_jobs']) * 100
        else:
            metrics['success_rate'] = 0
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return {}

def filter_jobs_data(jobs_data, filters):
    """Apply filters to jobs data"""
    try:
        if not jobs_data:
            return []
        
        df = pd.DataFrame(jobs_data)
        filtered_df = df.copy()
        
        # Apply search filter
        if filters.get('search'):
            search_term = filters['search'].lower()
            mask = (
                filtered_df['title'].str.lower().str.contains(search_term, na=False) |
                filtered_df['company'].str.lower().str.contains(search_term, na=False) |
                filtered_df['location'].str.lower().str.contains(search_term, na=False)
            )
            filtered_df = filtered_df[mask]
        
        # Apply company filter
        if filters.get('company') and filters['company'] != 'all':
            filtered_df = filtered_df[filtered_df['company'] == filters['company']]
        
        # Apply status filter
        if filters.get('status') and filters['status'] != 'all':
            filtered_df = filtered_df[filtered_df['status'] == filters['status']]
        
        # Apply date range filter
        if filters.get('start_date') and filters.get('end_date'):
            filtered_df['created_at'] = pd.to_datetime(filtered_df['created_at'])
            filtered_df = filtered_df[
                (filtered_df['created_at'] >= filters['start_date']) &
                (filtered_df['created_at'] <= filters['end_date'])
            ]
        
        # Apply match score filter
        if filters.get('min_match_score'):
            filtered_df = filtered_df[filtered_df['match_score'] >= filters['min_match_score']]
        
        return filtered_df.to_dict('records')
        
    except Exception as e:
        logger.error(f"Error filtering jobs data: {e}")
        return jobs_data

def generate_status_badge_color(status):
    """Generate appropriate color for job status badge"""
    status_colors = {
        'new': 'primary',
        'ready_to_apply': 'success',
        'applied': 'warning',
        'needs_review': 'info',
        'filtered_out': 'secondary',
        'interview': 'success',
        'rejected': 'danger',
        'offer': 'success'
    }
    return status_colors.get(status, 'secondary')

def format_currency(amount, currency='CAD'):
    """Format currency amounts"""
    try:
        if amount is None:
            return 'Not specified'
        return f"${amount:,.0f} {currency}"
    except Exception:
        return 'Invalid amount'

def format_date_relative(date_str):
    """Format date as relative time (e.g., '2 days ago')"""
    try:
        date = pd.to_datetime(date_str)
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            return 'Today'
        elif diff.days == 1:
            return 'Yesterday'
        elif diff.days < 7:
            return f'{diff.days} days ago'
        elif diff.days < 30:
            weeks = diff.days // 7
            return f'{weeks} week{"s" if weeks > 1 else ""} ago'
        elif diff.days < 365:
            months = diff.days // 30
            return f'{months} month{"s" if months > 1 else ""} ago'
        else:
            years = diff.days // 365
            return f'{years} year{"s" if years > 1 else ""} ago'
            
    except Exception:
        return date_str

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + '...'

def sanitize_filename(filename):
    """Sanitize filename for safe export"""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename.strip()

def export_jobs_to_csv(jobs_data, filename=None):
    """Export jobs data to CSV format"""
    try:
        if not jobs_data:
            return None
        
        df = pd.DataFrame(jobs_data)
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'jobs_export_{timestamp}.csv'
        
        # Clean up data for export
        export_df = df.copy()
        
        # Remove any action columns
        if 'actions' in export_df.columns:
            export_df = export_df.drop('actions', axis=1)
        
        # Format dates
        date_columns = ['created_at', 'updated_at', 'scraped_at']
        for col in date_columns:
            if col in export_df.columns:
                export_df[col] = pd.to_datetime(export_df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return export_df.to_csv(index=False)
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return None