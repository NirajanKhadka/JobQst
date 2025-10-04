"""
Salary Analyzer Component
Visualizes salary trends and market position.
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Any, Optional


def create_salary_analyzer(salary_data: Dict[str, Any], user_target_salary: Optional[float] = None) -> dbc.Card:
    """
    Create salary analysis card with trends and market position.
    
    Args:
        salary_data: Dictionary with salary statistics from MarketAnalyzer
        user_target_salary: User's target salary for comparison
        
    Returns:
        Dash Bootstrap Card component
    """
    if not salary_data or salary_data.get('count', 0) == 0:
        return _create_empty_salary_card()
    
    avg_salary = salary_data.get('average', 0)
    median_salary = salary_data.get('median', 0)
    min_salary = salary_data.get('min', 0)
    max_salary = salary_data.get('max', 0)
    
    # Calculate market position if user target provided
    market_position = None
    position_color = 'secondary'
    position_text = ''
    
    if user_target_salary and avg_salary > 0:
        diff_pct = ((user_target_salary - avg_salary) / avg_salary) * 100
        
        if diff_pct > 20:
            position_color = 'success'
            position_text = f'Above Market (+{abs(diff_pct):.0f}%)'
        elif diff_pct < -20:
            position_color = 'warning'
            position_text = f'Below Market ({diff_pct:.0f}%)'
        else:
            position_color = 'info'
            position_text = 'At Market Rate'
        
        market_position = {
            'color': position_color,
            'text': position_text,
            'diff_pct': diff_pct
        }
    
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.I(className="fas fa-dollar-sign me-2 text-success"),
                    html.Strong("Salary Analysis"),
                ],
                className="bg-light"
            ),
            dbc.CardBody(
                [
                    # Salary range visualization
                    html.Div(
                        [
                            html.H6("Market Salary Range", className="text-muted mb-3"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("Minimum", className="text-muted d-block"),
                                                    html.H5(
                                                        f"${min_salary:,.0f}",
                                                        className="mb-0 text-secondary"
                                                    ),
                                                ],
                                                className="text-center"
                                            )
                                        ],
                                        width=3
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("Average", className="text-muted d-block"),
                                                    html.H4(
                                                        f"${avg_salary:,.0f}",
                                                        className="mb-0 text-primary"
                                                    ),
                                                ],
                                                className="text-center"
                                            )
                                        ],
                                        width=3
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("Median", className="text-muted d-block"),
                                                    html.H5(
                                                        f"${median_salary:,.0f}",
                                                        className="mb-0 text-info"
                                                    ),
                                                ],
                                                className="text-center"
                                            )
                                        ],
                                        width=3
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("Maximum", className="text-muted d-block"),
                                                    html.H5(
                                                        f"${max_salary:,.0f}",
                                                        className="mb-0 text-success"
                                                    ),
                                                ],
                                                className="text-center"
                                            )
                                        ],
                                        width=3
                                    ),
                                ],
                                className="mb-3"
                            ),
                            # Visual range bar
                            html.Div(
                                [
                                    html.Div(
                                        style={
                                            'height': '8px',
                                            'background': 'linear-gradient(to right, #6c757d, #0d6efd, #20c997)',
                                            'borderRadius': '4px',
                                            'position': 'relative'
                                        }
                                    ),
                                ],
                                className="mb-3"
                            ),
                        ]
                    ),
                    
                    html.Hr(),
                    
                    # Market position indicator (if user target provided)
                    (
                        html.Div(
                            [
                                html.H6("Your Market Position", className="text-muted mb-2"),
                                dbc.Alert(
                                    [
                                        html.Div(
                                            [
                                                html.Strong(f"Target: ${user_target_salary:,.0f}"),
                                                html.Span(
                                                    f" • {market_position['text']}",
                                                    className="ms-2"
                                                ),
                                            ]
                                        ),
                                    ],
                                    color=market_position['color'],
                                    className="mb-0"
                                ),
                            ]
                        ) if market_position else html.Div()
                    ),
                    
                    # Salary distribution
                    html.Div(
                        [
                            html.H6("Salary Distribution", className="text-muted mt-3 mb-2"),
                            html.Div(
                                [
                                    _create_distribution_bar(dist)
                                    for dist in salary_data.get('distribution', [])
                                ]
                            )
                        ]
                    ) if salary_data.get('distribution') else html.Div(),
                    
                    # Stats footer
                    html.Div(
                        [
                            html.Small(
                                f"Based on {salary_data.get('count', 0)} jobs with salary information",
                                className="text-muted"
                            )
                        ],
                        className="mt-3 text-center"
                    ),
                ]
            ),
        ],
        className="shadow-sm h-100 professional-card"
    )


def _create_distribution_bar(dist: Dict[str, Any]) -> html.Div:
    """Create a single distribution bar."""
    return html.Div(
        [
            html.Div(
                [
                    html.Span(dist['range'], className="small"),
                    html.Span(
                        f"{dist['count']} jobs ({dist['percentage']}%)",
                        className="small text-muted float-end"
                    ),
                ],
                className="d-flex justify-content-between mb-1"
            ),
            dbc.Progress(
                value=dist['percentage'],
                max=100,
                color="primary",
                className="mb-2",
                style={'height': '6px'}
            ),
        ]
    )


def _create_empty_salary_card() -> dbc.Card:
    """Create empty state card when no salary data available."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.I(className="fas fa-dollar-sign me-2 text-muted"),
                    html.Strong("Salary Analysis"),
                ],
                className="bg-light"
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(className="fas fa-chart-line fa-3x text-muted mb-3"),
                            html.P(
                                "No salary data available",
                                className="text-muted mb-0"
                            ),
                            html.Small(
                                "Salary information will appear here when jobs with salary data are available",
                                className="text-muted"
                            ),
                        ],
                        className="text-center py-4"
                    )
                ]
            ),
        ],
        className="shadow-sm h-100"
    )
