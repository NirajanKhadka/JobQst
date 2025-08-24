"""
Processing layout for JobLens Dashboard
Real-time job processing controls and monitoring
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

from ..components.navigation import create_page_header

def create_processing_layout():
    """Create the processing control layout"""
    
    return html.Div([
        # Page header
        create_page_header(
            "⚙️ Job Processing",
            "Manage job analysis and processing pipeline"
        ),
        
        # Processing status overview
        dbc.Row([
            dbc.Col([
                create_status_card("Queue Status", "Ready", "fas fa-list", "success", "queue-status")
            ], width=3),
            dbc.Col([
                create_status_card("Processing", "Idle", "fas fa-play", "secondary", "processing-status")
            ], width=3),
            dbc.Col([
                create_status_card("Completed", "0", "fas fa-check", "primary", "completed-count")
            ], width=3),
            dbc.Col([
                create_status_card("Errors", "0", "fas fa-exclamation", "danger", "error-count")
            ], width=3)
        ], className="mb-4"),
        
        # Processing controls
        dbc.Card([
            dbc.CardHeader("🎛️ Processing Controls"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Processing Method", className="fw-semibold"),
                        dcc.Dropdown(
                            id="processing-method",
                            options=[
                                {'label': 'Two-Stage Pipeline (Recommended)', 'value': 'two_stage'},
                                {'label': 'CPU Only', 'value': 'cpu_only'},
                                {'label': 'Auto-Detect', 'value': 'auto_detect'}
                            ],
                            value='two_stage'
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Batch Size", className="fw-semibold"),
                        dbc.Input(
                            id="batch-size",
                            type="number",
                            min=1,
                            max=50,
                            value=10
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Max Jobs", className="fw-semibold"),
                        dbc.Input(
                            id="max-jobs",
                            type="number",
                            min=1,
                            max=1000,
                            value=100
                        )
                    ], width=4)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="processing-options",
                            options=[
                                {'label': 'Enable Smart Filtering', 'value': 'smart_filtering'},
                                {'label': 'Auto-Apply High Matches', 'value': 'auto_apply'},
                                {'label': 'Generate Reports', 'value': 'generate_reports'}
                            ],
                            value=['smart_filtering'],
                            inline=True
                        )
                    ], width=12)
                ], className="mb-3"),
                
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-play me-2"),
                        "Start Processing"
                    ], color="success", size="lg", id="start-processing-btn"),
                    
                    dbc.Button([
                        html.I(className="fas fa-pause me-2"),
                        "Pause"
                    ], color="warning", size="lg", id="pause-processing-btn"),
                    
                    dbc.Button([
                        html.I(className="fas fa-stop me-2"),
                        "Stop"
                    ], color="danger", size="lg", id="stop-processing-btn")
                ])
            ])
        ], className="mb-4"),
        
        # Processing progress
        dbc.Card([
            dbc.CardHeader("📊 Processing Progress"),
            dbc.CardBody([
                html.Div([
                    html.Label("Overall Progress", className="fw-semibold"),
                    dbc.Progress(value=0, id="overall-progress", className="mb-3"),
                    
                    html.Label("Current Batch", className="fw-semibold"),
                    dbc.Progress(value=0, id="batch-progress", className="mb-3"),
                    
                    html.Div(id="processing-log", className="bg-light p-3 rounded", style={
                        'height': '200px',
                        'overflow-y': 'auto',
                        'font-family': 'monospace',
                        'font-size': '12px'
                    })
                ])
            ])
        ])
    ])

def create_status_card(title, value, icon, color, status_id):
    """Create a status card component"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(id=status_id, children=value, className="fw-bold mb-1"),
                    html.P(title, className="text-muted mb-0")
                ], width=8),
                dbc.Col([
                    html.I(className=f"{icon} fs-2 text-{color}")
                ], width=4, className="text-end")
            ], className="align-items-center")
        ])
    ], className="shadow-sm border-0")