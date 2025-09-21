"""
Enhanced Job Tracker Layout - Modern UX for JobLens
Comprehensive job application tracking with Kanban board, notes, and timeline
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime, timedelta


def create_job_tracker_header():
    """Create modern header for job tracker with quick stats"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H2([
                            html.I(className="fas fa-clipboard-list me-3 text-primary"),
                            "Job Application Tracker"
                        ], className="fw-bold mb-0"),
                        html.P("Manage your job applications with AI-powered insights",
                               className="text-muted mb-0")
                    ])
                ], md=8),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-plus me-2"),
                            "Add Application"
                        ], color="primary", id="add-application-btn", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-filter me-2"),
                            "Filter"
                        ], color="outline-secondary", id="filter-toggle-btn", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-download me-2"),
                            "Export"
                        ], color="outline-info", id="export-btn", size="sm")
                    ], className="d-flex")
                ], md=4, className="d-flex justify-content-end align-items-center")
            ])
        ])
    ], className="mb-4 shadow-sm border-0")


def create_quick_stats_cards():
    """Create quick stats cards for job tracking overview"""
    stats_cards = []
    
    stats_data = [
        {
            "title": "Total Applications", 
            "value": "0", 
            "icon": "fas fa-paper-plane", 
            "color": "primary",
            "id": "total-applications-stat"
        },
        {
            "title": "Active Interviews", 
            "value": "0", 
            "icon": "fas fa-calendar-alt", 
            "color": "success",
            "id": "active-interviews-stat"
        },
        {
            "title": "Pending Responses", 
            "value": "0", 
            "icon": "fas fa-clock", 
            "color": "warning",
            "id": "pending-responses-stat"
        },
        {
            "title": "Success Rate", 
            "value": "0%", 
            "icon": "fas fa-chart-line", 
            "color": "info",
            "id": "success-rate-stat"
        }
    ]
    
    for stat in stats_data:
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.I(className=f"{stat['icon']} fa-2x text-{stat['color']}")
                        ], width=3, className="d-flex align-items-center justify-content-center"),
                        dbc.Col([
                            html.H4(stat['value'], className="fw-bold mb-0", 
                                   id=stat['id']),
                            html.P(stat['title'], className="text-muted small mb-0")
                        ], width=9)
                    ])
                ])
            ], className="h-100 shadow-sm border-0 hover-shadow")
        ], md=3, className="mb-3")
        stats_cards.append(card)
    
    return dbc.Row(stats_cards)


def create_kanban_board():
    """Create Kanban board for application pipeline"""
    columns = [
        {"title": "Discovered", "status": "discovered", "color": "secondary"},
        {"title": "Interested", "status": "interested", "color": "info"},
        {"title": "Applied", "status": "applied", "color": "primary"},
        {"title": "Interviewing", "status": "interviewing", "color": "warning"},
        {"title": "Offer", "status": "offer", "color": "success"},
        {"title": "Closed", "status": "closed", "color": "danger"}
    ]
    
    kanban_columns = []
    
    for col in columns:
        column = dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H6([
                                html.I(className="fas fa-circle me-2", 
                                      style={"color": f"var(--bs-{col['color']})"} if col['color'] != 'secondary' else {"color": "#6c757d"}),
                                col['title']
                            ], className="mb-0 fw-semibold")
                        ]),
                        dbc.Col([
                            dbc.Badge("0", color="light", text_color="dark", 
                                    id=f"kanban-count-{col['status']}")
                        ], width="auto")
                    ])
                ], className="bg-light"),
                dbc.CardBody([
                    html.Div(
                        id=f"kanban-column-{col['status']}",
                        className="kanban-column min-height-400",
                        style={"min-height": "400px"}
                    )
                ], className="p-2")
            ], className="shadow-sm border-0")
        ], md=2, className="mb-3")
        kanban_columns.append(column)
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-columns me-2"),
                "Application Pipeline"
            ], className="mb-0 fw-semibold")
        ]),
        dbc.CardBody([
            dbc.Row(kanban_columns, className="g-3")
        ])
    ], className="mb-4 shadow-sm border-0")


def create_job_card(job_data):
    """Create a draggable job card for the Kanban board"""
    return dbc.Card([
        dbc.CardBody([
            html.H6(job_data.get('title', 'Unknown Title'), 
                   className="fw-bold mb-1 text-truncate"),
            html.P(job_data.get('company', 'Unknown Company'), 
                   className="text-muted small mb-2"),
            html.Div([
                dbc.Badge(job_data.get('location', 'Remote'), 
                         color="light", text_color="dark", className="me-1"),
                dbc.Badge(f"${job_data.get('salary_range', 'N/A')}", 
                         color="success", className="me-1") if job_data.get('salary_range') else None,
            ], className="mb-2"),
            html.Div([
                html.Small([
                    html.I(className="fas fa-calendar me-1"),
                    job_data.get('date_posted', 'Unknown date')
                ], className="text-muted")
            ])
        ])
    ], 
    className="job-card shadow-sm border-0 mb-2 cursor-pointer hover-shadow",
    style={"cursor": "pointer"},
    id={"type": "job-card", "job_id": job_data.get('id', '')}
    )


def create_application_timeline():
    """Create timeline view of recent application activities"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className="fas fa-history me-2"),
                        "Recent Activity"
                    ], className="mb-0 fw-semibold")
                ]),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-plus me-1"),
                        "Add Note"
                    ], color="outline-primary", size="sm", id="add-note-btn")
                ], width="auto")
            ])
        ]),
        dbc.CardBody([
            html.Div(id="activity-timeline", className="timeline-container")
        ])
    ], className="mb-4 shadow-sm border-0")


def create_filters_sidebar():
    """Create collapsible filters sidebar"""
    return dbc.Collapse([
        dbc.Card([
            dbc.CardHeader([
                html.H6([
                    html.I(className="fas fa-filter me-2"),
                    "Filters & Search"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                # Search
                dbc.InputGroup([
                    dbc.InputGroupText(html.I(className="fas fa-search")),
                    dbc.Input(placeholder="Search jobs...", id="job-search-input")
                ], className="mb-3"),
                
                # Status filter
                html.Label("Application Status", className="fw-semibold"),
                dcc.Dropdown(
                    id="status-filter",
                    options=[
                        {"label": "All Statuses", "value": "all"},
                        {"label": "🔍 Discovered", "value": "discovered"},
                        {"label": "💡 Interested", "value": "interested"},
                        {"label": "📤 Applied", "value": "applied"},
                        {"label": "🗣️ Interviewing", "value": "interviewing"},
                        {"label": "🎉 Offer", "value": "offer"},
                        {"label": "❌ Closed", "value": "closed"}
                    ],
                    value="all",
                    className="mb-3"
                ),
                
                # Date range
                html.Label("Date Range", className="fw-semibold"),
                dcc.DatePickerRange(
                    id="date-range-picker",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now(),
                    className="mb-3"
                ),
                
                # Priority filter
                html.Label("Priority Level", className="fw-semibold"),
                dcc.RangeSlider(
                    id="priority-filter",
                    min=1, max=5, step=1,
                    marks={i: str(i) for i in range(1, 6)},
                    value=[1, 5],
                    className="mb-3"
                ),
                
                # Company filter
                html.Label("Companies", className="fw-semibold"),
                dcc.Dropdown(
                    id="company-filter",
                    placeholder="Select companies...",
                    multi=True,
                    className="mb-3"
                ),
                
                dbc.Button("Reset Filters", color="outline-secondary", 
                          size="sm", id="reset-filters-btn", className="w-100")
            ])
        ], className="shadow-sm border-0")
    ], id="filters-collapse", is_open=False)


def create_job_details_modal():
    """Create comprehensive job details modal"""
    return dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle(id="job-modal-title")
        ]),
        dbc.ModalBody([
            dbc.Tabs([
                dbc.Tab(label="📋 Details", tab_id="details"),
                dbc.Tab(label="📝 Notes", tab_id="notes"),
                dbc.Tab(label="🗣️ Interviews", tab_id="interviews"),
                dbc.Tab(label="💬 Communications", tab_id="communications"),
                dbc.Tab(label="📄 Documents", tab_id="documents")
            ], id="job-modal-tabs", active_tab="details"),
            html.Div(id="job-modal-content", className="mt-3")
        ]),
        dbc.ModalFooter([
            dbc.ButtonGroup([
                dbc.Button("Close", color="secondary", id="close-job-modal"),
                dbc.Button("Edit", color="primary", id="edit-job-btn"),
                dbc.Button("Update Status", color="success", id="update-status-btn")
            ])
        ])
    ], id="job-details-modal", size="xl", is_open=False)


def create_job_tracker_layout():
    """Create the complete modern job tracker layout"""
    return html.Div([
        # Header
        create_job_tracker_header(),
        
        # Quick stats
        create_quick_stats_cards(),
        
        # Filters (collapsible)
        create_filters_sidebar(),
        
        # Main content area
        dbc.Row([
            dbc.Col([
                # Kanban board
                create_kanban_board(),
                
                # Timeline
                create_application_timeline()
            ], md=12)
        ]),
        
        # Modals and storage
        create_job_details_modal(),
        
        # Storage components
        dcc.Store(id="job-tracker-data"),
        dcc.Store(id="selected-job-data"),
        
        # Custom CSS - moved to external stylesheet
            .job-card {
                transition: all 0.2s ease;
                border-radius: 8px !important;
            }
            .job-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            }
            .hover-shadow:hover {
                box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
                transition: all 0.2s ease;
            }
            .kanban-column {
                border-radius: 8px;
                background: #f8f9fa;
            }
            .timeline-container {
                max-height: 400px;
                overflow-y: auto;
            }
            .cursor-pointer {
                cursor: pointer;
            }
            .min-height-400 {
                min-height: 400px;
            }
        """)
    ])
