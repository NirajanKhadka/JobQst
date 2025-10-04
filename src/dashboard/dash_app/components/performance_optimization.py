"""
Performance Optimization Components for JobQst Dashboard
Client-side filtering, pagination, and loading states
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def create_pagination_component(page_size=25, total_items=0):
    """Create pagination component for job listings"""
    total_pages = max(1, (total_items + page_size - 1) // page_size)

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                [html.I(className="fas fa-angle-double-left")],
                                                id="pagination-first",
                                                size="sm",
                                                outline=True,
                                                disabled=True,
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-angle-left")],
                                                id="pagination-prev",
                                                size="sm",
                                                outline=True,
                                                disabled=True,
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-angle-right")],
                                                id="pagination-next",
                                                size="sm",
                                                outline=True,
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-angle-double-right")],
                                                id="pagination-last",
                                                size="sm",
                                                outline=True,
                                            ),
                                        ]
                                    )
                                ],
                                width="auto",
                            ),
                            dbc.Col(
                                [
                                    html.Span(
                                        id="pagination-info", children=f"Page 1 of {total_pages}"
                                    )
                                ],
                                width="auto",
                                className="d-flex align-items-center px-3",
                            ),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id="page-size-selector",
                                        options=[
                                            {"label": "10 per page", "value": 10},
                                            {"label": "25 per page", "value": 25},
                                            {"label": "50 per page", "value": 50},
                                            {"label": "100 per page", "value": 100},
                                        ],
                                        value=page_size,
                                        clearable=False,
                                        style={"width": "150px"},
                                    )
                                ],
                                width="auto",
                            ),
                        ],
                        justify="between",
                        className="align-items-center",
                    )
                ]
            )
        ],
        className="shadow-sm border-0 mb-3",
    )


def create_loading_overlay():
    """Create loading overlay for async operations"""
    return html.Div(
        [
            dbc.Spinner(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-search fa-2x text-primary mb-3"),
                            html.H5("Processing jobs...", className="text-primary"),
                            html.P(
                                "Please wait while we fetch the latest job data",
                                className="text-muted mb-0",
                            ),
                        ],
                        className="text-center",
                    )
                ],
                size="lg",
                spinner_style={"width": "3rem", "height": "3rem"},
            )
        ],
        id="jobs-loading-overlay",
        className="position-fixed top-0 start-0 w-100 h-100 "
        "d-flex align-items-center justify-content-center",
        style={"background-color": "rgba(0,0,0,0.7)", "z-index": "9999", "display": "none"},
    )


def create_client_side_filters():
    """Create client-side filtering controls"""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6(
                        [html.I(className="fas fa-filter me-2"), "Quick Filters"], className="mb-0"
                    )
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Company", className="fw-semibold"),
                                    dcc.Dropdown(
                                        id="filter-company",
                                        placeholder="Filter by company...",
                                        multi=True,
                                        options=[],
                                        style={"font-size": "14px"},
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Location", className="fw-semibold"),
                                    dcc.Dropdown(
                                        id="filter-location",
                                        placeholder="Filter by location...",
                                        multi=True,
                                        options=[],
                                        style={"font-size": "14px"},
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Job Type", className="fw-semibold"),
                                    dcc.Dropdown(
                                        id="filter-job-type",
                                        placeholder="Filter by type...",
                                        multi=True,
                                        options=[
                                            {"label": "Full-time", "value": "full-time"},
                                            {"label": "Part-time", "value": "part-time"},
                                            {"label": "Contract", "value": "contract"},
                                            {"label": "Remote", "value": "remote"},
                                        ],
                                        style={"font-size": "14px"},
                                    ),
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Salary Range", className="fw-semibold"),
                                    dcc.RangeSlider(
                                        id="filter-salary-range",
                                        min=30000,
                                        max=200000,
                                        step=10000,
                                        value=[50000, 150000],
                                        marks={
                                            30000: "$30K",
                                            75000: "$75K",
                                            125000: "$125K",
                                            200000: "$200K+",
                                        },
                                        tooltip={"placement": "bottom"},
                                    ),
                                ],
                                width=3,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-search me-2"), "Apply Filters"],
                                        id="apply-filters-btn",
                                        color="primary",
                                        size="sm",
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-times me-2"), "Clear All"],
                                        id="clear-filters-btn",
                                        color="outline-secondary",
                                        size="sm",
                                        className="ms-2",
                                    ),
                                ],
                                width=12,
                                className="text-end",
                            )
                        ]
                    ),
                ]
            ),
        ],
        className="shadow-sm border-0 mb-3",
    )


def create_performance_metrics():
    """Create performance metrics display"""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6(
                        [html.I(className="fas fa-tachometer-alt me-2"), "Performance Metrics"],
                        className="mb-0",
                    )
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small("Load Time", className="text-muted"),
                                            html.H6(
                                                id="load-time-metric",
                                                children="--ms",
                                                className="mb-0 text-success",
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small("Jobs Displayed", className="text-muted"),
                                            html.H6(
                                                id="jobs-count-metric",
                                                children="0",
                                                className="mb-0 text-info",
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small("Cache Hit Rate", className="text-muted"),
                                            html.H6(
                                                id="cache-hit-metric",
                                                children="--",
                                                className="mb-0 text-warning",
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small("Memory Usage", className="text-muted"),
                                            html.H6(
                                                id="memory-usage-metric",
                                                children="--MB",
                                                className="mb-0 text-primary",
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                        ]
                    )
                ]
            ),
        ],
        className="shadow-sm border-0 mb-3",
    )


def register_performance_callbacks(app):
    """Register performance optimization callbacks"""
    try:

        @app.callback(
            [
                Output("pagination-info", "children"),
                Output("pagination-first", "disabled"),
                Output("pagination-prev", "disabled"),
                Output("pagination-next", "disabled"),
                Output("pagination-last", "disabled"),
            ],
            [
                Input("pagination-first", "n_clicks"),
                Input("pagination-prev", "n_clicks"),
                Input("pagination-next", "n_clicks"),
                Input("pagination-last", "n_clicks"),
                Input("page-size-selector", "value"),
            ],
            [State("jobs-data-store", "data")],
        )
        def update_pagination(
            first_clicks, prev_clicks, next_clicks, last_clicks, page_size, jobs_data
        ):
            """Update pagination state"""
            try:
                if not jobs_data:
                    return "Page 1 of 1", True, True, True, True

                total_jobs = len(jobs_data.get("jobs", []))
                total_pages = max(1, (total_jobs + page_size - 1) // page_size)

                # For now, assume page 1 (would need current page state)
                current_page = 1

                info_text = f"Page {current_page} of {total_pages}"

                # Determine button states
                is_first_page = current_page == 1
                is_last_page = current_page == total_pages

                return (info_text, is_first_page, is_first_page, is_last_page, is_last_page)

            except Exception as e:
                logger.error(f"Error updating pagination: {e}")
                return "Page 1 of 1", True, True, True, True

        @app.callback(
            [Output("filter-company", "options"), Output("filter-location", "options")],
            [Input("jobs-data-store", "data")],
        )
        def update_filter_options(jobs_data):
            """Update filter dropdown options based on available jobs"""
            try:
                if not jobs_data:
                    return [], []

                jobs = jobs_data.get("jobs", [])

                # Extract unique companies and locations
                companies = set()
                locations = set()

                for job in jobs:
                    if job.get("company"):
                        companies.add(job["company"])
                    if job.get("location"):
                        locations.add(job["location"])

                company_options = [
                    {"label": company, "value": company} for company in sorted(companies)
                ]

                location_options = [
                    {"label": location, "value": location} for location in sorted(locations)
                ]

                return company_options, location_options

            except Exception as e:
                logger.error(f"Error updating filter options: {e}")
                return [], []

        @app.callback(
            Output("jobs-loading-overlay", "style"),
            [Input("apply-filters-btn", "n_clicks"), Input("clear-filters-btn", "n_clicks")],
            prevent_initial_call=True,
        )
        def toggle_loading_overlay(apply_clicks, clear_clicks):
            """Show/hide loading overlay during filtering"""
            from dash import ctx

            try:
                if ctx.triggered:
                    # Show loading overlay briefly
                    return {
                        "background-color": "rgba(0,0,0,0.7)",
                        "z-index": "9999",
                        "display": "flex",
                    }

                return {"display": "none"}

            except Exception as e:
                logger.error(f"Error toggling loading overlay: {e}")
                return {"display": "none"}

        @app.callback(
            [
                Output("load-time-metric", "children"),
                Output("jobs-count-metric", "children"),
                Output("cache-hit-metric", "children"),
            ],
            [Input("auto-refresh-interval", "n_intervals")],
            [State("jobs-data-store", "data")],
        )
        def update_performance_metrics(n_intervals, jobs_data):
            """Update performance metrics display"""
            try:
                # Simulate load time (would be real in production)
                load_time = f"{150 + (n_intervals % 10) * 25}ms"

                # Count jobs
                jobs_count = len(jobs_data.get("jobs", [])) if jobs_data else 0

                # Simulate cache hit rate
                cache_hit = f"{85 + (n_intervals % 5) * 2}%"

                return load_time, str(jobs_count), cache_hit

            except Exception as e:
                logger.error(f"Error updating performance metrics: {e}")
                return "--ms", "0", "--%"

        logger.info("Performance optimization callbacks registered")

    except Exception as e:
        logger.error(f"Error registering performance callbacks: {e}")


# Utility functions for client-side operations
def filter_jobs_client_side(jobs: List[Dict], filters: Dict) -> List[Dict]:
    """Filter jobs on client side for better performance"""
    try:
        filtered_jobs = jobs.copy()

        # Filter by company
        if filters.get("companies"):
            filtered_jobs = [
                job for job in filtered_jobs if job.get("company") in filters["companies"]
            ]

        # Filter by location
        if filters.get("locations"):
            filtered_jobs = [
                job for job in filtered_jobs if job.get("location") in filters["locations"]
            ]

        # Filter by job type
        if filters.get("job_types"):
            filtered_jobs = [
                job
                for job in filtered_jobs
                if any(
                    jtype in job.get("description", "").lower() for jtype in filters["job_types"]
                )
            ]

        # Filter by salary range
        if filters.get("salary_range"):
            min_sal, max_sal = filters["salary_range"]
            # This would need salary parsing logic

        return filtered_jobs

    except Exception as e:
        logger.error(f"Error filtering jobs client-side: {e}")
        return jobs


def paginate_jobs(jobs: List[Dict], page: int, page_size: int) -> Dict:
    """Paginate jobs list for performance"""
    try:
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return {
            "jobs": jobs[start_idx:end_idx],
            "total": len(jobs),
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (len(jobs) + page_size - 1) // page_size),
        }

    except Exception as e:
        logger.error(f"Error paginating jobs: {e}")
        return {"jobs": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 1}
