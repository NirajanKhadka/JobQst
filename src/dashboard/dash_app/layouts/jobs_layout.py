"""
Jobs layout for JobQst Dashboard
Modern job management interface with DataTable and cards
"""
import dash_bootstrap_components as dbc  # already imported; keep single
from dash import html, dcc, dash_table

from ..components.navigation import create_page_header
from ..components.job_table import create_jobs_table, create_table_controls
from ..components.job_cards import create_jobs_grid, create_job_quick_stats
from ..components.job_modal import (
    create_job_modal,
    create_job_notes_storage,
    create_job_modal_store
)
from dash import dcc
import dash_bootstrap_components as dbc


def create_job_tracking_tabs():
    """Create tabbed interface for tracking jobs by status"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Tabs([
                dbc.Tab(label="📊 All Jobs", tab_id="all"),
                dbc.Tab(label="🔍 Scraped", tab_id="scraped"),
                dbc.Tab(label="⚙️ Processed", tab_id="processed"),
                dbc.Tab(label="✅ Applied", tab_id="applied"),
            ], id="job-status-tabs", active_tab="all")
        ]),
        dbc.CardBody(id="job-tracking-content")
    ], className="mb-4")


def create_jobs_layout():
    """Create the jobs management layout"""
    return html.Div([
        create_jobs_header(),
        create_jobs_metrics_row(),
        create_jobs_filters_section(),
        create_job_tracking_tabs(),
        create_jobs_table_section(),
        
        # Modal and storage components
        create_job_modal(),
        create_job_notes_storage(),
        create_job_modal_store()
    ])


def _create_notes_modal():
    """Lightweight modal specifically for quick notes editing."""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Job Notes")),
        dbc.ModalBody([
            html.Div(id='notes-modal-job-title', className='fw-bold mb-2'),
            dcc.Textarea(
                id='notes-modal-text',
                style={'width': '100%', 'height': 180}
            ),
            html.Small(
                "Notes are saved automatically when you close this modal.",
                className='text-muted'
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id='notes-modal-close', color='secondary')
        ])
    ], size="sm", className="mt-3")


def create_jobs_header():
    """Create the jobs page header with actions"""
    header_actions = dbc.ButtonGroup([
        dbc.Button([
            html.I(className="fas fa-plus me-1"),
            "Add Job"
        ], color="primary", size="sm"),
        
        dbc.Button([
            html.I(className="fas fa-download me-1"),
            "Export"
        ], color="outline-secondary", size="sm"),
        
        dbc.Button([
            html.I(className="fas fa-sync me-1"),
            "Refresh"
        ], color="outline-secondary", size="sm", id="jobs-refresh-btn")
    ])
    
    return create_page_header(
        "💼 Job Management",
        "Manage and track your job applications",
        header_actions
    )


def create_jobs_metrics_row():
    """Create the metrics cards row"""
    return dbc.Row([
        dbc.Col([
            create_metric_card(
                "Total Jobs", "0", "fas fa-briefcase", "primary",
                "total-jobs-metric"
            )
        ], width=3),
        dbc.Col([
            create_metric_card(
                "New Jobs", "0", "fas fa-plus-circle", "info",
                "new-jobs-metric"
            )
        ], width=3),
        dbc.Col([
            create_metric_card(
                "Ready to Apply", "0", "fas fa-paper-plane", "success",
                "ready-jobs-metric"
            )
        ], width=3),
        dbc.Col([
            create_metric_card(
                "Applied", "0", "fas fa-check-circle", "warning",
                "applied-jobs-metric"
            )
        ], width=3)
    ], className="mb-4")


def create_jobs_filters_section():
    """Create enhanced filters section for practical job search"""
    return dbc.Card([
        dbc.CardBody([
            # Row 1: Basic Search and Status
            dbc.Row([
                dbc.Col([
                    html.Label("🔍 Search", className="fw-semibold"),
                    dbc.Input(
                        id="jobs-search",
                        placeholder="Search jobs, companies, or skills...",
                        type="text"
                    )
                ], width=4),
                
                dbc.Col([
                    html.Label("📊 Status", className="fw-semibold"),
                    dcc.Dropdown(
                        id="jobs-status-filter",
                        placeholder="All Statuses",
                        options=[
                            {'label': 'All', 'value': 'all'},
                            {'label': '🆕 New', 'value': 'new'},
                            {'label': '✅ Ready to Apply',
                             'value': 'ready_to_apply'},
                            {'label': '📤 Applied', 'value': 'applied'},
                            {'label': '👀 Needs Review',
                             'value': 'needs_review'},
                            {'label': '❌ Rejected', 'value': 'rejected'}
                        ],
                        value='all'
                    )
                ], width=3),
                
                dbc.Col([
                    html.Label("🏢 Company", className="fw-semibold"),
                    dcc.Dropdown(
                        id="jobs-company-filter",
                        placeholder="All Companies",
                        options=[],
                        value=None
                    )
                ], width=3),
                
                dbc.Col([
                    html.Label("� Date Range", className="fw-semibold"),
                    dcc.DatePickerRange(
                        id="jobs-date-filter",
                        display_format="MMM DD, YYYY",
                        style={'width': '100%'}
                    )
                ], width=2)
            ], className="mb-3"),
            
            # Row 2: Salary, Work Type, and Experience
            dbc.Row([
                dbc.Col([
                    html.Label("💰 Salary Range", className="fw-semibold"),
                    dcc.RangeSlider(
                        id="salary-range-slider",
                        min=30000,
                        max=200000,
                        step=5000,
                        value=[40000, 150000],
                        marks={
                            30000: "$30K",
                            60000: "$60K",
                            100000: "$100K",
                            150000: "$150K",
                            200000: "$200K+"
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=4),
                
                dbc.Col([
                    html.Label("🏠 Work Type", className="fw-semibold"),
                    dcc.Dropdown(
                        id="work-type-filter",
                        options=[
                            {"label": "All Types", "value": "all"},
                            {"label": "🏠 Remote", "value": "remote"},
                            {"label": "🔄 Hybrid", "value": "hybrid"},
                            {"label": "🏢 On-site", "value": "onsite"}
                        ],
                        value="all",
                        clearable=False
                    )
                ], width=2),
                
                dbc.Col([
                    html.Label("📈 Experience", className="fw-semibold"),
                    dcc.Dropdown(
                        id="experience-filter",
                        options=[
                            {"label": "All Levels", "value": "all"},
                            {"label": "Entry", "value": "entry"},
                            {"label": "Mid", "value": "mid"},
                            {"label": "Senior", "value": "senior"},
                            {"label": "Lead", "value": "lead"}
                        ],
                        value="all",
                        clearable=False
                    )
                ], width=2),
                
                dbc.Col([
                    html.Label("🎯 Match Score", className="fw-semibold"),
                    dcc.RangeSlider(
                        id="match-score-slider",
                        min=0,
                        max=100,
                        step=10,
                        value=[60, 100],
                        marks={
                            0: "0%",
                            50: "50%",
                            100: "100%"
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=4)
            ], className="mb-3"),
            
            # Row 3: Action Buttons and User Feedback
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Apply Filters", color="primary", size="sm",
                                   id="apply-filters-btn"),
                        dbc.Button("Clear All", color="outline-secondary",
                                   size="sm", id="clear-filters-btn"),
                        dbc.Button("Save Search", color="outline-info",
                                   size="sm", id="save-search-btn")
                    ])
                ], width="auto"),
                
                dbc.Col([
                    html.Div([
                        html.Small("Quick Filters: ",
                                   className="text-muted me-2"),
                        dbc.Badge("Remote Only", color="info",
                                  className="me-1",
                                  id="quick-remote-filter"),
                        dbc.Badge("High Match", color="success",
                                  className="me-1",
                                  id="quick-high-match-filter"),
                        dbc.Badge("New Jobs", color="primary",
                                  className="me-1",
                                  id="quick-new-jobs-filter")
                    ])
                ], width="auto", className="ms-auto")
            ])
        ])
    ], className="mb-4")


def create_jobs_table_section():
    """Create the table section with view toggle"""
    return dbc.Card([
        dbc.CardHeader([
            create_table_header()
        ]),
        dbc.CardBody([
            create_table_view(),
            create_card_view()
        ])
    ])


def create_table_header():
    """Create the table header with view toggle"""
    return dbc.Row([
        dbc.Col([
            html.H5("📋 Job Listings", className="mb-0")
        ], width="auto"),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-table me-1"),
                    "Table"
                ], color="primary", size="sm", id="table-view-btn",
                   active=True),
                dbc.Button([
                    html.I(className="fas fa-th-large me-1"),
                    "Cards"
                ], color="outline-primary", size="sm", id="card-view-btn")
            ])
        ], width="auto", className="ms-auto")
    ], className="align-items-center")


def create_table_view():
    """Create the table view component"""
    return html.Div([
        dash_table.DataTable(
            id='jobs-table',
            columns=[
                {'name': 'Title', 'id': 'title', 'type': 'text'},
                {'name': 'Company', 'id': 'company', 'type': 'text'},
                {'name': 'Location', 'id': 'location', 'type': 'text'},
                {'name': '💰 Salary', 'id': 'salary', 'type': 'text'},
                {'name': 'Status', 'id': 'status', 'type': 'text'},
                {
                    'name': 'Match Score',
                    'id': 'match_score',
                    'type': 'numeric',
                    'format': {'specifier': '.0f'}
                },
                {'name': 'Date', 'id': 'created_at', 'type': 'datetime'},
                {
                    'name': 'View Job',
                    'id': 'view_job',
                    'presentation': 'markdown'
                }
            ],
            data=[],
            sort_action="native",
            filter_action="native",
            page_action="native",
            page_current=0,
            page_size=25,
            markdown_options={'link_target': '_blank'},
            style_cell=get_table_cell_style(),
            style_header=get_table_header_style(),
            style_data_conditional=get_table_conditional_styles(),
            css=[{
                'selector': '.dash-table-container',
                'rule': 'border-radius: 8px; overflow: hidden;'
            }]
        )
    ], id="table-view", style={'display': 'block'})


def create_card_view():
    """Create the card view component"""
    return html.Div([
        html.Div(id="jobs-cards-container")
    ], id="card-view", style={'display': 'none'})


def get_table_cell_style():
    """Get table cell styling"""
    return {
        'textAlign': 'left',
        'padding': '12px',
        'fontFamily': 'Inter, sans-serif'
    }


def get_table_header_style():
    """Get table header styling"""
    return {
        'backgroundColor': '#f8f9fa',
        'fontWeight': 'bold',
        'borderBottom': '2px solid #dee2e6'
    }


def get_table_conditional_styles():
    """Get table conditional styling"""
    return [
        {
            'if': {'filter_query': '{status} = new'},
            'backgroundColor': '#e3f2fd',
            'color': 'black',
        },
        {
            'if': {'filter_query': '{status} = ready_to_apply'},
            'backgroundColor': '#e8f5e8',
            'color': 'black',
        },
        {
            'if': {'filter_query': '{status} = applied'},
            'backgroundColor': '#fff3cd',
            'color': 'black',
        }
    ]


def create_metric_card(title, value, icon, color, metric_id):
    """Create a metric card component"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(
                        id=metric_id,
                        children=value,
                        className="fw-bold mb-1"
                    ),
                    html.P(title, className="text-muted mb-0 small")
                ], width=8),
                dbc.Col([
                    html.I(className=f"{icon} fs-2 text-{color}")
                ], width=4, className="text-end")
            ], className="align-items-center")
        ])
    ], className="shadow-sm border-0")


def create_job_card(job):
    """Create a job card component"""
    status_color = {
        'new': 'primary',
        'ready_to_apply': 'success',
        'applied': 'warning',
        'needs_review': 'info'
    }.get(job.get('status', 'new'), 'secondary')
    
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
                        color=(
                            "success"
                            if job.get('match_score', 0) >= 80
                            else "warning"
                        ),
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
                
                dbc.Badge(
                    job.get('status', 'new').replace('_', ' ').title(),
                    color=status_color,
                    className="mb-3"
                )
            ]),
            
            # Actions
            dbc.ButtonGroup([
                dbc.Button("👀 View", size="sm", color="outline-primary"),
                dbc.Button("✅ Apply", size="sm", color="primary"),
                dbc.Button("📝 Notes", size="sm", color="outline-secondary")
            ], size="sm", className="w-100")
        ])
    ], className="mb-3 shadow-sm border-0 h-100")

