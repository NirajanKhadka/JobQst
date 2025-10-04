"""
Advanced Search Component for Job Browser
Implements debounced search, sort dropdown, and advanced filters panel
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Optional


def create_enhanced_search_bar(placeholder: str = "Search jobs, companies, skills...") -> dbc.InputGroup:
    """
    Create enhanced search bar with debounced input (500ms).
    
    Args:
        placeholder: Placeholder text for search input
    
    Returns:
        dbc.InputGroup with search input and button
    """
    return dbc.InputGroup([
        dbc.InputGroupText(html.I(className="fas fa-search")),
        dbc.Input(
            id="enhanced-search-input",
            placeholder=placeholder,
            type="text",
            debounce=True,  # Enables debouncing
            className="form-control-lg"
        ),
        dbc.Button(
            [html.I(className="fas fa-search me-2"), "Search"],
            id="enhanced-search-button",
            color="primary",
            className="px-4"
        )
    ], className="mb-3")


def create_sort_dropdown() -> html.Div:
    """
    Create sort dropdown with multiple sorting options.
    
    Returns:
        html.Div containing sort dropdown
    """
    return html.Div([
        html.Label("Sort by:", className="me-2 fw-semibold"),
        dcc.Dropdown(
            id="enhanced-sort-dropdown",
            options=[
                {"label": "🎯 Best Match", "value": "match_desc"},
                {"label": "🆕 Newest First", "value": "date_desc"},
                {"label": "💰 Highest Salary", "value": "salary_desc"},
                {"label": "🏢 Company A-Z", "value": "company_asc"},
                {"label": "🍁 RCIP Priority", "value": "rcip_priority"},
            ],
            value="match_desc",
            clearable=False,
            className="w-100",
            style={"minWidth": "200px"}
        )
    ], className="d-flex align-items-center mb-3")


def create_advanced_filters_panel(collapsed: bool = False) -> dbc.Card:
    """
    Create collapsible advanced filters panel with sliders and checkboxes.
    
    Args:
        collapsed: Whether panel should start collapsed
    
    Returns:
        dbc.Card containing advanced filters
    """
    return dbc.Card([
        dbc.CardHeader([
            dbc.Button(
                [
                    html.I(id="filter-panel-icon", className="fas fa-chevron-down me-2"),
                    "Advanced Filters"
                ],
                id="filter-panel-toggle",
                color="link",
                className="text-decoration-none w-100 text-start p-0"
            )
        ]),
        dbc.Collapse([
            dbc.CardBody([
                # Match Score Range Slider
                html.Div([
                    html.Label("⭐ Match Score Range", className="fw-semibold mb-2"),
                    dcc.RangeSlider(
                        id="match-score-range-slider",
                        min=0,
                        max=100,
                        step=5,
                        value=[0, 100],
                        marks={
                            0: "0%",
                            25: "25%",
                            50: "50%",
                            75: "75%",
                            100: "100%"
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="mb-4"
                    )
                ], className="mb-4"),
                
                # Salary Range Slider
                html.Div([
                    html.Label("💰 Salary Range (CAD)", className="fw-semibold mb-2"),
                    dcc.RangeSlider(
                        id="salary-range-slider",
                        min=40000,
                        max=150000,
                        step=5000,
                        value=[40000, 150000],
                        marks={
                            40000: "$40K",
                            70000: "$70K",
                            100000: "$100K",
                            130000: "$130K",
                            150000: "$150K"
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="mb-4"
                    )
                ], className="mb-4"),
                
                # Location Type Checkboxes
                html.Div([
                    html.Label("📍 Work Location Type", className="fw-semibold mb-2"),
                    dbc.Checklist(
                        id="location-type-checkboxes",
                        options=[
                            {"label": " Remote", "value": "remote"},
                            {"label": " Hybrid", "value": "hybrid"},
                            {"label": " On-site", "value": "onsite"}
                        ],
                        value=["remote", "hybrid", "onsite"],
                        inline=False,
                        switch=True,
                        className="mb-3"
                    )
                ], className="mb-4"),
                
                # RCIP Filter
                html.Div([
                    html.Label("🍁 RCIP Cities", className="fw-semibold mb-2"),
                    dbc.Checklist(
                        id="rcip-filter-checkbox",
                        options=[
                            {"label": " RCIP Cities Only", "value": "rcip_only"}
                        ],
                        value=[],
                        inline=False,
                        switch=True,
                        className="mb-3"
                    )
                ], className="mb-4"),
                
                # Date Posted Filter
                html.Div([
                    html.Label("📅 Posted Within", className="fw-semibold mb-2"),
                    dcc.Dropdown(
                        id="date-posted-dropdown",
                        options=[
                            {"label": "Any time", "value": "all"},
                            {"label": "Last 24 hours", "value": "1"},
                            {"label": "Last 3 days", "value": "3"},
                            {"label": "Last 7 days", "value": "7"},
                            {"label": "Last 30 days", "value": "30"}
                        ],
                        value="all",
                        clearable=False,
                        className="mb-3"
                    )
                ], className="mb-3"),
                
                # Clear Filters Button
                dbc.Button(
                    [html.I(className="fas fa-times me-2"), "Clear All Filters"],
                    id="clear-advanced-filters-btn",
                    color="secondary",
                    outline=True,
                    className="w-100"
                )
            ])
        ], id="filter-panel-collapse", is_open=not collapsed)
    ], className="professional-card mb-3")


def create_search_results_header(total_results: int = 0, search_term: Optional[str] = None) -> html.Div:
    """
    Create search results header showing count and search term.
    
    Args:
        total_results: Number of results found
        search_term: Current search term
    
    Returns:
        html.Div with results header
    """
    if search_term:
        header_text = f"Found {total_results} jobs matching '{search_term}'"
    else:
        header_text = f"Showing {total_results} jobs"
    
    return html.Div([
        html.H5(header_text, className="mb-0"),
        html.Small(
            "Tip: Use advanced filters to narrow your search",
            className="text-muted"
        )
    ], className="mb-3 pb-3 border-bottom")


def create_loading_state() -> html.Div:
    """
    Create loading state for search results.
    
    Returns:
        html.Div with loading spinner
    """
    return html.Div([
        dbc.Spinner(
            html.Div([
                html.I(className="fas fa-search fa-3x text-muted mb-3"),
                html.H5("Searching jobs...", className="text-muted")
            ], className="text-center py-5"),
            color="primary"
        )
    ])


def create_no_results_state(search_term: Optional[str] = None) -> html.Div:
    """
    Create no results state.
    
    Args:
        search_term: Current search term
    
    Returns:
        html.Div with no results message
    """
    if search_term:
        message = f"No jobs found matching '{search_term}'"
        suggestion = "Try different keywords or adjust your filters"
    else:
        message = "No jobs found"
        suggestion = "Try adjusting your filters or run a new job search"
    
    return html.Div([
        dbc.Alert([
            html.I(className="fas fa-search fa-3x mb-3"),
            html.H4(message, className="alert-heading"),
            html.P(suggestion),
            html.Hr(),
            dbc.Button(
                [html.I(className="fas fa-sync-alt me-2"), "Clear Filters"],
                id="no-results-clear-btn",
                color="primary",
                outline=True
            )
        ], color="info", className="text-center")
    ], className="py-5")
