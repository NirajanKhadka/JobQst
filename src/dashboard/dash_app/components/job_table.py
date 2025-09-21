"""
Job table component for JobQst Dashboard
Interactive DataTable for job management
"""
import dash_bootstrap_components as dbc
from dash import html, dash_table
import pandas as pd


def create_jobs_table(data=None):
    """Create an interactive jobs DataTable"""
    
    if data is None:
        data = []
    
    # Define table columns - including salary column prominently
    columns = [
        {
            'name': 'Title',
            'id': 'title',
            'type': 'text',
            'presentation': 'markdown'
        },
        {
            'name': 'Company',
            'id': 'company',
            'type': 'text'
        },
        {
            'name': 'Location',
            'id': 'location',
            'type': 'text'
        },
        {
            'name': '💰 Salary',
            'id': 'salary',
            'type': 'text'
        },
        {
            'name': 'Status',
            'id': 'status',
            'type': 'text',
            'presentation': 'dropdown'
        },
        {
            'name': 'Match Score',
            'id': 'match_score',
            'type': 'numeric',
            'format': {'specifier': '.0f'}
        },
        {
            'name': '🔑 Keywords',
            'id': 'keywords',
            'type': 'text'
        },
        {
            'name': '🇨🇦 RCIP',
            'id': 'rcip_indicator',
            'type': 'text'
        },
        {
            'name': '⭐ Priority',
            'id': 'immigration_priority',
            'type': 'text'
        },
        {
            'name': 'AI Confidence',
            'id': 'confidence_badge',
            'type': 'text',
            'presentation': 'markdown'
        },
        {
            'name': 'Semantic Score',
            'id': 'semantic_score',
            'type': 'numeric',
            'format': {'specifier': '.2f'}
        },
        {
            'name': 'Validation Method',
            'id': 'validation_method',
            'type': 'text'
        },
        {
            'name': 'Posted Date',
            'id': 'posted_date',
            'type': 'text'
        },
        {
            'name': 'Actions',
            'id': 'actions',
            'type': 'text',
            'presentation': 'markdown'
        }
    ]
    
    return dash_table.DataTable(
        id='jobs-table',
        columns=columns,
        data=data,
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=25,
        style_table={
            'backgroundColor': '#1e1e1e',
            'color': 'white',
            'borderRadius': '12px',
            'overflow': 'hidden',
            'boxShadow': '0 8px 32px rgba(0,0,0,0.3)',
            'border': '1px solid #333'
        },
        style_cell={
            'backgroundColor': '#2d2d2d',
            'color': 'white',
            'textAlign': 'left',
            'padding': '12px',
            'border': '1px solid #444',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#0d6efd',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'padding': '16px',
            'border': '1px solid #0d6efd',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '14px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#262626'
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#0d6efd',
                'border': '1px solid #0d6efd'
            },
            {
                'if': {'column_id': 'match_score',
                       'filter_query': '{match_score} >= 80'},
                'backgroundColor': '#198754',
                'color': 'white',
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': 'match_score',
                       'filter_query': '{match_score} >= 60 && {match_score} < 80'},
                'backgroundColor': '#fd7e14',
                'color': 'white'
            },
            {
                'if': {'column_id': 'match_score',
                       'filter_query': '{match_score} < 60'},
                'backgroundColor': '#dc3545',
                'color': 'white'
            }
        ],
        style_cell_conditional=[
            {
                'if': {'column_id': 'title'},
                'textAlign': 'left',
                'minWidth': '200px',
                'width': '200px',
                'maxWidth': '200px',
            },
            {
                'if': {'column_id': 'company'},
                'textAlign': 'left',
                'minWidth': '150px',
                'width': '150px',
                'maxWidth': '150px',
            },
            {
                'if': {'column_id': 'salary'},
                'textAlign': 'center',
                'minWidth': '120px',
                'width': '120px',
                'maxWidth': '120px',
                'fontWeight': 'bold',
                'color': '#20c997'
            },
            {
                'if': {'column_id': 'actions'},
                'textAlign': 'center',
                'minWidth': '180px',
                'width': '180px',
                'maxWidth': '180px',
            }
        ],
        tooltip_data=[
            {
                column: {'value': str(value)[:100] + '...' if len(str(value)) > 100 else str(value),
                         'type': 'markdown'}
                for column, value in row.items()
                if column in ['title', 'company', 'location', 'status']
            } for row in data
        ],
        tooltip_duration=3000
    )


def create_table_controls():
    """Create modern table control buttons"""
    return dbc.ButtonGroup([
        dbc.Button([
            html.I(className="fas fa-table me-2"),
            "Table View"
        ], id="table-view-btn", color="primary", size="sm", active=True,
           className="fw-bold"),
        
        dbc.Button([
            html.I(className="fas fa-th-large me-2"),
            "Card View"
        ], id="card-view-btn", color="outline-primary", size="sm",
           className="fw-bold"),
        
        dbc.Button([
            html.I(className="fas fa-download me-2"),
            "Export"
        ], id="export-jobs-btn", color="outline-success", size="sm",
           className="fw-bold"),
        
        dbc.Button([
            html.I(className="fas fa-filter me-2"),
            "Advanced Filter"
        ], id="advanced-filter-btn", color="outline-info", size="sm",
           className="fw-bold")
    ], className="mb-3")


def format_job_data_for_table(df):
    """Format job DataFrame for display in DataTable"""
    if df.empty:
        return []
    
    # Create a copy to avoid modifying the original
    display_df = df.copy()
    
    # Ensure required columns exist
    required_columns = ['id', 'title', 'company', 'location', 'status',
                        'salary', 'match_score', 'posted_date', 'job_url']
    
    for col in required_columns:
        if col not in display_df.columns:
            if col == 'id':
                display_df[col] = range(len(display_df))
            elif col == 'salary':
                display_df[col] = 'Not specified'
            elif col == 'match_score':
                display_df[col] = 0
            elif col == 'job_url':
                display_df[col] = '#'
            else:
                display_df[col] = 'Unknown'
    
    # Format dates
    if 'created_at' in display_df.columns:
        display_df['posted_date'] = pd.to_datetime(
            display_df['created_at']
        ).dt.strftime('%Y-%m-%d')
    elif 'posted_date' not in display_df.columns:
        display_df['posted_date'] = 'Unknown'
    
    # Format salary for display with better formatting
    if 'salary_display' in display_df.columns:
        display_df['salary'] = display_df['salary_display']
    elif 'salary' in display_df.columns:
        def format_salary(salary_value):
            if pd.isna(salary_value) or salary_value == '' or salary_value == 'None':
                return '💼 Not specified'
            return f'💰 {str(salary_value)}'
        
        display_df['salary'] = display_df['salary'].apply(format_salary)
    else:
        display_df['salary'] = '💼 Not specified'
    
    # Format status for display
    if 'status' in display_df.columns:
        status_map = {
            'new': '🆕 New',
            'ready_to_apply': '✅ Ready to Apply',
            'applied': '📤 Applied',
            'needs_review': '🔍 Needs Review',
            'rejected': '❌ Rejected',
            'archived': '📁 Archived'
        }
        display_df['status'] = display_df['status'].map(
            status_map
        ).fillna(display_df['status'])
    
    # Format confidence scores
    if 'confidence_score' in display_df.columns:
        def format_confidence_badge(score):
            if pd.isna(score):
                return '❓ Unknown'
            elif score >= 0.8:
                return '🟢 HIGH'
            elif score >= 0.6:
                return '🟡 MEDIUM'
            elif score >= 0.4:
                return '🟠 LOW'
            else:
                return '🔴 POOR'
        
        display_df['confidence_badge'] = display_df['confidence_score'].apply(
            format_confidence_badge
        )
    elif 'quality_score' in display_df.columns:
        # Fallback to quality_score if confidence_score not available
        def format_quality_badge(score):
            if pd.isna(score):
                return '❓ Unknown'
            elif score >= 0.8:
                return '🟢 HIGH'
            elif score >= 0.6:
                return '🟡 MEDIUM'
            elif score >= 0.4:
                return '🟠 LOW'
            else:
                return '🔴 POOR'
        
        display_df['confidence_badge'] = display_df['quality_score'].apply(
            format_quality_badge
        )
    else:
        # Default if no confidence data available
        display_df['confidence_badge'] = '❓ Unknown'
    
    # Format semantic scores
    if 'semantic_score' not in display_df.columns:
        display_df['semantic_score'] = 0.0
    
    # Format validation methods
    if 'validation_method' not in display_df.columns:
        display_df['validation_method'] = 'standard'
    
    # Add validation method icons
    def format_validation_method(method):
        if pd.isna(method) or method == 'standard':
            return '📋 Standard'
        elif method == 'ai_semantic':
            return '🤖 AI Semantic'
        elif method == 'exact_match':
            return '✅ Exact Match'
        elif method == 'partial_matching':
            return '🔍 Partial'
        else:
            return f'❓ {method}'
    
    display_df['validation_method'] = display_df['validation_method'].apply(
        format_validation_method
    )
    
    # Add enhanced action buttons with proper HTML
    if 'actions' not in display_df.columns:
        def create_action_buttons(row):
            job_url = row.get('job_url', '#')
            title = row.get('title', 'Unknown Job')
            company = row.get('company', 'Unknown Company')
            salary = row.get('salary', 'Not specified')
            description = row.get('description', 'No description available')
            job_id = row.get('id', 'unknown')
            
            # Create clickable links that open in new tabs
            if job_url and job_url != '#' and job_url != 'None':
                view_btn = (f'<a href="{job_url}" target="_blank" '
                          f'rel="noopener noreferrer" '
                          f'class="btn btn-sm btn-primary text-decoration-none">'
                          f'👁️ View</a>')
            else:
                view_btn = ('<span class="btn btn-sm btn-secondary disabled">'
                          '👁️ View</span>')
            
            # Create summary tooltip with rich job details
            safe_title = str(title).replace('"', "'").replace('\n', ' ')[:100]
            safe_company = str(company).replace('"', "'").replace('\n', ' ')[:50]
            safe_salary = str(salary).replace('"', "'").replace('\n', ' ')
            safe_desc = str(description).replace('"', "'").replace('\n', ' ')[:200]
            
            summary_text = (f"Title: {safe_title} | "
                          f"Company: {safe_company} | "
                          f"Salary: {safe_salary} | "
                          f"Description: {safe_desc}...")
            
            summary_btn = (f'<button class="btn btn-sm btn-info job-summary-btn" '
                         f'data-job-id="{job_id}" '
                         f'title="{summary_text}" '
                         f'style="cursor: pointer;">'
                         f'📋 Summary</button>')
            
            return f'{view_btn} {summary_btn}'
        
        display_df['actions'] = display_df.apply(create_action_buttons, axis=1)
    
    # Limit long text fields for better display
    text_columns = ['title', 'company', 'location']
    for col in text_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].astype(str).str.slice(0, 50)
    
    return display_df.to_dict('records')

