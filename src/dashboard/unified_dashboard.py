#!/usr/bin/env python3
"""
JobQst Unified Dashboard
Main entry point for the dashboard - redirects to the appropriate dashboard implementation
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def launch_dashboard(profile_name: str, port=8050):
    """
    Launch the JobQst dashboard
    
    Args:
        profile_name: Profile name (required, not optional)
        port: Port to run dashboard on (default: 8050)
        
    Raises:
        ValueError: If profile_name is None or invalid
    """
    # Validate profile is provided and exists
    from src.dashboard.utils.profile_utils import require_profile
    
    try:
        profile_name = require_profile(profile_name)
    except ValueError as e:
        print(f"❌ {e}")
        return False
    
    print(f"🚀 Starting JobQst Dashboard for profile: {profile_name}")
    print(f"📊 Dashboard will be available at: http://localhost:{port}")

    try:
        # Import and configure the Dash app
        from src.dashboard.dash_app.app import dashboard, set_dashboard_profile

        # Set the profile for the dashboard
        set_dashboard_profile(profile_name)

        # Run the dashboard
        dashboard.run(debug=False, host="0.0.0.0", port=port)

    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("💡 Make sure you have installed the requirements:")
        print("   pip install -r src/dashboard/requirements_dash.txt")
        return False

    return True


def load_job_data(profile_name: str):
    """
    Load job data for the dashboard
    
    Args:
        profile_name: Profile name (required)
        
    Returns:
        DataFrame with job data or None on error
    """
    from src.dashboard.utils.profile_utils import require_profile
    
    try:
        profile_name = require_profile(profile_name)
        
        from src.dashboard.dash_app.utils.data_loader import DataLoader
        data_loader = DataLoader()
        return data_loader.load_jobs_data(profile_name)
    except ValueError as e:
        print(f"❌ {e}")
        return None
    except Exception as e:
        print(f"Error loading job data: {e}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JobQst Unified Dashboard")
    parser.add_argument("profile", help="Profile name (required)")
    parser.add_argument("--port", type=int, default=8050, help="Port to run dashboard on")

    args = parser.parse_args()

    launch_dashboard(args.profile, args.port)
