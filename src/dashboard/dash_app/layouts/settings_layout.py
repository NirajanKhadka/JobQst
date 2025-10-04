"""
Settings layout for JobQst Dashboard
Configuration and preferences management
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

from src.dashboard.dash_app.components.navigation import create_page_header


def create_settings_layout():
    """Create the settings configuration layout with enhanced profile optimization"""

    return html.Div(
        [
            # Page header
            create_page_header("⚙️ Settings", "Configure dashboard and processing preferences"),
            # Settings tabs
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(label="👤 Profile Settings", tab_id="profile-settings"),
                                    dbc.Tab(label="🎯 Job Preferences", tab_id="job-preferences"),
                                    dbc.Tab(label="📊 Dashboard Settings", tab_id="dashboard-settings"),
                                    dbc.Tab(label="💾 Data Management", tab_id="data-management"),
                                ],
                                id="settings-tabs",
                                active_tab="profile-settings",
                            )
                        ]
                    ),
                    dbc.CardBody([html.Div(id="settings-content")]),
                ]
            ),
            # Save notification
            html.Div(id="settings-save-notification"),
        ]
    )


def create_processing_settings():
    """Create processing settings content"""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("⚙️ Default Processing Configuration"),
                            html.Label("Processing Method", className="fw-semibold mt-3"),
                            dcc.Dropdown(
                                id="default-processing-method",
                                options=[
                                    {"label": "Two-Stage Pipeline", "value": "two_stage"},
                                    {"label": "CPU Only", "value": "cpu_only"},
                                    {"label": "Auto-Detect", "value": "auto_detect"},
                                ],
                                value="two_stage",
                            ),
                            html.Label("Default Batch Size", className="fw-semibold mt-3"),
                            dbc.Input(
                                id="default-batch-size", type="number", min=1, max=50, value=10
                            ),
                            html.Label("Minimum Match Score", className="fw-semibold mt-3"),
                            dcc.Slider(
                                id="min-match-score",
                                min=0,
                                max=100,
                                step=5,
                                value=60,
                                marks={i: f"{i}%" for i in range(0, 101, 20)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H5("🎯 Quality Filters"),
                            dbc.Checklist(
                                id="processing-features",
                                options=[
                                    {"label": "Enable Smart Filtering", "value": "smart_filtering"},
                                    {"label": "Auto-process New Jobs", "value": "auto_process"},
                                    {"label": "Skip Low-Quality Jobs", "value": "skip_low_quality"},
                                    {
                                        "label": "Prioritize Remote Jobs",
                                        "value": "prioritize_remote",
                                    },
                                    {
                                        "label": "Generate Processing Reports",
                                        "value": "generate_reports",
                                    },
                                ],
                                value=["smart_filtering", "skip_low_quality"],
                                className="mt-3",
                            ),
                            html.Label("Max Concurrent Jobs", className="fw-semibold mt-3"),
                            dbc.Input(
                                id="max-concurrent-jobs", type="number", min=1, max=10, value=5
                            ),
                        ],
                        width=6,
                    ),
                ]
            )
        ]
    )


def create_dashboard_settings():
    """Create enhanced dashboard settings content"""
    return html.Div(
        [
            html.H5("📊 Display Preferences", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Default View", className="fw-semibold"),
                            dcc.Dropdown(
                                id="dash-settings-default-view",
                                options=[
                                    {"label": "Table View", "value": "table"},
                                    {"label": "Card View", "value": "cards"},
                                    {"label": "Compact View", "value": "compact"},
                                ],
                                value="table",
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Jobs per Page", className="fw-semibold"),
                            dcc.Dropdown(
                                id="dash-settings-jobs-per-page",
                                options=[
                                    {"label": "10 jobs", "value": 10},
                                    {"label": "25 jobs", "value": 25},
                                    {"label": "50 jobs", "value": 50},
                                    {"label": "100 jobs", "value": 100},
                                ],
                                value=25,
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            html.H5("🔄 Auto-Refresh Settings", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id="dash-settings-auto-refresh",
                                options=[
                                    {"label": "Enable Auto-refresh", "value": "enabled"},
                                ],
                                value=["enabled"],
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Refresh Interval (seconds)", className="fw-semibold"),
                            dbc.Input(
                                id="dash-settings-refresh-interval",
                                type="number",
                                min=10,
                                max=300,
                                value=60,
                                step=10
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            html.H5("🔔 Notifications", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id="dash-settings-notifications",
                                options=[
                                    {"label": "Enable Notifications", "value": "enabled"},
                                    {"label": "Notify on New Jobs", "value": "new_jobs"},
                                    {"label": "Notify on High Matches", "value": "high_matches"},
                                ],
                                value=["enabled", "new_jobs"],
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            html.H5("🎯 Filters", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id="dash-settings-filters",
                                options=[
                                    {"label": "Show RCIP Jobs Only by Default", "value": "rcip_only"},
                                    {"label": "Hide Applied Jobs", "value": "hide_applied"},
                                    {"label": "Show Remote Jobs First", "value": "remote_first"},
                                ],
                                value=[],
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            
            # Save button
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-save me-2"), "Save Dashboard Settings"],
                                id="save-dashboard-settings-btn",
                                color="primary",
                                size="lg",
                                className="w-100"
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
        ]
    )


def create_data_management():
    """Create data management content"""
    return html.Div(
        [
            html.H5("💾 Database Management", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6("Export Data", className="mb-3"),
                                            html.P(
                                                "Download your job data in various formats",
                                                className="text-muted small"
                                            ),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        [html.I(className="fas fa-file-csv me-2"), "CSV"],
                                                        id="export-data-csv",
                                                        color="success",
                                                        outline=True
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="fas fa-file-excel me-2"), "Excel"],
                                                        id="export-data-excel",
                                                        color="success",
                                                        outline=True
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="fas fa-file-code me-2"), "JSON"],
                                                        id="export-data-json",
                                                        color="success",
                                                        outline=True
                                                    ),
                                                ],
                                                className="w-100"
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3"
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6("Clear Cache", className="mb-3"),
                                            html.P(
                                                "Clear cached data to free up space",
                                                className="text-muted small"
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-trash me-2"), "Clear All Cache"],
                                                id="clear-cache-btn",
                                                color="warning",
                                                outline=True,
                                                className="w-100"
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3"
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            html.H5("⚠️ Danger Zone", className="mb-4 text-danger"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6("Reset Settings", className="mb-3"),
                                            html.P(
                                                "Reset all settings to default values",
                                                className="text-muted small"
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-undo me-2"), "Reset to Defaults"],
                                                id="reset-settings-btn",
                                                color="danger",
                                                outline=True,
                                                className="w-100"
                                            ),
                                        ]
                                    ),
                                ],
                                className="border-danger"
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
        ]
    )


def create_profile_settings():
    """Create enhanced profile settings content"""
    return html.Div(
        [
            html.H5("👤 Personal Information", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Full Name", className="fw-semibold"),
                            dbc.Input(
                                id="profile-full-name",
                                type="text",
                                placeholder="Enter your full name"
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Email", className="fw-semibold"),
                            dbc.Input(
                                id="profile-email",
                                type="email",
                                placeholder="your.email@example.com"
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            html.H5("🎓 Professional Background", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Years of Experience", className="fw-semibold"),
                            dbc.Input(
                                id="profile-experience-years",
                                type="number",
                                min=0,
                                max=50,
                                placeholder="e.g., 5"
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Current Job Title", className="fw-semibold"),
                            dbc.Input(
                                id="profile-current-title",
                                type="text",
                                placeholder="e.g., Data Analyst"
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Skills (comma-separated)", className="fw-semibold"),
                            dbc.Textarea(
                                id="profile-skills",
                                placeholder="Python, SQL, Data Analysis, Machine Learning, Tableau",
                                rows=3,
                            ),
                            html.Small(
                                "Enter your key skills separated by commas",
                                className="text-muted"
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            
            # Save button
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-save me-2"), "Save Profile Settings"],
                                id="save-profile-settings-btn",
                                color="primary",
                                size="lg",
                                className="w-100"
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
        ]
    )


def create_job_preferences():
    """Create job preferences content"""
    return html.Div(
        [
            html.H5("📍 Location Preferences", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Preferred Locations", className="fw-semibold"),
                            dbc.Textarea(
                                id="job-pref-locations",
                                placeholder="Toronto, Vancouver, Montreal, Remote",
                                rows=3,
                            ),
                            html.Small(
                                "Enter cities or 'Remote' separated by commas",
                                className="text-muted"
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            html.H5("💰 Salary Expectations", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Desired Salary Range (CAD)", className="fw-semibold mb-3"),
                            dcc.RangeSlider(
                                id="job-pref-salary-range",
                                min=40000,
                                max=200000,
                                step=5000,
                                value=[80000, 150000],
                                marks={i: f"${i//1000}k" for i in range(40000, 201000, 40000)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            
            html.Hr(),
            html.H5("🏢 Work Preferences", className="mb-4"),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id="job-pref-work-type",
                                options=[
                                    {"label": "Remote Work Preferred", "value": "remote_preferred"},
                                    {"label": "Hybrid Work OK", "value": "hybrid_ok"},
                                    {"label": "On-site Work OK", "value": "onsite_ok"},
                                ],
                                value=["remote_preferred", "hybrid_ok"],
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Checklist(
                                id="job-pref-employment-type",
                                options=[
                                    {"label": "Full-time Only", "value": "fulltime_only"},
                                    {"label": "Contract OK", "value": "contract_ok"},
                                    {"label": "Part-time OK", "value": "parttime_ok"},
                                ],
                                value=["fulltime_only"],
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-3",
            ),
            
            html.Hr(),
            
            # Save button
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-save me-2"), "Save Job Preferences"],
                                id="save-job-preferences-btn",
                                color="primary",
                                size="lg",
                                className="w-100"
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
        ]
    )


def create_workflow_settings():
    """Create workflow settings content"""
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("🚀 Automation Settings"),
                            html.Label("Automation Level", className="fw-semibold mt-3"),
                            dcc.Slider(
                                id="automation-level",
                                min=0,
                                max=3,
                                step=1,
                                value=1,
                                marks={0: "Manual", 1: "Semi-Auto", 2: "Auto", 3: "Full-Auto"},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                            html.Label("Auto-Apply Threshold", className="fw-semibold mt-3"),
                            dcc.Slider(
                                id="auto-apply-threshold",
                                min=70,
                                max=100,
                                step=5,
                                value=90,
                                marks={i: f"{i}%" for i in range(70, 101, 10)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                            html.Label("Daily Application Limit", className="fw-semibold mt-3"),
                            dbc.Input(id="daily-limit", type="number", min=1, max=50, value=10),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H5("🎯 Smart Features"),
                            dbc.Checklist(
                                id="workflow-features",
                                options=[
                                    {"label": "Skip Applied Companies", "value": "skip_applied"},
                                    {"label": "Learning Mode", "value": "learning_mode"},
                                    {"label": "Smart Scheduling", "value": "smart_schedule"},
                                    {"label": "Email Notifications", "value": "email_notify"},
                                    {"label": "Weekly Reports", "value": "weekly_reports"},
                                ],
                                value=["skip_applied", "learning_mode"],
                                className="mt-3",
                            ),
                            html.Hr(),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-save me-2"), "Save Settings"],
                                        color="primary",
                                        size="lg",
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-undo me-2"), "Reset to Defaults"],
                                        color="outline-secondary",
                                        size="lg",
                                    ),
                                ],
                                className="w-100",
                            ),
                        ],
                        width=6,
                    ),
                ]
            )
        ]
    )
