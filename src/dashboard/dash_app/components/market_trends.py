"""
Market Trends Component
Displays skills demand, top companies, and hiring trends.
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Any, List


def create_market_trends(
    skills_data: List[Dict[str, Any]],
    companies_data: List[Dict[str, Any]],
    trends_data: Dict[str, Any]
) -> html.Div:
    """
    Create market trends section with skills and companies.
    
    Args:
        skills_data: List of skills with demand metrics
        companies_data: List of top hiring companies
        trends_data: Hiring trend information
        
    Returns:
        Div containing market trends components
    """
    return html.Div(
        [
            dbc.Row(
                [
                    # Skills in demand
                    dbc.Col(
                        [
                            _create_skills_demand_card(skills_data)
                        ],
                        width=6
                    ),
                    # Top hiring companies
                    dbc.Col(
                        [
                            _create_top_companies_card(companies_data, trends_data)
                        ],
                        width=6
                    ),
                ],
                className="mb-4"
            ),
        ]
    )


def _create_skills_demand_card(skills_data: List[Dict[str, Any]]) -> dbc.Card:
    """Create skills in demand card."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.I(className="fas fa-code me-2 text-primary"),
                    html.Strong("Skills in Demand"),
                ],
                className="bg-light"
            ),
            dbc.CardBody(
                [
                    html.P(
                        "Most requested skills across all job postings",
                        className="text-muted small mb-3"
                    ),
                    html.Div(
                        [
                            _create_skill_badge(skill)
                            for skill in skills_data[:15]  # Top 15 skills
                        ] if skills_data else [
                            html.Div(
                                [
                                    html.I(className="fas fa-info-circle fa-2x text-muted mb-2"),
                                    html.P("No skills data available", className="text-muted mb-0"),
                                ],
                                className="text-center py-4"
                            )
                        ],
                        className="d-flex flex-wrap gap-2"
                    ),
                ]
            ),
        ],
        className="shadow-sm h-100 professional-card"
    )


def _create_skill_badge(skill: Dict[str, Any]) -> dbc.Badge:
    """Create a skill badge with color coding by priority."""
    priority = skill.get('priority', 'low')
    
    # Color mapping
    color_map = {
        'high': 'danger',
        'medium': 'warning',
        'low': 'secondary'
    }
    
    color = color_map.get(priority, 'secondary')
    
    return dbc.Badge(
        [
            html.Span(skill['skill'], className="me-1"),
            html.Span(
                f"{skill['percentage']}%",
                className="badge bg-light text-dark ms-1",
                style={'fontSize': '0.7em'}
            ),
        ],
        color=color,
        className="me-2 mb-2 px-3 py-2",
        style={'fontSize': '0.9em'}
    )


def _create_top_companies_card(
    companies_data: List[Dict[str, Any]],
    trends_data: Dict[str, Any]
) -> dbc.Card:
    """Create top hiring companies card."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.I(className="fas fa-building me-2 text-success"),
                    html.Strong("Top Hiring Companies"),
                ],
                className="bg-light"
            ),
            dbc.CardBody(
                [
                    # Hiring trend indicator
                    _create_trend_indicator(trends_data),
                    
                    html.Hr(className="my-3"),
                    
                    # Companies table
                    html.Div(
                        [
                            _create_company_row(company, idx + 1)
                            for idx, company in enumerate(companies_data[:10])  # Top 10
                        ] if companies_data else [
                            html.Div(
                                [
                                    html.I(className="fas fa-building fa-2x text-muted mb-2"),
                                    html.P("No company data available", className="text-muted mb-0"),
                                ],
                                className="text-center py-4"
                            )
                        ],
                        style={'maxHeight': '400px', 'overflowY': 'auto'}
                    ),
                ]
            ),
        ],
        className="shadow-sm h-100 professional-card"
    )


def _create_trend_indicator(trends_data: Dict[str, Any]) -> html.Div:
    """Create hiring trend indicator."""
    trend = trends_data.get('trend', 'stable')
    recent_activity = trends_data.get('recent_activity', 'moderate')
    weekly_avg = trends_data.get('weekly_average', 0)
    
    # Trend icon and color
    trend_config = {
        'growing': {'icon': 'fa-arrow-up', 'color': 'success', 'text': 'Growing'},
        'declining': {'icon': 'fa-arrow-down', 'color': 'danger', 'text': 'Declining'},
        'stable': {'icon': 'fa-minus', 'color': 'info', 'text': 'Stable'},
    }
    
    config = trend_config.get(trend, trend_config['stable'])
    
    # Activity color
    activity_colors = {
        'high': 'success',
        'moderate': 'info',
        'low': 'warning'
    }
    activity_color = activity_colors.get(recent_activity, 'secondary')
    
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(className=f"fas {config['icon']} me-2"),
                                    html.Strong(f"Market Trend: {config['text']}"),
                                ],
                                className=f"text-{config['color']}"
                            ),
                        ],
                        width=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        f"Activity: {recent_activity.title()} • Avg: {weekly_avg:.0f} jobs/week",
                                        className=f"text-{activity_color}"
                                    ),
                                ],
                                className="text-end"
                            ),
                        ],
                        width=6
                    ),
                ],
            ),
        ],
        className="mb-2"
    )


def _create_company_row(company: Dict[str, Any], rank: int) -> html.Div:
    """Create a single company row."""
    trend = company.get('trend', 'stable')
    trend_icon = 'fa-arrow-up' if trend == 'growing' else 'fa-minus'
    trend_color = 'success' if trend == 'growing' else 'secondary'
    
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Span(
                                f"#{rank}",
                                className="badge bg-light text-dark me-2",
                                style={'fontSize': '0.8em', 'minWidth': '30px'}
                            ),
                            html.Strong(company['company'], className="me-2"),
                            html.I(
                                className=f"fas {trend_icon} text-{trend_color}",
                                style={'fontSize': '0.8em'}
                            ),
                        ],
                        width=8,
                        className="d-flex align-items-center"
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Strong(
                                        f"{company['job_count']}",
                                        className="text-primary me-1"
                                    ),
                                    html.Small(
                                        f"({company['percentage']}%)",
                                        className="text-muted"
                                    ),
                                ],
                                className="text-end"
                            ),
                        ],
                        width=4
                    ),
                ],
                className="align-items-center"
            ),
        ],
        className="py-2 border-bottom hover-bg-light",
        style={'cursor': 'pointer'}
    )
