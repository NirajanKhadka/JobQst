"""
Jobs callbacks for JobLens Dashboard
Handle job management interactions
"""
import logging
from dash import Input, Output, no_update, callback_context, State, html
import pandas as pd

logger = logging.getLogger(__name__)


def apply_job_filters(df, search_term, company_filter, status_filter,
                      start_date, end_date):
    """Apply filters to the jobs dataframe"""
    filtered_df = df.copy()
    
    if search_term:
        mask = (
            filtered_df['title'].str.contains(search_term,
                                              case=False, na=False) |
            filtered_df['company'].str.contains(search_term,
                                                case=False, na=False) |
            filtered_df['location'].str.contains(search_term,
                                                 case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if company_filter and company_filter != 'all':
        filtered_df = filtered_df[filtered_df['company'] == company_filter]
    
    if status_filter and status_filter != 'all':
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if start_date and end_date:
        filtered_df['created_at'] = pd.to_datetime(
            filtered_df['created_at']
        )
        filtered_df = filtered_df[
            (filtered_df['created_at'] >= start_date) &
            (filtered_df['created_at'] <= end_date)
        ]
    
    return filtered_df


def calculate_job_metrics(df):
    """Calculate job metrics for dashboard"""
    total_jobs = len(df)
    new_jobs = len(df[df['status'] == 'new'])
    ready_jobs = len(df[df['status'] == 'ready_to_apply'])
    applied_jobs = len(df[df['status'] == 'applied'])
    
    return (
        f"{total_jobs:,}",
        f"{new_jobs:,}",
        f"{ready_jobs:,}",
        f"{applied_jobs:,}"
    )


def format_table_data(df):
    """Format dataframe for table display"""
    return df.to_dict('records')


def register_jobs_callbacks(app):
    """Register all jobs-related callbacks"""
    
    # Data loading callback
    @app.callback(
        Output('jobs-data-store', 'data'),
        [Input('profile-store', 'data'),
         Input('auto-refresh-interval', 'n_intervals'),
         Input('jobs-refresh-btn', 'n_clicks')],
        prevent_initial_call=False
    )
    def load_jobs_data(profile_data, n_intervals, refresh_clicks):
        """Load jobs data for current profile"""
        try:
            # Try different import methods for data_loader
            try:
                from ..utils.data_loader import DataLoader
            except ImportError:
                try:
                    from src.dashboard.dash_app.utils.data_loader import (
                        DataLoader
                    )
                except ImportError:
                    # Create sample data if DataLoader not available
                    logger.warning(
                        "DataLoader not available, using sample data"
                    )
                    return [
                        {
                            'id': 1,
                            'title': 'Software Engineer',
                            'company': 'Tech Corp',
                            'location': 'San Francisco, CA',
                            'status': 'new',
                            'salary': '$80,000 - $120,000',
                            'match_score': 85,
                            'confidence_badge': '🟢 HIGH',
                            'semantic_score': 0.85,
                            'validation_method': '🤖 AI Semantic',
                            'posted_date': '2024-08-18',
                            'created_at': '2024-08-18',
                            'description': 'Software Engineer Python/React',
                            'job_url': ('https://example.com/jobs/'
                                        'software-engineer-1'),
                        },
                        {
                            'id': 2,
                            'title': 'Data Scientist',
                            'company': 'Data Inc',
                            'location': 'New York, NY',
                            'status': 'ready_to_apply',
                            'salary': '$90,000 - $140,000',
                            'match_score': 92,
                            'confidence_badge': '🟢 HIGH',
                            'semantic_score': 0.92,
                            'validation_method': '✅ Exact Match',
                            'posted_date': '2024-08-17',
                            'created_at': '2024-08-17',
                            'description': 'Data Scientist ML/Python',
                            'job_url': ('https://example.com/jobs/'
                                        'data-scientist-2'),
                        },
                        {
                            'id': 3,
                            'title': 'Frontend Developer',
                            'company': 'Web Solutions',
                            'location': 'Toronto, ON',
                            'status': 'applied',
                            'salary': '$70,000 - $95,000',
                            'match_score': 78,
                            'confidence_badge': '🟡 MEDIUM',
                            'semantic_score': 0.78,
                            'validation_method': '🔍 Partial',
                            'posted_date': '2024-08-16',
                            'created_at': '2024-08-16',
                            'description': 'Frontend React/TypeScript',
                            'job_url': ('https://example.com/jobs/'
                                        'frontend-developer-3')
                        }
                    ]
            
            # Use profile name attached to app if available
            profile_name = getattr(app, 'profile_name', 'Nirajan')
            if hasattr(app, 'profile_name') and app.profile_name:
                profile_name = app.profile_name
            
            data_loader = DataLoader()
            df = data_loader.load_jobs_data(profile_name)
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error loading jobs data: {e}")
            return []
    
    @app.callback(
        [Output('jobs-table', 'data'),
         Output('total-jobs-metric', 'children'),
         Output('new-jobs-metric', 'children'),
         Output('ready-jobs-metric', 'children'),
         Output('applied-jobs-metric', 'children')],
        [Input('jobs-data-store', 'data'),
         Input('jobs-search', 'value'),
         Input('jobs-company-filter', 'value'),
         Input('jobs-status-filter', 'value'),
         Input('jobs-date-filter', 'start_date'),
         Input('jobs-date-filter', 'end_date')]
    )
    def update_jobs_table(jobs_data, search_term, company_filter,
                          status_filter, start_date, end_date):
        """Update the jobs table based on filters"""
        try:
            if not jobs_data:
                return [], "0", "0", "0", "0"
            
            df = pd.DataFrame(jobs_data)
            filtered_df = apply_job_filters(
                df, search_term, company_filter, status_filter,
                start_date, end_date
            )
            metrics = calculate_job_metrics(df)
            table_data = format_table_data(filtered_df)
            
            return table_data, *metrics
            
        except Exception as e:
            logger.error(f"Error updating jobs table: {e}")
            return [], "Error", "Error", "Error", "Error"
    
    @app.callback(
        Output('jobs-company-filter', 'options'),
        Input('jobs-data-store', 'data')
    )
    def update_company_filter_options(jobs_data):
        """Update company filter dropdown options"""
        try:
            if not jobs_data:
                return [{'label': 'All Companies', 'value': 'all'}]
            
            df = pd.DataFrame(jobs_data)
            companies = sorted(df['company'].dropna().unique())
            
            options = [{'label': 'All Companies', 'value': 'all'}]
            options.extend([
                {'label': company, 'value': company}
                for company in companies
            ])
            
            return options
            
        except Exception as e:
            logger.error(f"Error updating company options: {e}")
            return [{'label': 'All Companies', 'value': 'all'}]
    
    @app.callback(
        [Output('table-view', 'style'),
         Output('card-view', 'style'),
         Output('table-view-btn', 'active'),
         Output('card-view-btn', 'active')],
        [Input('table-view-btn', 'n_clicks'),
         Input('card-view-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def toggle_view_mode(table_clicks, card_clicks):
        """Toggle between table and card view"""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'table-view-btn':
            return {'display': 'block'}, {'display': 'none'}, True, False
        elif button_id == 'card-view-btn':
            return {'display': 'none'}, {'display': 'block'}, False, True
        
        return no_update
    
    @app.callback(
        Output('jobs-cards-container', 'children'),
        Input('jobs-data-store', 'data')
    )
    def update_jobs_cards(jobs_data):
        """Update jobs card view"""
        try:
            if not jobs_data:
                return "No jobs available"
            
            from ..layouts.jobs_layout import create_job_card
            import dash_bootstrap_components as dbc
            
            cards = []
            for job in jobs_data[:12]:  # Show first 12 jobs
                cards.append(
                    dbc.Col(
                        create_job_card(job),
                        width=6,
                        lg=4,
                        className="mb-3"
                    )
                )
            
            return dbc.Row(cards)
            
        except Exception as e:
            logger.error(f"Error updating jobs cards: {e}")
            return f"Error loading jobs cards: {e}"

    # Job modal callbacks removed - using direct links for job viewing

    # Job tracking tabs callback
    @app.callback(
        Output('job-tracking-content', 'children'),
        Input('job-status-tabs', 'active_tab'),
        State('jobs-data-store', 'data')
    )
    def update_job_tracking_content(active_tab, jobs_data):
        """Update content based on selected status tab"""
        if not jobs_data:
            return html.P("No jobs data available", className="text-muted")
        
        df = pd.DataFrame(jobs_data)
        
        if active_tab == "scraped":
            filtered_df = df[df['status'] == 'scraped']
            title = "🔍 Scraped Jobs"
        elif active_tab == "processed":
            filtered_df = df[df['status'] == 'processed']
            title = "⚙️ Processed Jobs"
        elif active_tab == "applied":
            filtered_df = df[df['status'] == 'applied']
            title = "✅ Applied Jobs"
        else:
            filtered_df = df
            title = "📊 All Jobs"
        
        return html.Div([
            html.H5(f"{title} ({len(filtered_df)} jobs)"),
            html.P(f"Status breakdown: {len(filtered_df)} out of "
                   f"{len(df)} total jobs",
                   className="text-muted")
        ])

    # CSV Export callback
    @app.callback(
        Output('jobs-csv-download', 'data'),
        Input('export-jobs-btn', 'n_clicks'),
        [State('jobs-table', 'data'),
         State('jobs-table', 'derived_virtual_data'),
         State('profile-store', 'data')],
        prevent_initial_call=True
    )
    def export_jobs_to_csv(export_clicks, table_data,
                           filtered_data, profile_data):
        """Export jobs data to CSV file"""
        if not export_clicks:
            return no_update
            
        try:
            # Use filtered data if available, otherwise use all table data
            export_data = filtered_data if filtered_data else table_data
            
            if not export_data:
                return no_update
                
            # Import the export function
            try:
                from ..utils.formatters import export_jobs_to_csv
            except ImportError:
                # Fallback export function
                df = pd.DataFrame(export_data)
                
                # Remove action columns and clean data
                if 'actions' in df.columns:
                    df = df.drop('actions', axis=1)
                    
                # Format dates
                date_columns = ['created_at', 'updated_at', 'scraped_at']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(
                            df[col], errors='coerce'
                        ).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                csv_string = df.to_csv(index=False)
                
                # Generate filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                profile_name = (profile_data.get('name', 'jobs')
                                if profile_data else 'jobs')
                filename = f"JobLens_{profile_name}_export_{timestamp}.csv"
                
                return {
                    "content": csv_string,
                    "filename": filename,
                    "type": "text/csv"
                }
            
            # Use the utility function if available
            csv_string = export_jobs_to_csv(export_data)
            if csv_string:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                profile_name = (profile_data.get('name', 'jobs')
                                if profile_data else 'jobs')
                filename = f"JobLens_{profile_name}_export_{timestamp}.csv"
                
                return {
                    "content": csv_string,
                    "filename": filename,
                    "type": "text/csv"
                }
            else:
                return no_update
                
        except Exception as e:
            logger.error(f"Error exporting jobs to CSV: {e}")
            return no_update
