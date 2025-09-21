"""
Sidebar component for JobQst Dashboard
"""
import dash_bootstrap_components as dbc
from dash import html
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.dash_app.utils.data_loader import DataLoader

 
def create_sidebar():
    """Create the main sidebar navigation"""
    
    return dbc.Card([
        dbc.CardBody([
            # Logo and title
            html.Div([
                html.I(className="fas fa-rocket fs-1 text-info mb-3"),
                html.H4("JobQst", className="fw-bold text-info"),
                html.P(
                    "AI-Powered Job Search",
                    className="text-light small mb-4"
                )
            ], className="text-center"),
            
            html.Hr(className="border-secondary"),
            
            # Current Profile Display (no switching)
            html.Div([
                html.Label(
                    "👤 Current Profile",
                    className="fw-semibold mb-2 text-light"
                ),
                dbc.Badge(
                    id="current-profile-display",
                    children="Profile will be loaded...",
                    color="info",
                    className="mb-3 p-2 fs-6"
                )
            ]),
            
            html.Hr(className="border-secondary"),
            
            # Navigation menu
            html.Div([
                html.Label(
                    "📋 Navigation",
                    className="fw-semibold mb-2 text-light"
                ),
                dbc.Nav([
                    dbc.NavItem(
                        dbc.NavLink([
                            html.I(className="fas fa-home me-2"),
                            "Dashboard"
                        ], href="#", id="nav-home", active=True,
                                   className="py-2")
                    ),
                    
                    dbc.NavItem(
                        dbc.NavLink([
                            html.I(className="fas fa-clipboard-list me-2"),
                            "Job Tracker"
                        ], href="#", id="nav-job-tracker", className="py-2")
                    ),
                    
                    dbc.NavItem(
                        dbc.NavLink([
                            html.I(className="fas fa-briefcase me-2"),
                            "Jobs"
                        ], href="#", id="nav-jobs", className="py-2")
                    ),
                    
                    dbc.NavItem(dbc.NavLink([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Analytics"
                    ], href="#", id="nav-analytics", className="py-2")),
                    
                    dbc.NavItem(dbc.NavLink([
                        html.I(className="fas fa-tools me-2"),
                        "Utilities"
                    ], href="#", id="nav-utilities", className="py-2")),
                    
                    dbc.NavItem(dbc.NavLink([
                        html.I(className="fas fa-spider me-2"),
                        "Scraping"
                    ], href="#", id="nav-scraping", className="py-2")),
                    
                    dbc.NavItem(dbc.NavLink([
                        html.I(className="fas fa-cogs me-2"),
                        "Processing"
                    ], href="#", id="nav-processing", className="py-2")),
                    
                    dbc.NavItem(dbc.NavLink([
                        html.I(className="fas fa-server me-2"),
                        "System"
                    ], href="#", id="nav-system", className="py-2")),
                    
                    dbc.NavItem(dbc.NavLink([
                        html.I(className="fas fa-sliders-h me-2"),
                        "Settings"
                    ], href="#", id="nav-settings", className="py-2"))
                ], vertical=True, pills=True, id="sidebar-nav")
            ]),
            
            html.Hr(className="border-secondary"),
            
            # Quick actions
            html.Div([
                html.Label(
                    "⚡ Quick Actions",
                    className="fw-semibold mb-2 text-light"
                ),
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-search me-1"),
                        "Scrape"
                    ],
                        color="primary",
                        size="sm",
                        className="mb-2",
                        id="quick-scrape-btn"
                    ),
                    
                    dbc.Button([
                        html.I(className="fas fa-play me-1"),
                        "Process"
                    ], color="success", size="sm", className="mb-2",
                       id="quick-process")
                ], vertical=True, className="w-100")
            ]),
            
            html.Hr(className="border-secondary"),
            
            # System status
            html.Div([
                html.Label(
                    "💊 System Health",
                    className="fw-semibold mb-2 text-light"
                ),
                html.Div(id="sidebar-system-status", children=[
                    dbc.Badge(
                        "Database",
                        color="success",
                        className="me-1 mb-1"
                    ),
                    dbc.Badge(
                        "API",
                        color="success",
                        className="me-1 mb-1"
                    ),
                    dbc.Badge(
                        "Cache",
                        color="warning",
                        className="me-1 mb-1"
                    )
                ])
            ])
        ])
    ], className="h-100 shadow-sm bg-dark")


def create_profile_stats_card(profile_name):
    """Create profile statistics card"""
    data_loader = DataLoader()
    stats = data_loader.get_job_stats(profile_name)
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("📊 Profile Stats", className="card-title"),
            html.Div([
                html.Small(f"Total Jobs: {stats.get('total_jobs', 0)}",
                           className="d-block"),
                html.Small(f"Applied: {stats.get('applied_jobs', 0)}",
                           className="d-block"),
                html.Small(
                    f"Avg Score: {stats.get('avg_match_score', 0):.1f}%",
                    className="d-block"
                )
            ])
        ])
    ], size="sm", className="mt-3")

