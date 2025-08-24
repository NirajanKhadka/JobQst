"""
Settings layout for JobLens Dashboard
Configuration and preferences management
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

from ..components.navigation import create_page_header

def create_settings_layout():
    """Create the settings configuration layout"""
    
    return html.Div([
        # Page header
        create_page_header(
            "⚙️ Settings",
            "Configure dashboard and processing preferences"
        ),
        
        # Settings tabs
        dbc.Card([
            dbc.CardHeader([
                dbc.Tabs([
                    dbc.Tab(label="🔧 Processing", tab_id="processing-settings"),
                    dbc.Tab(label="📊 Dashboard", tab_id="dashboard-settings"),
                    dbc.Tab(label="👤 Profile", tab_id="profile-settings"),
                    dbc.Tab(label="🚀 Workflow", tab_id="workflow-settings")
                ], id="settings-tabs", active_tab="processing-settings")
            ]),
            
            dbc.CardBody([
                html.Div(id="settings-content")
            ])
        ])
    ])

def create_processing_settings():
    """Create processing settings content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("⚙️ Default Processing Configuration"),
                
                html.Label("Processing Method", className="fw-semibold mt-3"),
                dcc.Dropdown(
                    id="default-processing-method",
                    options=[
                        {'label': 'Two-Stage Pipeline', 'value': 'two_stage'},
                        {'label': 'CPU Only', 'value': 'cpu_only'},
                        {'label': 'Auto-Detect', 'value': 'auto_detect'}
                    ],
                    value='two_stage'
                ),
                
                html.Label("Default Batch Size", className="fw-semibold mt-3"),
                dbc.Input(
                    id="default-batch-size",
                    type="number",
                    min=1,
                    max=50,
                    value=10
                ),
                
                html.Label("Minimum Match Score", className="fw-semibold mt-3"),
                dcc.Slider(
                    id="min-match-score",
                    min=0,
                    max=100,
                    step=5,
                    value=60,
                    marks={i: f"{i}%" for i in range(0, 101, 20)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], width=6),
            
            dbc.Col([
                html.H5("🎯 Quality Filters"),
                
                dbc.Checklist(
                    id="processing-features",
                    options=[
                        {'label': 'Enable Smart Filtering', 'value': 'smart_filtering'},
                        {'label': 'Auto-process New Jobs', 'value': 'auto_process'},
                        {'label': 'Skip Low-Quality Jobs', 'value': 'skip_low_quality'},
                        {'label': 'Prioritize Remote Jobs', 'value': 'prioritize_remote'},
                        {'label': 'Generate Processing Reports', 'value': 'generate_reports'}
                    ],
                    value=['smart_filtering', 'skip_low_quality'],
                    className="mt-3"
                ),
                
                html.Label("Max Concurrent Jobs", className="fw-semibold mt-3"),
                dbc.Input(
                    id="max-concurrent-jobs",
                    type="number",
                    min=1,
                    max=10,
                    value=5
                )
            ], width=6)
        ])
    ])

def create_dashboard_settings():
    """Create dashboard settings content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("📊 Display Preferences"),
                
                html.Label("Default View", className="fw-semibold mt-3"),
                dcc.Dropdown(
                    id="default-view",
                    options=[
                        {'label': 'Table View', 'value': 'table'},
                        {'label': 'Card View', 'value': 'cards'}
                    ],
                    value='table'
                ),
                
                html.Label("Jobs per Page", className="fw-semibold mt-3"),
                dcc.Slider(
                    id="jobs-per-page",
                    min=10,
                    max=100,
                    step=10,
                    value=25,
                    marks={i: str(i) for i in range(10, 101, 20)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                dbc.Checklist(
                    id="dashboard-features",
                    options=[
                        {'label': 'Enable Auto-refresh', 'value': 'auto_refresh'},
                        {'label': 'Show Debug Info', 'value': 'debug_info'},
                        {'label': 'Enable Notifications', 'value': 'notifications'},
                        {'label': 'Dark Mode', 'value': 'dark_mode'}
                    ],
                    value=['auto_refresh'],
                    className="mt-3"
                )
            ], width=6),
            
            dbc.Col([
                html.H5("⚡ Performance"),
                
                html.Label("Auto-refresh Interval (seconds)", className="fw-semibold mt-3"),
                dbc.Input(
                    id="refresh-interval",
                    type="number",
                    min=10,
                    max=300,
                    value=30
                ),
                
                html.Label("Cache TTL (minutes)", className="fw-semibold mt-3"),
                dbc.Input(
                    id="cache-ttl",
                    type="number",
                    min=1,
                    max=60,
                    value=5
                ),
                
                dbc.Checklist(
                    id="performance-options",
                    options=[
                        {'label': 'Enable Caching', 'value': 'enable_cache'},
                        {'label': 'Lazy Load Charts', 'value': 'lazy_charts'},
                        {'label': 'Compress Data', 'value': 'compress_data'}
                    ],
                    value=['enable_cache'],
                    className="mt-3"
                )
            ], width=6)
        ])
    ])

def create_profile_settings():
    """Create profile settings content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("👤 Profile Configuration"),
                
                html.Label("Profile Name", className="fw-semibold mt-3"),
                dbc.Input(
                    id="profile-name",
                    type="text",
                    placeholder="Enter profile name"
                ),
                
                html.Label("Preferred Locations", className="fw-semibold mt-3"),
                dbc.Textarea(
                    id="preferred-locations",
                    placeholder="Toronto, Vancouver, Remote",
                    rows=3
                ),
                
                html.Label("Skills & Keywords", className="fw-semibold mt-3"),
                dbc.Textarea(
                    id="skills-keywords",
                    placeholder="Python, Data Science, Machine Learning",
                    rows=3
                )
            ], width=6),
            
            dbc.Col([
                html.H5("💰 Salary Preferences"),
                
                html.Label("Salary Range (CAD)", className="fw-semibold mt-3"),
                dcc.RangeSlider(
                    id="salary-range",
                    min=40000,
                    max=200000,
                    step=5000,
                    value=[80000, 150000],
                    marks={i: f"${i//1000}k" for i in range(40000, 201000, 40000)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                dbc.Checklist(
                    id="job-preferences",
                    options=[
                        {'label': 'Remote Work Preferred', 'value': 'remote_preferred'},
                        {'label': 'Full-time Only', 'value': 'fulltime_only'},
                        {'label': 'Contract OK', 'value': 'contract_ok'},
                        {'label': 'Startup Environment', 'value': 'startup_ok'}
                    ],
                    value=['remote_preferred', 'fulltime_only'],
                    className="mt-4"
                )
            ], width=6)
        ])
    ])

def create_workflow_settings():
    """Create workflow settings content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("🚀 Automation Settings"),
                
                html.Label("Automation Level", className="fw-semibold mt-3"),
                dcc.Slider(
                    id="automation-level",
                    min=0,
                    max=3,
                    step=1,
                    value=1,
                    marks={
                        0: "Manual",
                        1: "Semi-Auto",
                        2: "Auto",
                        3: "Full-Auto"
                    },
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                html.Label("Auto-Apply Threshold", className="fw-semibold mt-3"),
                dcc.Slider(
                    id="auto-apply-threshold",
                    min=70,
                    max=100,
                    step=5,
                    value=90,
                    marks={i: f"{i}%" for i in range(70, 101, 10)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                html.Label("Daily Application Limit", className="fw-semibold mt-3"),
                dbc.Input(
                    id="daily-limit",
                    type="number",
                    min=1,
                    max=50,
                    value=10
                )
            ], width=6),
            
            dbc.Col([
                html.H5("🎯 Smart Features"),
                
                dbc.Checklist(
                    id="workflow-features",
                    options=[
                        {'label': 'Skip Applied Companies', 'value': 'skip_applied'},
                        {'label': 'Learning Mode', 'value': 'learning_mode'},
                        {'label': 'Smart Scheduling', 'value': 'smart_schedule'},
                        {'label': 'Email Notifications', 'value': 'email_notify'},
                        {'label': 'Weekly Reports', 'value': 'weekly_reports'}
                    ],
                    value=['skip_applied', 'learning_mode'],
                    className="mt-3"
                ),
                
                html.Hr(),
                
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-save me-2"),
                        "Save Settings"
                    ], color="primary", size="lg"),
                    
                    dbc.Button([
                        html.I(className="fas fa-undo me-2"),
                        "Reset to Defaults"
                    ], color="outline-secondary", size="lg")
                ], className="w-100")
            ], width=6)
        ])
    ])