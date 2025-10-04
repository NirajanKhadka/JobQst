"""
Export Callbacks
Handle export functionality interactions
"""

import logging
import os
from datetime import datetime
from dash import Input, Output, State, no_update, ctx
from dash import html

logger = logging.getLogger(__name__)


def register_export_callbacks(app):
    """Register all export related callbacks."""

    @app.callback(
        Output("export-modal", "is_open"),
        [
            Input("export-btn", "n_clicks"),
            Input("export-excel-btn", "n_clicks"),
            Input("export-csv-btn", "n_clicks"),
            Input("export-json-btn", "n_clicks"),
            Input("export-cancel-btn", "n_clicks"),
            Input("export-confirm-btn", "n_clicks"),
        ],
        [State("export-modal", "is_open")],
    )
    def toggle_export_modal(
        export_btn, excel_btn, csv_btn, json_btn, cancel_btn, confirm_btn, is_open
    ):
        """Toggle export modal based on button clicks."""
        try:
            if not ctx.triggered:
                return no_update

            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # Open modal for any export button
            export_buttons = ["export-btn", "export-excel-btn", "export-csv-btn", "export-json-btn"]
            if trigger_id in export_buttons:
                return True

            # Close modal for cancel or confirm
            elif trigger_id in ["export-cancel-btn", "export-confirm-btn"]:
                return False

            return is_open

        except Exception as e:
            logger.error(f"Error toggling export modal: {str(e)}")
            return is_open

    @app.callback(
        [Output("export-format-radio", "value"), Output("export-summary", "children")],
        [
            Input("export-excel-btn", "n_clicks"),
            Input("export-csv-btn", "n_clicks"),
            Input("export-json-btn", "n_clicks"),
            Input("export-fields-checklist", "value"),
            Input("export-filters-checklist", "value"),
        ],
        [State("jobs-table-data", "data"), State("export-format-radio", "value")],
    )
    def update_export_options(
        excel_clicks,
        csv_clicks,
        json_clicks,
        selected_fields,
        selected_filters,
        jobs_data,
        current_format,
    ):
        """Update export format and summary based on selections."""
        try:
            # Determine format based on trigger
            export_format = current_format
            if ctx.triggered:
                trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
                if trigger_id == "export-excel-btn":
                    export_format = "excel"
                elif trigger_id == "export-csv-btn":
                    export_format = "csv"
                elif trigger_id == "export-json-btn":
                    export_format = "json"

            # Calculate summary
            if not jobs_data:
                summary = html.P("No jobs data available for export.", className="text-warning")
                return export_format, summary

            total_jobs = len(jobs_data)

            # Estimate filtered count
            filtered_count = total_jobs
            if selected_filters:
                if "bookmarked" in selected_filters:
                    bookmarked_count = sum(
                        1 for job in jobs_data if job.get("is_bookmarked", False)
                    )
                    filtered_count = min(filtered_count, bookmarked_count)

                if "applied" in selected_filters:
                    applied_count = sum(
                        1
                        for job in jobs_data
                        if job.get("application_status") in ["applied", "interview", "offer"]
                    )
                    filtered_count = min(filtered_count, applied_count)

                if "high_match" in selected_filters:
                    high_match_count = sum(
                        1 for job in jobs_data if job.get("match_score", 0) >= 80
                    )
                    filtered_count = min(filtered_count, high_match_count)

            # Create summary
            summary = html.Div(
                [
                    html.P(
                        [
                            html.Strong(f"📊 {filtered_count:,} jobs"),
                            f" will be exported from {total_jobs:,} total jobs",
                        ]
                    ),
                    html.P(
                        [
                            html.Strong(f"📋 {len(selected_fields or [])} field groups"),
                            " selected for export",
                        ]
                    ),
                    html.P([html.Strong(f"🔧 Format: "), export_format.upper()]),
                    html.P(
                        [
                            html.Strong(f"📁 File size estimate: "),
                            f"~{(filtered_count * 0.5):.1f} KB",
                        ],
                        className="small text-muted",
                    ),
                ]
            )

            return export_format, summary

        except Exception as e:
            logger.error(f"Error updating export options: {str(e)}")
            summary = html.P("Error calculating export summary.", className="text-danger")
            return current_format, summary

    @app.callback(
        [
            Output("export-toast", "is_open"),
            Output("export-toast", "children"),
            Output("export-toast", "header"),
            Output("export-toast", "icon"),
        ],
        [Input("export-confirm-btn", "n_clicks")],
        [
            State("jobs-table-data", "data"),
            State("export-format-radio", "value"),
            State("export-fields-checklist", "value"),
            State("export-filters-checklist", "value"),
        ],
    )
    def handle_export_confirm(
        confirm_clicks, jobs_data, export_format, selected_fields, selected_filters
    ):
        """Handle the actual export process."""
        try:
            if not confirm_clicks or not jobs_data:
                return no_update, no_update, no_update, no_update

            from ..components.export_component import (
                prepare_export_data,
                export_to_excel,
                export_to_csv,
                export_to_json,
            )

            try:
                # Prepare data
                if export_format in ["excel", "csv"]:
                    df = prepare_export_data(
                        jobs_data, selected_fields or [], selected_filters or []
                    )

                    if df.empty:
                        return (
                            True,
                            "No data to export with current filters.",
                            "Export Failed",
                            "danger",
                        )

                # Create exports directory if it doesn't exist
                exports_dir = "exports"
                os.makedirs(exports_dir, exist_ok=True)

                # Generate filename with timestamp
                from pathlib import Path

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                if export_format == "excel":
                    filename = str(Path(exports_dir) / f"jobqst_export_{timestamp}.xlsx")
                    export_to_excel(df, filename)
                    message = f"Excel file exported: {filename}"

                elif export_format == "csv":
                    filename = str(Path(exports_dir) / f"jobqst_export_{timestamp}.csv")
                    export_to_csv(df, filename)
                    message = f"CSV file exported: {filename}"

                elif export_format == "json":
                    filename = str(Path(exports_dir) / f"jobqst_export_{timestamp}.json")
                    # Apply filters to jobs_data for JSON export
                    filtered_jobs = jobs_data
                    if selected_filters:
                        if "bookmarked" in selected_filters:
                            filtered_jobs = [
                                job for job in filtered_jobs if job.get("is_bookmarked", False)
                            ]
                        if "applied" in selected_filters:
                            filtered_jobs = [
                                job
                                for job in filtered_jobs
                                if job.get("application_status")
                                in ["applied", "interview", "offer"]
                            ]
                        if "high_match" in selected_filters:
                            filtered_jobs = [
                                job for job in filtered_jobs if job.get("match_score", 0) >= 80
                            ]

                    export_to_json(filtered_jobs, filename)
                    message = f"JSON file exported: {filename}"

                return (
                    True,
                    html.Div(
                        [
                            html.P("✅ Export completed successfully!"),
                            html.Small(message, className="text-muted"),
                        ]
                    ),
                    "Export Successful",
                    "success",
                )

            except Exception as export_error:
                logger.error(f"Export failed: {str(export_error)}")
                return (
                    True,
                    html.Div(
                        [
                            html.P("❌ Export failed!"),
                            html.Small(f"Error: {str(export_error)}", className="text-danger"),
                        ]
                    ),
                    "Export Failed",
                    "danger",
                )

        except Exception as e:
            logger.error(f"Error in export confirm: {str(e)}")
            return (True, "An unexpected error occurred during export.", "Export Error", "danger")

    logger.info("Export callbacks registered successfully")
