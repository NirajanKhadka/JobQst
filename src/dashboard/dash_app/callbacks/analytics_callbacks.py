"""
Analytics callbacks for JobQst Dashboard
Handle chart updates and analytics visualizations
"""

import logging
from dash import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.dashboard.analytics import (
    compute_company_stats,
    compute_location_stats,
    compute_job_metrics,
)

logger = logging.getLogger(__name__)


def register_analytics_callbacks(app):
    """Register all analytics-related callbacks"""

    @app.callback(
        [
            Output("success-rate-kpi", "children"),
            Output("avg-match-kpi", "children"),
            Output("companies-kpi", "children"),
            Output("active-days-kpi", "children"),
        ],
        Input("jobs-data-store", "data"),
    )
    def update_kpi_metrics(jobs_data):
        """Update KPI metrics cards"""
        try:
            if not jobs_data:
                return "0%", "0%", "0", "0"

            df = pd.DataFrame(jobs_data)

            # Use shared aggregation helpers
            job_metrics = compute_job_metrics(df)
            company_stats = compute_company_stats(df)

            # Calculate metrics
            total_jobs = job_metrics.total_jobs
            applied_jobs = job_metrics.status_counts.get("applied", 0)
            success_rate = (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0

            avg_match_score = job_metrics.avg_match_score

            companies_count = company_stats.total_companies

            # Calculate active days
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"])
                date_range = df["created_at"].max() - df["created_at"].min()
                active_days = date_range.days + 1
            else:
                active_days = 0

            return (
                f"{success_rate:.1f}%",
                f"{avg_match_score:.0f}%",
                f"{companies_count:,}",
                f"{active_days}",
            )

        except Exception as e:
            logger.error(f"Error updating KPI metrics: {e}")
            return "Error", "Error", "Error", "Error"

    @app.callback(Output("jobs-timeline-chart", "figure"), Input("jobs-data-store", "data"))
    def update_timeline_chart(jobs_data):
        """Update jobs over time chart"""
        try:
            if not jobs_data:
                return create_empty_chart("No data available")

            df = pd.DataFrame(jobs_data)

            if "created_at" not in df.columns:
                return create_empty_chart("No date information available")

            df["created_at"] = pd.to_datetime(df["created_at"])
            df["date"] = df["created_at"].dt.date

            # Group by date and count jobs
            timeline_data = df.groupby("date").size().reset_index(name="count")
            timeline_data["cumulative"] = timeline_data["count"].cumsum()

            fig = go.Figure()

            # Add daily jobs bar chart
            fig.add_trace(
                go.Bar(
                    x=timeline_data["date"],
                    y=timeline_data["count"],
                    name="Daily Jobs",
                    marker_color="#3498db",
                    opacity=0.7,
                )
            )

            # Add cumulative line
            fig.add_trace(
                go.Scatter(
                    x=timeline_data["date"],
                    y=timeline_data["cumulative"],
                    name="Cumulative",
                    line=dict(color="#e74c3c", width=3),
                    yaxis="y2",
                )
            )

            fig.update_layout(
                title="Jobs Over Time",
                xaxis_title="Date",
                yaxis=dict(title="Daily Jobs", side="left"),
                yaxis2=dict(title="Cumulative Jobs", side="right", overlaying="y"),
                hovermode="x unified",
                template="plotly_white",
                height=400,
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating timeline chart: {e}")
            return create_empty_chart(f"Error: {str(e)}")

    @app.callback(Output("status-pie-chart", "figure"), Input("jobs-data-store", "data"))
    def update_status_pie_chart(jobs_data):
        """Update status distribution pie chart"""
        try:
            if not jobs_data:
                return create_empty_chart("No data available")

            df = pd.DataFrame(jobs_data)

            if "status" not in df.columns:
                return create_empty_chart("No status information available")

            # Use shared aggregation helper
            job_metrics = compute_job_metrics(df)
            status_counts = job_metrics.status_counts

            # Color mapping for statuses
            colors = {
                "new": "#3498db",
                "ready_to_apply": "#27ae60",
                "applied": "#f39c12",
                "needs_review": "#e74c3c",
                "filtered_out": "#95a5a6",
            }

            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Job Status Distribution",
                color_discrete_map=colors,
            )

            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(template="plotly_white", height=400, showlegend=True)

            return fig

        except Exception as e:
            logger.error(f"Error creating status pie chart: {e}")
            return create_empty_chart(f"Error: {str(e)}")

    @app.callback(Output("companies-bar-chart", "figure"), Input("jobs-data-store", "data"))
    def update_companies_chart(jobs_data):
        """Update top companies bar chart"""
        try:
            if not jobs_data:
                return create_empty_chart("No data available")

            df = pd.DataFrame(jobs_data)

            if "company" not in df.columns:
                return create_empty_chart("No company information available")

            # Use shared aggregation helper
            company_stats = compute_company_stats(df, top_n=10)
            company_counts = pd.Series(company_stats.counts, index=company_stats.companies)

            fig = px.bar(
                x=company_counts.values,
                y=company_counts.index,
                orientation="h",
                title="Top Companies",
                labels={"x": "Number of Jobs", "y": "Company"},
                color=company_counts.values,
                color_continuous_scale="Blues",
            )

            fig.update_layout(
                template="plotly_white",
                height=400,
                yaxis={"categoryorder": "total ascending"},
                showlegend=False,
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating companies chart: {e}")
            return create_empty_chart(f"Error: {str(e)}")

    @app.callback(Output("location-bar-chart", "figure"), Input("jobs-data-store", "data"))
    def update_location_chart(jobs_data):
        """Update location distribution chart"""
        try:
            if not jobs_data:
                return create_empty_chart("No data available")

            df = pd.DataFrame(jobs_data)

            if "location" not in df.columns:
                return create_empty_chart("No location information available")

            # Use shared aggregation helper
            location_stats = compute_location_stats(df, top_n=10)
            location_counts = pd.Series(location_stats.counts, index=location_stats.locations)

            fig = px.bar(
                x=location_counts.index,
                y=location_counts.values,
                title="Top Locations",
                labels={"x": "Location", "y": "Number of Jobs"},
                color=location_counts.values,
                color_continuous_scale="Greens",
            )

            fig.update_layout(
                template="plotly_white", height=400, xaxis_tickangle=-45, showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating location chart: {e}")
            return create_empty_chart(f"Error: {str(e)}")

    @app.callback(Output("match-score-histogram", "figure"), Input("jobs-data-store", "data"))
    def update_match_score_histogram(jobs_data):
        """Update match score distribution histogram"""
        try:
            if not jobs_data:
                return create_empty_chart("No data available")

            df = pd.DataFrame(jobs_data)

            if "match_score" not in df.columns:
                return create_empty_chart("No match score information available")

            fig = px.histogram(
                df,
                x="match_score",
                nbins=20,
                title="Match Score Distribution",
                labels={"match_score": "Match Score (%)", "count": "Number of Jobs"},
                color_discrete_sequence=["#3498db"],
            )

            # Add vertical line for average
            avg_score = df["match_score"].mean()
            fig.add_vline(
                x=avg_score,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Avg: {avg_score:.1f}%",
            )

            fig.update_layout(template="plotly_white", height=400, bargap=0.1)

            return fig

        except Exception as e:
            logger.error(f"Error creating match score histogram: {e}")
            return create_empty_chart(f"Error: {str(e)}")


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
