"""
Job cards component for JobQst Dashboard
Card-based view for job listings
"""
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd


def create_job_actions(job):
    """Create action buttons for a job card"""
    job_url = job.get('job_url')
    has_valid_url = (job_url and job_url != '#' and job_url != 'None')
    
    # Create Apply button with job URL if available
    if has_valid_url:
        apply_button = html.A(
            dbc.Button([
                html.I(className="fas fa-external-link-alt me-1"),
                "Apply"
            ], size="sm", color="primary"),
            href=job_url,
            target='_blank',
            style={'textDecoration': 'none'}
        )
    else:
        apply_button = dbc.Button([
            html.I(className="fas fa-paper-plane me-1"),
            "Apply"
        ], size="sm", color="secondary", disabled=True)
    
    return dbc.ButtonGroup([
        dbc.Button([
            html.I(className="fas fa-eye me-1"),
            "View"
        ], size="sm", color="outline-primary",
           id=f"view-job-{job.get('id', 0)}"),
        
        apply_button,
        
        dbc.Button([
            html.I(className="fas fa-edit me-1"),
            "Notes"
        ], size="sm", color="outline-secondary",
           id=f"notes-job-{job.get('id', 0)}")
    ], size="sm", className="w-100")


def create_job_card(job):
    """Create a job card component"""
    status_color = {
        'new': 'primary',
        'ready_to_apply': 'success',
        'applied': 'warning',
        'needs_review': 'info'
    }.get(job.get('status', 'new'), 'secondary')
    
    status_icon = {
        'new': 'fas fa-plus-circle',
        'ready_to_apply': 'fas fa-check-circle',
        'applied': 'fas fa-paper-plane',
        'needs_review': 'fas fa-eye'
    }.get(job.get('status', 'new'), 'fas fa-circle')
    
    return dbc.Card([
        dbc.CardBody([
            # Header with company and match score
            dbc.Row([
                dbc.Col([
                    html.H6(
                        job.get('company', 'Unknown Company'),
                        className="text-primary mb-1"
                    ),
                    html.H5(
                        job.get('title', 'Unknown Position'),
                        className="mb-2"
                    )
                ], width=8),
                dbc.Col([
                    dbc.Badge(
                        f"{job.get('match_score', 0):.0f}%",
                        color=("success" if job.get('match_score', 0) >= 80
                               else "warning"),
                        className="fs-6"
                    )
                ], width=4, className="text-end")
            ]),
            
            # Location and status
            html.Div([
                html.P([
                    html.I(className="fas fa-map-marker-alt me-1"),
                    job.get('location', 'Location not specified')
                ], className="mb-2 text-muted"),
                
                dbc.Badge([
                    html.I(className=f"{status_icon} me-1"),
                    job.get('status', 'new').replace('_', ' ').title()
                ], color=status_color, className="mb-3")
            ]),
            
            # Description preview (if available)
            html.Div([
                html.P(
                    job.get('description', '')[:100] +
                    ('...' if len(job.get('description', '')) > 100 else ''),
                    className="text-muted small mb-3"
                ) if job.get('description') else None
            ]),
            
            # Actions
            create_job_actions(job)
        ])
    ], className="mb-3 shadow-sm border-0 h-100 job-card")


def create_jobs_grid(jobs_data, max_cards=12):
    """Create a grid of job cards"""
    if not jobs_data:
        return dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No jobs found. Try adjusting your filters or run a new search."
        ], color="info", className="text-center")
    
    cards = []
    for job in jobs_data[:max_cards]:
        cards.append(
            dbc.Col(
                create_job_card(job),
                width=12,
                md=6,
                lg=4,
                xl=3,
                className="mb-3"
            )
        )
    
    # Add "show more" card if there are more jobs
    if len(jobs_data) > max_cards:
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-plus fs-1 " +
                                             "text-primary mb-3"),
                            html.H5(f"+{len(jobs_data) - max_cards} " +
                                    "more jobs"),
                            html.P("Adjust filters or load more results",
                                   className="text-muted"),
                            dbc.Button(
                                "Load More",
                                color="primary",
                                size="sm",
                                id="load-more-jobs-btn"
                            )
                        ], className="text-center")
                    ])
                ], className="mb-3 shadow-sm border-0 h-100 " +
                   "d-flex align-items-center justify-content-center")
            ], width=12, md=6, lg=4, xl=3, className="mb-3")
        )
    
    return dbc.Row(cards, className="jobs-grid")


def create_card_view_controls():
    """Create controls for card view"""
    return dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-th me-1"),
                    "Grid 4"
                ], size="sm", color="outline-primary", active=True,
                   id="grid-4-btn"),
                
                dbc.Button([
                    html.I(className="fas fa-th-large me-1"),
                    "Grid 3"
                ], size="sm", color="outline-primary",
                   id="grid-3-btn"),
                
                dbc.Button([
                    html.I(className="fas fa-list me-1"),
                    "List"
                ], size="sm", color="outline-primary",
                   id="list-view-btn")
            ])
        ], width=6),
        
        dbc.Col([
            dbc.InputGroup([
                dbc.Input(
                    placeholder="Cards per page...",
                    type="number",
                    value=12,
                    min=6,
                    max=50,
                    step=6,
                    id="cards-per-page-input",
                    size="sm"
                ),
                dbc.Button(
                    "Apply",
                    color="outline-secondary",
                    size="sm",
                    id="apply-cards-per-page-btn"
                )
            ], size="sm")
        ], width=6, className="text-end")
    ], className="mb-3")


def create_job_quick_stats(jobs_data):
    """Create quick stats for jobs"""
    if not jobs_data:
        return html.Div()
    
    df = pd.DataFrame(jobs_data)
    
    # Calculate stats
    total_jobs = len(df)
    avg_score = df['match_score'].mean() if 'match_score' in df.columns else 0
    top_company = (df['company'].value_counts().index[0]
                   if 'company' in df.columns and not df.empty else 'N/A')
    
    status_counts = (df['status'].value_counts()
                     if 'status' in df.columns else {})
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{total_jobs:,}", className="text-primary mb-0"),
                    html.Small("Total Jobs", className="text-muted")
                ])
            ], className="text-center shadow-sm border-0")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{avg_score:.1f}%",
                            className="text-success mb-0"),
                    html.Small("Avg Match", className="text-muted")
                ])
            ], className="text-center shadow-sm border-0")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(top_company, className="text-info mb-0"),
                    html.Small("Top Company", className="text-muted")
                ])
            ], className="text-center shadow-sm border-0")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(
                        f"{status_counts.get('ready_to_apply', 0):,}",
                        className="text-warning mb-0"
                    ),
                    html.Small("Ready to Apply", className="text-muted")
                ])
            ], className="text-center shadow-sm border-0")
        ], width=3)
    ], className="mb-4")

