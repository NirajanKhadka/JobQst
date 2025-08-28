"""
Emergency fixes for dashboard import errors and missing components
Run this script to quickly fix the most critical dashboard issues
"""

import os
import sys
from pathlib import Path

def fix_health_monitor_missing_classes():
    """Add missing HealthStatus enum to health_monitor.py"""
    health_monitor_path = Path("src/dashboard/services/health_monitor.py")
    
    missing_classes = '''
from enum import Enum

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ComponentHealth:
    """Component health data class"""
    def __init__(self, name: str, status: HealthStatus, message: str = ""):
        self.name = name
        self.status = status
        self.message = message
        self.timestamp = datetime.now()
'''
    
    # Read current content
    if health_monitor_path.exists():
        with open(health_monitor_path, 'r') as f:
            content = f.read()
        
        # Add missing classes at the top after imports
        if "class HealthStatus" not in content:
            # Insert after imports
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('logger = '):
                    import_end = i
                    break
            
            # Insert missing classes
            lines.insert(import_end + 1, missing_classes)
            
            # Write back
            with open(health_monitor_path, 'w') as f:
                f.write('\n'.join(lines))
            
            print("✅ Fixed HealthStatus class in health_monitor.py")
        else:
            print("ℹ️ HealthStatus class already exists")

def fix_orchestration_service_missing_classes():
    """Add missing ApplicationStatus enum to orchestration_service.py"""
    orchestration_path = Path("src/dashboard/services/orchestration_service.py")
    
    missing_classes = '''
from enum import Enum

class ApplicationStatus(Enum):
    """Application status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

class ServiceStatus:
    """Service status data class"""
    def __init__(self, name: str, status: ApplicationStatus, port: int = None):
        self.name = name
        self.status = status
        self.port = port
        self.timestamp = datetime.now()
'''
    
    if orchestration_path.exists():
        with open(orchestration_path, 'r') as f:
            content = f.read()
        
        if "class ApplicationStatus" not in content:
            # Add missing classes
            lines = content.split('\n')
            # Find import section end
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('logger = ') or line.startswith('class '):
                    import_end = i
                    break
            
            lines.insert(import_end, missing_classes)
            
            with open(orchestration_path, 'w') as f:
                f.write('\n'.join(lines))
            
            print("✅ Fixed ApplicationStatus class in orchestration_service.py")
        else:
            print("ℹ️ ApplicationStatus class already exists")

def fix_dashboard_api_imports():
    """Fix missing 'api' import in dashboard __init__.py"""
    dashboard_init = Path("src/dashboard/__init__.py")
    
    api_content = '''
# Dashboard API module imports
try:
    from .services import data_service, health_monitor, orchestration_service
    # Create api namespace for backward compatibility
    class APINamespace:
        """API namespace for dashboard services"""
        def __init__(self):
            self.data_service = data_service
            self.health_monitor = health_monitor  
            self.orchestration_service = orchestration_service
    
    api = APINamespace()
    
except ImportError as e:
    print(f"Warning: Could not import dashboard services: {e}")
    api = None
'''
    
    with open(dashboard_init, 'w') as f:
        f.write(api_content)
    
    print("✅ Fixed dashboard API imports")

def create_missing_header_component():
    """Create missing header component"""
    components_dir = Path("src/dashboard/components")
    components_dir.mkdir(exist_ok=True)
    
    header_path = components_dir / "header.py"
    
    header_content = '''
"""
Dashboard header component
"""
import dash_bootstrap_components as dbc
from dash import html

def render_header(profile_name: str = "Default"):
    """Render dashboard header"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.NavbarBrand("JobQst Dashboard", className="ms-2")
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.Strong(f"Profile: {profile_name}"),
                        html.Br(),
                        html.Small("Job Discovery Platform")
                    ], className="text-end text-light")
                ], width=6)
            ], align="center", className="g-0")
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-3"
    )
'''
    
    with open(header_path, 'w') as f:
        f.write(header_content)
    
    print("✅ Created missing header component")

def main():
    """Run all emergency fixes"""
    print("🚨 Running JobQst Dashboard Emergency Fixes...")
    print("=" * 50)
    
    try:
        fix_health_monitor_missing_classes()
        fix_orchestration_service_missing_classes() 
        fix_dashboard_api_imports()
        create_missing_header_component()
        
        print("=" * 50)
        print("✅ All emergency fixes completed successfully!")
        print("🔄 Please run tests again: pytest tests/dashboard/ -v")
        
    except Exception as e:
        print(f"❌ Error during fixes: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
