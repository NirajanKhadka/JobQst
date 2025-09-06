"""
Advanced filtering components for job search dashboard
Focuses on filters job seekers actually use
"""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_salary_range_filter():
    """Create salary range filter with min/max sliders"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-dollar-sign me-2"),
            html.Strong("Salary Range")
        ]),
        dbc.CardBody([
            html.Label("Minimum Salary", className="form-label"),
            dcc.Slider(
                id="salary-min-slider",
                min=30000,
                max=200000,
                step=5000,
                value=50000,
                marks={
                    30000: '$30K',
                    60000: '$60K',
                    100000: '$100K',
                    150000: '$150K',
                    200000: '$200K+'
                },
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            html.Br(),
            html.Label("Maximum Salary", className="form-label"),
            dcc.Slider(
                id="salary-max-slider",
                min=40000,
                max=300000,
                step=5000,
                value=120000,
                marks={
                    40000: '$40K',
                    80000: '$80K',
                    120000: '$120K',
                    200000: '$200K',
                    300000: '$300K+'
                },
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ])
    ], className="filter-card mb-3")


def create_location_type_filter():
    """Create work arrangement filter (remote/hybrid/on-site)"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-map-marker-alt me-2"),
            html.Strong("Work Arrangement")
        ]),
        dbc.CardBody([
            dbc.Checklist(
                id="location-type-filter",
                options=[
                    {
                        "label": [
                            html.I(className="fas fa-home me-2"),
                            "Remote"
                        ],
                        "value": "remote"
                    },
                    {
                        "label": [
                            html.I(className="fas fa-laptop-house me-2"),
                            "Hybrid"
                        ],
                        "value": "hybrid"
                    },
                    {
                        "label": [
                            html.I(className="fas fa-building me-2"),
                            "On-site"
                        ],
                        "value": "onsite"
                    }
                ],
                value=["remote", "hybrid", "onsite"],  # All selected by default
                inline=False,
                switch=True
            )
        ])
    ], className="filter-card mb-3")


def create_experience_level_filter():
    """Create experience level filter"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-user-graduate me-2"),
            html.Strong("Experience Level")
        ]),
        dbc.CardBody([
            dcc.Dropdown(
                id="experience-level-filter",
                options=[
                    {"label": "🎓 Entry Level (0-2 years)", "value": "entry"},
                    {"label": "👔 Mid Level (3-5 years)", "value": "mid"},
                    {"label": "🏆 Senior Level (6+ years)", "value": "senior"},
                    {"label": "🎯 Lead/Manager", "value": "lead"},
                    {"label": "📈 Executive", "value": "executive"}
                ],
                value=["entry", "mid", "senior"],  # Most common levels
                multi=True,
                placeholder="Select experience levels..."
            )
        ])
    ], className="filter-card mb-3")


def create_job_freshness_filter():
    """Create job posting date filter"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-calendar-alt me-2"),
            html.Strong("Posted Date")
        ]),
        dbc.CardBody([
            dbc.RadioItems(
                id="job-freshness-filter",
                options=[
                    {"label": "📅 Today", "value": "today"},
                    {"label": "📆 This Week", "value": "week"},
                    {"label": "🗓️ This Month", "value": "month"},
                    {"label": "📅 Last 3 Months", "value": "3months"},
                    {"label": "🕒 Any Time", "value": "any"}
                ],
                value="month",  # Default to this month
                inline=False
            )
        ])
    ], className="filter-card mb-3")


def create_company_size_filter():
    """Create company size filter"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-users me-2"),
            html.Strong("Company Size")
        ]),
        dbc.CardBody([
            dbc.Checklist(
                id="company-size-filter",
                options=[
                    {"label": "🚀 Startup (1-50)", "value": "startup"},
                    {"label": "🏢 Small (51-200)", "value": "small"},
                    {"label": "🏗️ Medium (201-1000)", "value": "medium"},
                    {"label": "🏙️ Large (1000+)", "value": "large"}
                ],
                value=["startup", "small", "medium", "large"],
                inline=False,
                switch=True
            )
        ])
    ], className="filter-card mb-3")


def create_application_status_filter():
    """Create application status filter"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-tasks me-2"),
            html.Strong("Application Status")
        ]),
        dbc.CardBody([
            dbc.Checklist(
                id="application-status-filter",
                options=[
                    {"label": "🆕 Not Applied", "value": "new"},
                    {"label": "🔖 Bookmarked", "value": "bookmarked"},
                    {"label": "📤 Applied", "value": "applied"},
                    {"label": "📞 Interview", "value": "interview"},
                    {"label": "✅ Offer", "value": "offer"},
                    {"label": "❌ Rejected", "value": "rejected"}
                ],
                value=["new", "bookmarked"],  # Focus on actionable jobs
                inline=False,
                switch=True
            )
        ])
    ], className="filter-card mb-3")


def create_quick_filters():
    """Create quick filter buttons for common searches"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-bolt me-2"),
            html.Strong("Quick Filters")
        ]),
        dbc.CardBody([
            dbc.ButtonGroup([
                dbc.Button(
                    [html.I(className="fas fa-home me-1"), "Remote Only"],
                    id="quick-filter-remote",
                    color="outline-success",
                    size="sm"
                ),
                dbc.Button(
                    [html.I(className="fas fa-dollar-sign me-1"), "High Pay"],
                    id="quick-filter-high-pay",
                    color="outline-primary",
                    size="sm"
                ),
                dbc.Button(
                    [html.I(className="fas fa-calendar-day me-1"), "New Today"],
                    id="quick-filter-new",
                    color="outline-warning",
                    size="sm"
                )
            ], className="d-flex flex-wrap gap-1")
        ])
    ], className="filter-card mb-3")


def create_search_box():
    """Create enhanced search box with autocomplete"""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-search me-2"),
            html.Strong("Search Jobs")
        ]),
        dbc.CardBody([
            dbc.InputGroup([
                dbc.Input(
                    id="job-search-input",
                    placeholder="Search by title, company, skills...",
                    type="text"
                ),
                dbc.Button(
                    [html.I(className="fas fa-search")],
                    id="job-search-button",
                    color="primary",
                    n_clicks=0
                )
            ]),
            html.Div(id="search-suggestions", className="mt-2")
        ])
    ], className="filter-card mb-3")


def create_filter_panel():
    """Create complete filter panel for job search"""
    return html.Div([
        # Search box at top
        create_search_box(),
        
        # Quick filters
        create_quick_filters(),
        
        # Main filters
        create_salary_range_filter(),
        create_location_type_filter(),
        create_experience_level_filter(),
        create_job_freshness_filter(),
        create_company_size_filter(),
        create_application_status_filter(),
        
        # Filter actions
        dbc.Card([
            dbc.CardBody([
                dbc.ButtonGroup([
                    dbc.Button(
                        [html.I(className="fas fa-filter me-1"), "Apply Filters"],
                        id="apply-filters-btn",
                        color="primary",
                        className="flex-fill"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-undo me-1"), "Reset"],
                        id="reset-filters-btn",
                        color="outline-secondary"
                    )
                ], className="w-100")
            ])
        ], className="filter-card")
    ], className="filter-panel")


def create_filter_summary():
    """Create active filters summary display"""
    return html.Div([
        html.H6("Active Filters:", className="mb-2"),
        html.Div(id="active-filters-display", className="filter-summary"),
        html.Small(
            id="filter-results-count",
            className="text-muted mt-2 d-block"
        )
    ], className="mb-3")

