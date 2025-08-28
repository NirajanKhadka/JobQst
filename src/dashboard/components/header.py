"""
Dashboard header component
"""
import dash
from dash import html, dcc
import logging

logger = logging.getLogger(__name__)


def render_header(app_title: str = "JobQst Dashboard") -> html.Div:
    """Render dashboard header"""
    return html.Div([
        html.H1(
            app_title,
            className="header-title",
            style={
                'textAlign': 'center',
                'color': '#2c3e50',
                'marginBottom': '20px',
                'fontFamily': 'Arial, sans-serif'
            }
        ),
        html.Hr(style={'marginBottom': '30px'}),
        html.Div(
            id="header-status",
            children=[
                html.Span(
                    "System Status: ",
                    style={'fontWeight': 'bold'}
                ),
                html.Span(
                    "Active",
                    id="status-indicator",
                    style={
                        'color': '#27ae60',
                        'fontWeight': 'bold'
                    }
                )
            ],
            style={
                'textAlign': 'center',
                'marginBottom': '20px'
            }
        )
    ], className="dashboard-header")


def create_navigation() -> html.Div:
    """Create simple navigation"""
    return html.Div([
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            children=[
                dcc.Tab(label="Overview", value="overview"),
                dcc.Tab(label="Jobs", value="jobs"),
                dcc.Tab(label="Analytics", value="analytics"),
                dcc.Tab(label="Settings", value="settings"),
            ],
            style={'marginBottom': '20px'}
        )
    ], className="navigation")
