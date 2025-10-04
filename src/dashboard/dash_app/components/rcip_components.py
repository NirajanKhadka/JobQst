"""
RCIP Dashboard Components
UI components for displaying RCIP badges, filters, and information.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, List, Any


def create_rcip_badge(is_rcip: bool = False, size: str = "sm") -> dbc.Badge:
    """
    Create an RCIP badge component.

    Args:
        is_rcip: Whether the job is in an RCIP city
        size: Badge size ('sm', 'md', 'lg')

    Returns:
        dbc.Badge component
    """
    if not is_rcip:
        return html.Span()

    return dbc.Badge(
        [html.I(className="fas fa-maple-leaf me-1"), "RCIP"],
        color="success",
        className=f"badge-{size} me-2",
        title="Regional and Community Immigration Program City",
    )


def create_immigration_priority_badge(is_priority: bool = False) -> dbc.Badge:
    """
    Create an immigration priority badge.

    Args:
        is_priority: Whether the job is in an immigration priority city

    Returns:
        dbc.Badge component
    """
    if not is_priority:
        return html.Span()

    return dbc.Badge(
        [html.I(className="fas fa-star me-1"), "Immigration Priority"],
        color="info",
        className="badge-sm me-2",
        title="Immigration Priority City",
    )


def create_rcip_filter_controls() -> dbc.Card:
    """
    Create RCIP filter controls for the dashboard.

    Returns:
        dbc.Card with filter controls
    """
    return dbc.Card(
        [
            dbc.CardHeader([html.I(className="fas fa-filter me-2"), "Immigration Filters"]),
            dbc.CardBody(
                [
                    dbc.Checklist(
                        id="rcip-filter-checklist",
                        options=[
                            {
                                "label": html.Span(
                                    [
                                        html.I(className="fas fa-maple-leaf me-2 text-success"),
                                        "RCIP Cities Only",
                                    ]
                                ),
                                "value": "rcip_only",
                            },
                            {
                                "label": html.Span(
                                    [
                                        html.I(className="fas fa-star me-2 text-info"),
                                        "Immigration Priority",
                                    ]
                                ),
                                "value": "immigration_priority",
                            },
                        ],
                        value=[],
                        inline=False,
                        switch=True,
                        className="mb-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-sort me-2"), "Prioritize RCIP Jobs"],
                        id="rcip-sort-button",
                        color="success",
                        outline=True,
                        size="sm",
                        className="w-100",
                    ),
                ]
            ),
        ],
        className="mb-3",
    )


def create_rcip_stats_card(rcip_count: int, total_count: int) -> dbc.Card:
    """
    Create RCIP statistics card.

    Args:
        rcip_count: Number of RCIP jobs
        total_count: Total number of jobs

    Returns:
        dbc.Card with RCIP statistics
    """
    percentage = (rcip_count / total_count * 100) if total_count > 0 else 0

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-maple-leaf fa-2x text-success mb-2"),
                            html.H4(f"{rcip_count}", className="mb-0"),
                            html.P("RCIP Jobs", className="text-muted mb-1"),
                            dbc.Progress(
                                value=percentage,
                                color="success",
                                className="mb-1",
                                style={"height": "4px"},
                            ),
                            html.Small(f"{percentage:.1f}% of total", className="text-muted"),
                        ],
                        className="text-center",
                    )
                ]
            )
        ],
        className="shadow-sm",
    )


def create_rcip_info_modal() -> dbc.Modal:
    """
    Create information modal about RCIP program.

    Returns:
        dbc.Modal with RCIP information
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [html.I(className="fas fa-maple-leaf me-2 text-success"), "About RCIP Cities"]
                )
            ),
            dbc.ModalBody(
                [
                    html.P(
                        [
                            "The ",
                            html.Strong("Regional and Community Immigration Program (RCIP)"),
                            " targets jobs in specific Canadian cities and regions that are actively ",
                            "seeking skilled workers through immigration programs.",
                        ]
                    ),
                    html.H6("Why RCIP Cities Matter:", className="mt-3 mb-2"),
                    html.Ul(
                        [
                            html.Li("Easier pathways to permanent residence"),
                            html.Li("Lower cost of living compared to major cities"),
                            html.Li("Strong community support for newcomers"),
                            html.Li("Growing tech and professional opportunities"),
                            html.Li("Provincial nominee program advantages"),
                        ]
                    ),
                    html.H6("Included Regions:", className="mt-3 mb-2"),
                    html.Ul(
                        [
                            html.Li("Atlantic Canada: Halifax, Moncton, Charlottetown, St. John's"),
                            html.Li("Prairie Provinces: Winnipeg, Saskatoon, Regina"),
                            html.Li("Northern Ontario: Thunder Bay, Sudbury, Sault Ste. Marie"),
                            html.Li("Interior BC: Kelowna, Kamloops, Prince George"),
                            html.Li("Quebec (outside Montreal): Quebec City, Sherbrooke, Gatineau"),
                        ]
                    ),
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Jobs in RCIP cities receive a ranking boost in this dashboard to help ",
                            "you discover opportunities with immigration advantages.",
                        ],
                        color="info",
                        className="mt-3",
                    ),
                ]
            ),
            dbc.ModalFooter(dbc.Button("Close", id="rcip-info-modal-close", className="ms-auto")),
        ],
        id="rcip-info-modal",
        size="lg",
        is_open=False,
    )


def create_rcip_city_tag(city_tags: List[str]) -> html.Div:
    """
    Create city tag badges from city_tags list.

    Args:
        city_tags: List of city tag strings

    Returns:
        html.Div with tag badges
    """
    if not city_tags:
        return html.Div()

    if isinstance(city_tags, str):
        city_tags = city_tags.split(",")

    badge_map = {
        "rcip": ("success", "fas fa-maple-leaf", "RCIP"),
        "immigration_priority": ("info", "fas fa-star", "Immigration Priority"),
        "tech_hub": ("primary", "fas fa-laptop-code", "Tech Hub"),
        "major_city": ("secondary", "fas fa-city", "Major City"),
        "atlantic_canada": ("info", "fas fa-water", "Atlantic"),
        "prairie_province": ("warning", "fas fa-tractor", "Prairie"),
        "remote": ("dark", "fas fa-home", "Remote"),
    }

    badges = []
    for tag in city_tags:
        tag = tag.strip().lower()
        if tag in badge_map:
            color, icon, label = badge_map[tag]
            badges.append(
                dbc.Badge(
                    [html.I(className=f"{icon} me-1"), label],
                    color=color,
                    className="badge-sm me-1",
                    pill=True,
                )
            )

    return html.Div(badges, className="d-flex flex-wrap gap-1")


def create_rcip_summary_section(summary_data: Dict[str, Any]) -> dbc.Card:
    """
    Create RCIP summary section for analytics dashboard.

    Args:
        summary_data: Dictionary with RCIP statistics

    Returns:
        dbc.Card with RCIP summary
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [html.I(className="fas fa-map-marked-alt me-2"), "RCIP & Immigration Insights"]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H4(
                                        summary_data.get("total_rcip_jobs", 0),
                                        className="text-success mb-0",
                                    ),
                                    html.P("RCIP Jobs", className="text-muted small"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.H4(
                                        summary_data.get("total_immigration_priority", 0),
                                        className="text-info mb-0",
                                    ),
                                    html.P("Immigration Priority", className="text-muted small"),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.H4(
                                        f"{summary_data.get('rcip_percentage', 0):.1f}%",
                                        className="text-warning mb-0",
                                    ),
                                    html.P("RCIP Coverage", className="text-muted small"),
                                ],
                                width=4,
                            ),
                        ]
                    ),
                    html.Hr(),
                    dbc.Button(
                        [html.I(className="fas fa-info-circle me-2"), "Learn About RCIP"],
                        id="rcip-info-button",
                        color="success",
                        outline=True,
                        size="sm",
                        className="w-100",
                    ),
                ]
            ),
        ],
        className="mb-3",
    )
