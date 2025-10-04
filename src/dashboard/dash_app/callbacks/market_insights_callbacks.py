"""
Market Insights Callbacks
Handles data updates for market analysis components.
"""

from dash import Input, Output, html
import logging
from typing import Optional

from src.dashboard.dash_app.utils.data_loader import DataLoader
from src.dashboard.dash_app.utils.market_analyzer import MarketAnalyzer
from src.dashboard.dash_app.components.salary_analyzer import create_salary_analyzer
from src.dashboard.dash_app.components.market_trends import create_market_trends

logger = logging.getLogger(__name__)


def register_market_insights_callbacks(app, profile_name: str):
    """Register market insights callbacks with profile context"""
    
    @app.callback(
        [
            Output("insights-total-jobs", "children"),
            Output("insights-companies", "children"),
            Output("insights-locations", "children"),
            Output("insights-rcip-jobs", "children")
        ],
        [
            Input("refresh-insights", "n_clicks"),
            Input("auto-refresh-interval", "n_intervals"),
        ],
        prevent_initial_call=False,
    )
    def update_market_insights_stats(n_clicks: int, n_intervals: int):
        """
        Update market insights statistics cards.
        
        Args:
            n_clicks: Refresh button clicks
            n_intervals: Auto-refresh intervals
            
        Returns:
            Tuple of (total_jobs, companies, locations, rcip_jobs)
        """
        try:
            # Load data
            data_loader = DataLoader(profile_name=profile_name)
            jobs_data = data_loader.get_jobs_data(profile_name)
            
            if not jobs_data:
                return "0", "0", "0", "0"
            
            # Calculate stats
            total_jobs = len(jobs_data)
            
            # Unique companies
            companies = set()
            for job in jobs_data:
                company = job.get("company") or job.get("company_name")
                if company:
                    companies.add(company)
            
            # Unique locations
            locations = set()
            for job in jobs_data:
                location = job.get("location")
                if location:
                    locations.add(location)
            
            # RCIP jobs
            rcip_jobs = sum(1 for job in jobs_data if job.get("is_rcip_city") or job.get("is_rcip"))
            
            return str(total_jobs), str(len(companies)), str(len(locations)), str(rcip_jobs)
        
        except Exception as e:
            logger.error(f"Error updating market insights stats: {e}")
            return "0", "0", "0", "0"
    
    
    @app.callback(
        Output("salary-analysis-container", "children"),
        [
            Input("refresh-insights", "n_clicks"),
            Input("auto-refresh-interval", "n_intervals"),
        ],
        prevent_initial_call=False,
    )
    def update_salary_analysis(n_clicks: int, n_intervals: int):
        """
        Update salary analysis section with market data.
        
        Args:
            n_clicks: Refresh button clicks
            n_intervals: Auto-refresh intervals
            
        Returns:
            Salary analyzer component
        """
        try:
            # Load data
            data_loader = DataLoader(profile_name=profile_name)
            jobs_data = data_loader.get_jobs_data(profile_name)
            
            if not jobs_data:
                logger.info("No jobs data available for salary analysis")
                return create_salary_analyzer({}, None)
            
            # Analyze market
            analyzer = MarketAnalyzer(jobs_data)
            salary_data = analyzer.calculate_salary_range()
            
            # Get user target salary from profile if available
            user_target_salary = None
            try:
                from src.core.user_profile_manager import UserProfileManager
                profile_manager = UserProfileManager()
                
                profile_data = profile_manager.load_profile(profile_name)
                
                # Try to get salary expectation
                salary_pref = profile_data.get("salary_expectation") or profile_data.get("target_salary")
                if salary_pref:
                    if isinstance(salary_pref, dict):
                        user_target_salary = salary_pref.get("min") or salary_pref.get("target")
                    elif isinstance(salary_pref, (int, float)):
                        user_target_salary = float(salary_pref)
            except Exception as e:
                logger.debug(f"Could not load user salary target: {e}")
            
            return create_salary_analyzer(salary_data, user_target_salary)
        
        except Exception as e:
            logger.error(f"Error updating salary analysis: {e}")
            return create_salary_analyzer({}, None)
    
    
    @app.callback(
        Output("market-trends-container", "children"),
        [
            Input("refresh-insights", "n_clicks"),
            Input("auto-refresh-interval", "n_intervals"),
        ],
        prevent_initial_call=False,
    )
    def update_market_trends(n_clicks: int, n_intervals: int):
        """
        Update market trends section with skills and companies data.
        
        Args:
            n_clicks: Refresh button clicks
            n_intervals: Auto-refresh intervals
            
        Returns:
            Market trends component
        """
        try:
            # Load data
            data_loader = DataLoader(profile_name=profile_name)
            jobs_data = data_loader.get_jobs_data(profile_name)
            
            if not jobs_data:
                logger.info("No jobs data available for market trends")
                return create_market_trends([], [], {'trend': 'stable', 'weekly_average': 0, 'recent_activity': 'low'})
            
            # Analyze market
            analyzer = MarketAnalyzer(jobs_data)
            skills_data = analyzer.analyze_skills_demand(15)
            companies_data = analyzer.get_top_hiring_companies(10)
            trends_data = analyzer.detect_hiring_trends()
            
            return create_market_trends(skills_data, companies_data, trends_data)
        
        except Exception as e:
            logger.error(f"Error updating market trends: {e}")
            return create_market_trends([], [], {'trend': 'stable', 'weekly_average': 0, 'recent_activity': 'low'})
