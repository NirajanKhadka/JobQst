"""
Application Tracking System for JobQst Dashboard
Complete job application pipeline management
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime
from enum import Enum


class ApplicationStatus(Enum):
    """Application status enum"""
    INTERESTED = "interested"
    APPLIED = "applied"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_RECEIVED = "offer_received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


def create_application_tracker():
    """Create the application tracking dashboard"""
    
    return html.Div([
        # Application pipeline header
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4("🎯 Job Application Pipeline", className="mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.Button(
                            "📊 Export Report",
                            id="export-applications-btn",
                            size="sm",
                            outline=True
                        )
                    ], width=4)
                ])
            ])
        ], className="mb-4"),
        
        # Quick stats
        dbc.Row([
            create_pipeline_stat_card("🎯 Interested", "0", "interested"),
            create_pipeline_stat_card("📝 Applied", "0", "applied"),
            create_pipeline_stat_card("💬 Interviews", "0", "interviews"),
            create_pipeline_stat_card("🎉 Offers", "0", "offers")
        ], className="mb-4"),
        
        # Kanban board
        dbc.Card([
            dbc.CardHeader("📋 Application Board"),
            dbc.CardBody([
                html.Div(id="application-kanban-board", children=[
                    create_kanban_board()
                ])
            ])
        ])
    ])


def create_pipeline_stat_card(title, count, status):
    """Create a pipeline statistics card"""
    color_map = {
        "interested": "info",
        "applied": "primary", 
        "interviews": "warning",
        "offers": "success"
    }
    
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H3(count, id=f"stat-{status}-count", 
                       className=f"text-{color_map[status]} mb-0"),
                html.P(title, className="text-muted small mb-0")
            ])
        ])
    ], width=3)


def create_kanban_board():
    """Create the kanban board for application tracking"""
    
    statuses = [
        ("🎯 Interested", "interested", "info"),
        ("📝 Applied", "applied", "primary"),
        ("💬 Interview", "interview", "warning"),
        ("🎉 Offers", "offers", "success")
    ]
    
    return dbc.Row([
        dbc.Col([
            create_kanban_column(title, status, color)
            for title, status, color in statuses
        ])
    ])


def create_kanban_column(title, status, color):
    """Create a single kanban column"""
    
    return dbc.Col([
        dbc.Card([
            dbc.CardHeader([
                html.H6(title, className=f"text-{color} mb-0")
            ]),
            dbc.CardBody([
                html.Div(
                    id=f"kanban-{status}",
                    className="kanban-column",
                    style={"min-height": "400px"},
                    children=[
                        create_sample_job_card() if status == "interested" else
                        html.P("Drag jobs here", 
                              className="text-muted text-center mt-4")
                    ]
                )
            ])
        ])
    ], width=3)


def create_sample_job_card():
    """Create a sample job card for the kanban board"""
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("Senior Data Scientist", className="card-title"),
            html.P("TechCorp Inc.", className="text-muted small"),
            dbc.Badge("Remote", color="success", className="me-2"),
            dbc.Badge("$120k", color="info"),
            html.Hr(),
            dbc.ButtonGroup([
                dbc.Button("👁️", size="sm", outline=True),
                dbc.Button("📝", size="sm", outline=True), 
                dbc.Button("➡️", size="sm", color="primary")
            ], size="sm")
        ])
    ], className="mb-2", style={"cursor": "move"})


def create_job_application_modal():
    """Create modal for job application details"""
    
    return dbc.Modal([
        dbc.ModalHeader("📝 Job Application Details"),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Application Status", className="fw-semibold"),
                    dcc.Dropdown(
                        id="app-status-dropdown",
                        options=[
                            {'label': '🎯 Interested', 'value': 'interested'},
                            {'label': '📝 Applied', 'value': 'applied'},
                            {'label': '💬 Interview Scheduled', 
                             'value': 'interview_scheduled'},
                            {'label': '💬 Interview Completed', 
                             'value': 'interview_completed'},
                            {'label': '🎉 Offer Received', 'value': 'offer_received'},
                            {'label': '✅ Accepted', 'value': 'accepted'},
                            {'label': '❌ Rejected', 'value': 'rejected'},
                            {'label': '🚫 Withdrawn', 'value': 'withdrawn'}
                        ]
                    ),
                    
                    html.Label("Application Date", className="fw-semibold mt-3"),
                    dcc.DatePickerSingle(
                        id="app-date-picker",
                        date=datetime.now().date()
                    ),
                    
                    html.Label("Interview Date", className="fw-semibold mt-3"),
                    dcc.DatePickerSingle(
                        id="interview-date-picker"
                    )
                ], width=6),
                
                dbc.Col([
                    html.Label("Cover Letter", className="fw-semibold"),
                    dbc.Textarea(
                        id="cover-letter-text",
                        placeholder="Paste or write your cover letter...",
                        rows=8
                    ),
                    
                    dbc.Button(
                        "🤖 Generate Cover Letter",
                        id="generate-cover-letter-btn",
                        color="info",
                        size="sm",
                        className="mt-2"
                    )
                ], width=6)
            ]),
            
            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Notes", className="fw-semibold"),
                    dbc.Textarea(
                        id="app-notes",
                        placeholder="Add notes about this application...",
                        rows=3
                    )
                ])
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="app-modal-cancel", 
                      color="secondary", className="me-2"),
            dbc.Button("Save Application", id="app-modal-save", 
                      color="primary")
        ])
    ], id="job-application-modal", size="lg")


def create_application_calendar():
    """Create calendar view for interviews and deadlines"""
    
    return dbc.Card([
        dbc.CardHeader("📅 Interview Calendar"),
        dbc.CardBody([
            html.Div([
                # Calendar component would go here
                # For now, showing upcoming events
                html.H6("Upcoming Interviews"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Div([
                            html.Strong("TechCorp - Final Interview"),
                            html.Br(),
                            html.Small("Tomorrow 2:00 PM", 
                                     className="text-muted")
                        ])
                    ]),
                    dbc.ListGroupItem([
                        html.Div([
                            html.Strong("DataCorp - Phone Screen"),
                            html.Br(),
                            html.Small("Friday 10:00 AM", 
                                     className="text-muted")
                        ])
                    ])
                ])
            ])
        ])
    ])


def create_application_analytics():
    """Create analytics view for application tracking"""
    
    return dbc.Card([
        dbc.CardHeader("📊 Application Analytics"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Application Funnel"),
                    # Chart would go here
                    html.Div("Chart placeholder", 
                           className="text-center text-muted",
                           style={"height": "200px", "line-height": "200px"})
                ], width=6),
                
                dbc.Col([
                    html.H6("Response Rates"),
                    dbc.Progress([
                        dbc.Progress(
                            "Applied: 15", value=15, color="info", 
                            bar=True, className="mb-1"
                        ),
                        dbc.Progress(
                            "Responses: 8", value=8, color="warning",
                            bar=True, className="mb-1"
                        ),
                        dbc.Progress(
                            "Interviews: 3", value=3, color="success",
                            bar=True
                        )
                    ], multi=True)
                ], width=6)
            ])
        ])
    ])


def create_quick_apply_section():
    """Create quick apply functionality"""
    
    return dbc.Card([
        dbc.CardHeader("⚡ Quick Apply"),
        dbc.CardBody([
            html.P("Apply to multiple jobs with one click"),
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select Resume"),
                        dcc.Dropdown(
                            id="quick-apply-resume",
                            options=[
                                {'label': 'Resume_2024.pdf', 'value': 'resume_2024'},
                                {'label': 'Resume_Tech.pdf', 'value': 'resume_tech'}
                            ]
                        )
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Label("Cover Letter Template"),
                        dcc.Dropdown(
                            id="quick-apply-cover-letter",
                            options=[
                                {'label': 'Generic Template', 'value': 'generic'},
                                {'label': 'Tech Companies', 'value': 'tech'},
                                {'label': 'Custom', 'value': 'custom'}
                            ]
                        )
                    ], width=6)
                ]),
                
                dbc.Button(
                    "📤 Apply to Selected Jobs",
                    id="bulk-apply-btn",
                    color="success",
                    className="mt-3"
                )
            ])
        ])
    ])
