"""
Enhanced Dashboard App with Complete Standalone Functionality
Integrates scheduling, profile management, and application tracking
"""
import sys
import logging
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
from flask import Flask

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from src.dashboard.dash_app.layouts.enhanced_home_layout import (
    create_enhanced_home_layout
)
from src.dashboard.dash_app.components.profile_manager import (
    create_profile_management_section
)
from src.dashboard.dash_app.components.application_tracker import (
    create_application_tracker
)
from src.dashboard.services.scheduling_service import job_scheduler

logger = logging.getLogger(__name__)

# Initialize Flask app for custom endpoints
server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME
    ],
    suppress_callback_exceptions=True,
    title="JobQst - AI Job Discovery Platform"
)

# Enhanced sidebar with new features
def create_enhanced_sidebar():
    """Create enhanced sidebar with complete functionality"""
    
    return dbc.Nav([
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-home me-2"),
                "🏠 Dashboard"
            ], href="/", active="exact", className="text-light")
        ]),
        
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-search me-2"),
                "🔍 Job Search"
            ], href="/search", active="exact", className="text-light")
        ]),
        
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-list me-2"),
                "📋 Applications"
            ], href="/applications", active="exact", className="text-light")
        ]),
        
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-calendar me-2"),
                "⏰ Scheduler"
            ], href="/scheduler", active="exact", className="text-light")
        ]),
        
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-user me-2"),
                "👤 Profile"
            ], href="/profile", active="exact", className="text-light")
        ]),
        
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-chart-bar me-2"),
                "📊 Analytics"
            ], href="/analytics", active="exact", className="text-light")
        ]),
        
        html.Hr(className="text-light"),
        
        dbc.NavItem([
            dbc.NavLink([
                html.I(className="fas fa-cog me-2"),
                "⚙️ Settings"
            ], href="/settings", active="exact", className="text-light")
        ])
    ], vertical=True, pills=True)


# Main app layout
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    
    # Top navigation bar
    dbc.NavbarSimple([
        dbc.NavItem([
            dbc.Badge([
                html.I(className="fas fa-robot me-1"),
                "JobQst AI"
            ], color="success", className="fs-6")
        ]),
        
        dbc.NavItem([
            dbc.Button([
                html.I(className="fas fa-play me-1"),
                "Quick Start"
            ], id="nav-quick-start", color="primary", size="sm")
        ])
    ], brand="🚀 JobQst", brand_href="/", color="dark", dark=True),
    
    dbc.Row([
        # Enhanced sidebar
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    create_enhanced_sidebar()
                ])
            ], className="h-100", color="dark", outline=True)
        ], width=2, className="pe-0"),
        
        # Main content area
        dbc.Col([
            html.Div(id="page-content", className="p-4")
        ], width=10)
    ], className="mt-3")
], fluid=True)


# Router callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    """Route pages based on URL"""
    if pathname == '/' or pathname == '/dashboard':
        return create_enhanced_home_layout()
    elif pathname == '/search':
        return create_job_search_page()
    elif pathname == '/applications':
        return create_application_tracker()
    elif pathname == '/scheduler':
        return create_scheduler_page()
    elif pathname == '/profile':
        return create_profile_management_section()
    elif pathname == '/analytics':
        return create_analytics_page()
    elif pathname == '/settings':
        return create_settings_page()
    else:
        return dbc.Alert(
            "🚫 Page not found", 
            color="warning",
            className="text-center"
        )


def create_job_search_page():
    """Create enhanced job search page"""
    return html.Div([
        dbc.Card([
            dbc.CardHeader("🔍 AI-Powered Job Search"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Search Keywords", className="fw-semibold"),
                        dbc.Input(
                            id="search-keywords",
                            placeholder="python, data scientist, remote",
                            value=""
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Location", className="fw-semibold"),
                        dcc.Dropdown(
                            id="search-location",
                            options=[
                                {'label': 'Remote', 'value': 'remote'},
                                {'label': 'Toronto', 'value': 'toronto'},
                                {'label': 'Vancouver', 'value': 'vancouver'},
                                {'label': 'Montreal', 'value': 'montreal'}
                            ],
                            placeholder="Select location"
                        )
                    ], width=3),
                    
                    dbc.Col([
                        html.Label("Job Sites", className="fw-semibold"),
                        dcc.Dropdown(
                            id="search-sites",
                            options=[
                                {'label': 'All Sites', 'value': 'all'},
                                {'label': 'Indeed', 'value': 'indeed'},
                                {'label': 'LinkedIn', 'value': 'linkedin'},
                                {'label': 'Glassdoor', 'value': 'glassdoor'}
                            ],
                            value='all'
                        )
                    ], width=3),
                    
                    dbc.Col([
                        html.Label(" ", className="fw-semibold"),
                        dbc.Button(
                            "🚀 Start Search",
                            id="start-search-btn",
                            color="success",
                            className="w-100"
                        )
                    ], width=2)
                ])
            ])
        ], className="mb-4"),
        
        # Search results area
        html.Div(id="search-results-area")
    ])


def create_scheduler_page():
    """Create scheduler management page"""
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4("⏰ Job Search Scheduler", className="mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.Button(
                            "➕ New Schedule",
                            id="new-schedule-btn",
                            color="success"
                        )
                    ], width=4)
                ])
            ]),
            dbc.CardBody([
                html.Div(id="schedules-list", children=[
                    create_schedules_display()
                ])
            ])
        ])
    ])


def create_schedules_display():
    """Create display of current schedules"""
    schedules = job_scheduler.get_schedules()
    
    if not schedules:
        return dbc.Alert(
            "⏰ No scheduled searches yet. Create your first schedule!",
            color="info",
            className="text-center"
        )
    
    schedule_cards = []
    for schedule in schedules:
        schedule_cards.append(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6(schedule['name'], className="mb-1"),
                            html.P(f"Keywords: {', '.join(schedule['keywords'])}", 
                                  className="text-muted small mb-1"),
                            html.P(f"Location: {schedule['location']}", 
                                  className="text-muted small mb-0")
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Badge(
                                schedule['schedule_type'].replace('_', ' ').title(),
                                color="info",
                                className="mb-2"
                            ),
                            html.Br(),
                            html.Small(f"Next: {schedule.get('next_run', 'N/A')}", 
                                     className="text-muted")
                        ], width=4),
                        
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("⏸️" if schedule['enabled'] else "▶️", 
                                         size="sm", outline=True),
                                dbc.Button("✏️", size="sm", outline=True),
                                dbc.Button("🗑️", size="sm", 
                                         outline=True, color="danger")
                            ])
                        ], width=2)
                    ])
                ])
            ], className="mb-3")
        )
    
    return html.Div(schedule_cards)


def create_analytics_page():
    """Create analytics and insights page"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Job Search Analytics"),
                    dbc.CardBody([
                        html.P("Coming soon: Advanced analytics and insights")
                    ])
                ])
            ], width=12)
        ])
    ])


def create_settings_page():
    """Create settings and configuration page"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("⚙️ System Settings"),
                    dbc.CardBody([
                        html.P("Coming soon: System configuration options")
                    ])
                ])
            ], width=12)
        ])
    ])


# Initialize scheduler
def initialize_app():
    """Initialize the application"""
    try:
        job_scheduler.start()
        logger.info("JobQst Dashboard initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing dashboard: {e}")


if __name__ == '__main__':
    initialize_app()
    app.run_server(
        host='0.0.0.0',
        port=8050,
        debug=True
    )
