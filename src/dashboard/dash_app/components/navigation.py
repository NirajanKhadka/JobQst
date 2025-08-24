"""
Navigation component for JobLens Dashboard
"""
import dash_bootstrap_components as dbc
from dash import html

def create_navigation():
    """Create navigation breadcrumbs or tabs"""
    return html.Div([
        dbc.Breadcrumb([
            {"label": "Dashboard", "href": "/", "active": True}
        ])
    ])

def create_page_header(title, subtitle=None, actions=None):
    """Create a page header with title and optional actions"""
    header_content = [
        html.H2(title, className="mb-1"),
    ]
    
    if subtitle:
        header_content.append(
            html.P(subtitle, className="text-muted mb-3")
        )
    
    if actions:
        return dbc.Row([
            dbc.Col(header_content, width="auto"),
            dbc.Col(actions, width="auto", className="ms-auto")
        ], className="align-items-center mb-4")
    else:
        return html.Div(header_content, className="mb-4")