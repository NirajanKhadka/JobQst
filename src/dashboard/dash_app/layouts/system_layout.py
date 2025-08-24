"""
System layout for JobLens Dashboard
System monitoring and health status
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

from ..components.navigation import create_page_header

def create_system_layout():
    """Create the system monitoring layout"""
    
    return html.Div([
        # Page header
        create_page_header(
            "🖥️ System Monitor",
            "Monitor system health and performance"
        ),
        
        # System health overview
        dbc.Row([
            dbc.Col([
                create_health_card("Database", "Healthy", "fas fa-database", "success", "db-health")
            ], width=3),
            dbc.Col([
                create_health_card("API Server", "Running", "fas fa-server", "success", "api-health")
            ], width=3),
            dbc.Col([
                create_health_card("Cache", "Active", "fas fa-memory", "warning", "cache-health")
            ], width=3),
            dbc.Col([
                create_health_card("Scrapers", "Ready", "fas fa-spider", "info", "scraper-health")
            ], width=3)
        ], className="mb-4"),
        
        # System resources
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💾 System Resources"),
                    dbc.CardBody([
                        html.Div([
                            html.Label("CPU Usage", className="fw-semibold"),
                            dbc.Progress(value=25, id="cpu-usage", className="mb-3"),
                            
                            html.Label("Memory Usage", className="fw-semibold"),
                            dbc.Progress(value=45, id="memory-usage", className="mb-3"),
                            
                            html.Label("Disk Usage", className="fw-semibold"),
                            dbc.Progress(value=60, id="disk-usage")
                        ])
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔧 Service Status"),
                    dbc.CardBody([
                        html.Div(id="service-status-list", children=[
                            create_service_status("JobSpy Scraper", True),
                            create_service_status("Job Processor", True),
                            create_service_status("AI Analysis", False),
                            create_service_status("Background Tasks", True)
                        ])
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # System controls
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("⚡ Quick Actions"),
                    dbc.CardBody([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-sync me-2"),
                                "Restart Services"
                            ], color="primary", className="mb-2"),
                            
                            dbc.Button([
                                html.I(className="fas fa-broom me-2"),
                                "Clear Cache"
                            ], color="warning", className="mb-2"),
                            
                            dbc.Button([
                                html.I(className="fas fa-download me-2"),
                                "Export Logs"
                            ], color="info", className="mb-2")
                        ], vertical=True, className="w-100")
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 System Logs"),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id="log-file-selector",
                            options=[
                                {'label': 'Application Logs', 'value': 'app'},
                                {'label': 'Error Logs', 'value': 'error'},
                                {'label': 'System Logs', 'value': 'system'},
                                {'label': 'Dashboard Logs', 'value': 'dashboard'}
                            ],
                            value='app',
                            className="mb-3"
                        ),
                        
                        html.Div(id="log-viewer", className="bg-dark text-light p-3 rounded", style={
                            'height': '300px',
                            'overflow-y': 'auto',
                            'font-family': 'monospace',
                            'font-size': '12px'
                        })
                    ])
                ])
            ], width=8)
        ])
    ])

def create_health_card(title, status, icon, color, health_id):
    """Create a health status card"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6(title, className="fw-bold mb-1"),
                    html.P(id=health_id, children=status, className=f"text-{color} mb-0")
                ], width=8),
                dbc.Col([
                    html.I(className=f"{icon} fs-2 text-{color}")
                ], width=4, className="text-end")
            ], className="align-items-center")
        ])
    ], className="shadow-sm border-0")

def create_service_status(service_name, is_running):
    """Create a service status indicator"""
    return dbc.ListGroupItem([
        dbc.Row([
            dbc.Col([
                html.Span(service_name, className="fw-semibold")
            ], width=8),
            dbc.Col([
                dbc.Badge(
                    "Running" if is_running else "Stopped",
                    color="success" if is_running else "danger"
                )
            ], width=4, className="text-end")
        ], className="align-items-center")
    ])