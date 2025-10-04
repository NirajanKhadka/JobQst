"""
Enhanced chart components for JobQst Dashboard
Beautiful, professional visualizations
"""

import plotly.graph_objects as go
import pandas as pd
import logging
from src.dashboard.analytics import compute_company_stats

logger = logging.getLogger(__name__)


def create_job_funnel_chart(jobs_data):
    """Create a funnel chart showing job application pipeline"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "status" not in df.columns:
            return create_empty_chart("Status data not available")

        # Define the funnel stages
        funnel_stages = [
            ("Total Jobs", len(df)),
            ("Ready to Apply", len(df[df["status"] == "ready_to_apply"])),
            ("Applied", len(df[df["status"] == "applied"])),
            ("Interview", len(df[df["status"] == "interview"])),
            ("Offer", len(df[df["status"] == "offer"])),
        ]

        # Filter out stages with 0 values for cleaner visualization
        funnel_stages = [(stage, count) for stage, count in funnel_stages if count > 0]

        stages, values = zip(*funnel_stages)

        fig = go.Figure(
            go.Funnel(
                y=stages,
                x=values,
                textinfo="value+percent initial",
                marker=dict(color=["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6"]),
            )
        )

        fig.update_layout(
            title="Job Application Pipeline",
            template="plotly_white",
            height=400,
            font=dict(size=12),
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating funnel chart: {e}")
        return create_empty_chart("Error creating chart")


def create_success_rate_gauge(jobs_data):
    """Create a gauge chart showing application success rate"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "status" not in df.columns:
            return create_empty_chart("Status data not available")

        total_jobs = len(df)
        applied_jobs = len(df[df["status"] == "applied"])

        success_rate = (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=success_rate,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Application Success Rate (%)"},
                delta={"reference": 20},  # Target success rate
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "#2ecc71"},
                    "steps": [
                        {"range": [0, 20], "color": "#e74c3c"},
                        {"range": [20, 50], "color": "#f39c12"},
                        {"range": [50, 80], "color": "#3498db"},
                        {"range": [80, 100], "color": "#2ecc71"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 90,
                    },
                },
            )
        )

        fig.update_layout(
            template="plotly_white", height=300, font={"color": "darkblue", "family": "Arial"}
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating gauge chart: {e}")
        return create_empty_chart("Error creating chart")


def create_match_score_radar(jobs_data):
    """Create radar chart showing match scores by category"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "match_score" not in df.columns:
            return create_empty_chart("Match score data not available")

        # Create categories based on match score ranges
        categories = [
            "Excellent (90-100%)",
            "Very Good (80-89%)",
            "Good (70-79%)",
            "Fair (60-69%)",
            "Poor (0-59%)",
        ]

        # Count jobs in each category
        excellent = len(df[df["match_score"] >= 90])
        very_good = len(df[(df["match_score"] >= 80) & (df["match_score"] < 90)])
        good = len(df[(df["match_score"] >= 70) & (df["match_score"] < 80)])
        fair = len(df[(df["match_score"] >= 60) & (df["match_score"] < 70)])
        poor = len(df[df["match_score"] < 60])

        values = [excellent, very_good, good, fair, poor]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill="toself",
                name="Job Distribution",
                line_color="#3498db",
                fillcolor="rgba(52, 152, 219, 0.3)",
            )
        )

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, range=[0, max(values) * 1.1] if max(values) > 0 else [0, 10]
                )
            ),
            showlegend=True,
            title="Match Score Distribution",
            template="plotly_white",
            height=400,
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating radar chart: {e}")
        return create_empty_chart("Error creating chart")


def create_activity_heatmap(jobs_data):
    """Create heatmap showing job search activity by day/time"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "created_at" not in df.columns:
            return create_empty_chart("Date data not available")

        df["created_at"] = pd.to_datetime(df["created_at"])
        df["day"] = df["created_at"].dt.day_name()
        df["hour"] = df["created_at"].dt.hour

        # Create pivot table for heatmap
        activity_matrix = df.groupby(["day", "hour"]).size().unstack(fill_value=0)

        # Reorder days
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        activity_matrix = activity_matrix.reindex(day_order)

        fig = go.Figure(
            data=go.Heatmap(
                z=activity_matrix.values,
                x=activity_matrix.columns,
                y=activity_matrix.index,
                colorscale="Blues",
                hoverongaps=False,
                hovertemplate="Day: %{y}<br>Hour: %{x}<br>Jobs: %{z}<extra></extra>",
            )
        )

        fig.update_layout(
            title="Job Search Activity Heatmap",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week",
            template="plotly_white",
            height=400,
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating heatmap: {e}")
        return create_empty_chart("Error creating chart")


def create_company_treemap(jobs_data):
    """Create treemap showing job distribution by company"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "company" not in df.columns:
            return create_empty_chart("Company data not available")

        # Use shared aggregation helper
        company_stats = compute_company_stats(df, top_n=15)
        company_counts = pd.Series(company_stats.counts, index=company_stats.companies)

        fig = go.Figure(
            go.Treemap(
                labels=company_counts.index,
                values=company_counts.values,
                parents=[""] * len(company_counts),
                textinfo="label+value",
                hovertemplate="Company: %{label}<br>Jobs: %{value}<extra></extra>",
                marker=dict(colorscale="Viridis", cmid=company_counts.median()),
            )
        )

        fig.update_layout(title="Jobs by Company", template="plotly_white", height=400)

        return fig

    except Exception as e:
        logger.error(f"Error creating treemap: {e}")
        return create_empty_chart("Error creating chart")


def create_empty_chart(message="No data available"):
    """Create an empty chart with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font=dict(size=16, color="gray"),
    )
    fig.update_layout(
        template="plotly_white", height=400, xaxis=dict(visible=False), yaxis=dict(visible=False)
    )
    return fig


def create_performance_metrics_chart(jobs_data):
    """Create comprehensive performance metrics chart"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        # Calculate various metrics
        metrics = {
            "Total Jobs": len(df),
            "Applied": len(df[df["status"] == "applied"]) if "status" in df.columns else 0,
            "High Match (>80%)": (
                len(df[df["match_score"] > 80]) if "match_score" in df.columns else 0
            ),
            "Recent (Last 7d)": 0,  # Would need date logic
            "Top Companies": df["company"].nunique() if "company" in df.columns else 0,
        }

        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(metrics.keys()),
                    y=list(metrics.values()),
                    marker_color=["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6"],
                )
            ]
        )

        fig.update_layout(
            title="Job Search Performance Metrics",
            xaxis_title="Metrics",
            yaxis_title="Count",
            template="plotly_white",
            height=400,
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating performance chart: {e}")
        return create_empty_chart("Error creating chart")
