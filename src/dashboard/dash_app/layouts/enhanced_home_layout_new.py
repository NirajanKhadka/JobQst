"""
Enhanced Home Layout - Modern Dashboard for JobLens
Clean, modern interface with comprehensive job management
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime


def create_modern_header():
    """Create modern dashboard header with branding"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([
                            html.I(className="fas fa-search me-3 text-primary"),
                            "JobLens"
                        ], className="fw-bold mb-1 display-6"),
                        html.P(
                            "AI-Powered Job Discovery & Application Tracking",
                            className="text-muted fs-5 mb-0"
                        )
                    ])
                ], md=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H6("System Status", className="mb-1"),
                                dbc.Badge(
                                    "🟢 Online",
                                    color="success",
                                    id="system-status-indicator"
                                )
                            ], className="text-center")
                        ])
                    ], className="border-0 bg-light")
                ], md=4)
            ])
        ])
    ], className="mb-4 border-0 shadow-sm bg-gradient")


def create_dashboard_stats():
    """Create comprehensive dashboard statistics"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.I(className="fas fa-briefcase fa-3x text-primary")
                        ], width=3, className="d-flex align-items-center"),
                        dbc.Col([
                            html.H3("0", className="fw-bold mb-0", 
                                   id="total-jobs-stat"),
                            html.P("Total Jobs", className="text-muted mb-0")
                        ], width=9)
                    ])
                ])
            ], className="h-100 border-0 shadow-sm")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.I(className="fas fa-paper-plane fa-3x text-success")
                        ], width=3, className="d-flex align-items-center"),
                        dbc.Col([
                            html.H3("0", className="fw-bold mb-0", 
                                   id="applications-stat"),
                            html.P("Applications", className="text-muted mb-0")
                        ], width=9)
                    ])
                ])
            ], className="h-100 border-0 shadow-sm")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.I(className="fas fa-calendar-alt fa-3x text-warning")
                        ], width=3, className="d-flex align-items-center"),
                        dbc.Col([
                            html.H3("0", className="fw-bold mb-0", 
                                   id="interviews-stat"),
                            html.P("Interviews", className="text-muted mb-0")
                        ], width=9)
                    ])
                ])
            ], className="h-100 border-0 shadow-sm")
        ], md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.I(className="fas fa-trophy fa-3x text-info")
                        ], width=3, className="d-flex align-items-center"),
                        dbc.Col([
                            html.H3("0%", className="fw-bold mb-0", 
                                   id="success-rate-stat"),
                            html.P("Success Rate", className="text-muted mb-0")
                        ], width=9)
                    ])
                ])
            ], className="h-100 border-0 shadow-sm")
        ], md=3)
    ], className="mb-4")


def create_quick_actions():
    """Create quick action buttons"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-bolt me-2"),
                "Quick Actions"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-search me-2"),
                        "Discover Jobs"
                    ], color="primary", size="lg", className="w-100 mb-2",
                    id="discover-jobs-btn")
                ], md=3),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Add Application"
                    ], color="success", size="lg", className="w-100 mb-2",
                    id="add-app-btn")
                ], md=3),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-chart-bar me-2"),
                        "View Analytics"
                    ], color="info", size="lg", className="w-100 mb-2",
                    id="view-analytics-btn")
                ], md=3),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-cog me-2"),
                        "Settings"
                    ], color="secondary", size="lg", className="w-100 mb-2",
                    id="settings-btn")
                ], md=3)
            ])
        ])
    ], className="mb-4 border-0 shadow-sm")


def create_recent_activity():
    """Create recent activity section"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className="fas fa-history me-2"),
                        "Recent Activity"
                    ], className="mb-0")
                ]),
                dbc.Col([
                    dbc.Button("View All", color="outline-primary", size="sm")
                ], width="auto")
            ])
        ]),
        dbc.CardBody([
            html.Div(id="recent-activity-content", children=[
                html.P("No recent activity", className="text-muted text-center py-4")
            ])
        ])
    ], className="border-0 shadow-sm")


def create_application_pipeline():
    """Create mini application pipeline overview"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-stream me-2"),
                "Application Pipeline"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Progress([
                dbc.Progress(value=20, color="info", bar=True, 
                           label="Discovered"),
                dbc.Progress(value=15, color="primary", bar=True, 
                           label="Applied"),
                dbc.Progress(value=10, color="warning", bar=True, 
                           label="Interviewing"),
                dbc.Progress(value=5, color="success", bar=True, 
                           label="Offers")
            ], multi=True, className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Small("🔍 Discovered: 0", className="text-muted")
                ], md=3),
                dbc.Col([
                    html.Small("📤 Applied: 0", className="text-muted")
                ], md=3),
                dbc.Col([
                    html.Small("🗣️ Interviewing: 0", className="text-muted")
                ], md=3),
                dbc.Col([
                    html.Small("🎉 Offers: 0", className="text-muted")
                ], md=3)
            ])
        ])
    ], className="mb-4 border-0 shadow-sm")


def create_enhanced_home_layout():
    """Create the enhanced modern home dashboard layout"""
    return html.Div([
        # Modern header
        create_modern_header(),
        
        # Dashboard stats
        create_dashboard_stats(),
        
        # Main content area
        dbc.Row([
            dbc.Col([
                # Quick actions
                create_quick_actions(),
                
                # Application pipeline
                create_application_pipeline()
            ], md=8),
            
            dbc.Col([
                # Recent activity
                create_recent_activity()
            ], md=4)
        ]),
        
        # Storage for data
        dcc.Store(id="dashboard-data"),
        dcc.Interval(id="dashboard-interval", interval=30000, n_intervals=0),
        
        # Custom styling
        html.Style("""
            .bg-gradient {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .shadow-sm {
                box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075) !important;
            }
            .card {
                border-radius: 10px !important;
            }
            .btn {
                border-radius: 8px !important;
            }
        """)
    ])
