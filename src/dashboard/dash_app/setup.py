"""
Setup script for the Dash dashboard
Run this script to set up and start the dashboard
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_requirements():
    """Install required packages"""
    try:
        requirements_file = Path(__file__).parent / "requirements.txt"
        if not requirements_file.exists():
            logger.error("requirements.txt not found")
            return False
        
        logger.info("Installing requirements...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Requirements installed successfully")
            return True
        else:
            logger.error(f"Failed to install requirements: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        # Import here to avoid circular imports
        sys.path.append(str(Path(__file__).parent.parent.parent.parent))
        from src.core.user_profile_manager import UserProfileManager
        
        # Try to create a profile manager instance
        UserProfileManager()
        logger.info("Database connection - OK")
        return True
        
    except Exception as e:
        logger.warning(f"Database connection issue: {e}")
        logger.info("Dashboard will run with limited functionality")
        return False

def create_directories():
    """Create necessary directories"""
    try:
        base_dir = Path(__file__).parent
        directories = [
            base_dir / "logs",
            base_dir / "assets" / "exports",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    try:
        # Set default environment variables if not present
        env_vars = {
            'DASH_DEBUG': 'True',
            'DASH_HOST': '127.0.0.1',
            'DASH_PORT': '8050',
            'DASH_LOG_LEVEL': 'INFO'
        }
        
        for var, default in env_vars.items():
            if var not in os.environ:
                os.environ[var] = default
                logger.info(f"Set {var}={default}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        return False

def run_dashboard():
    """Run the dashboard application"""
    try:
        app_file = Path(__file__).parent / "app.py"
        if not app_file.exists():
            logger.error("app.py not found")
            return False
        
        logger.info("Starting dashboard...")
        logger.info(f"Dashboard will be available at http://{os.environ.get('DASH_HOST', '127.0.0.1')}:{os.environ.get('DASH_PORT', '8050')}")
        
        # Import and run the app
        sys.path.insert(0, str(Path(__file__).parent))
        from app import dashboard
        
        try:
            dashboard.app.run(
                host=os.environ.get('DASH_HOST', '127.0.0.1'),
                port=int(os.environ.get('DASH_PORT', '8050')),
                debug=os.environ.get('DASH_DEBUG', 'True').lower() == 'true'
            )
        except AttributeError:
            # Fallback for older Dash versions
            dashboard.app.run_server(
                host=os.environ.get('DASH_HOST', '127.0.0.1'),
                port=int(os.environ.get('DASH_PORT', '8050')),
                debug=os.environ.get('DASH_DEBUG', 'True').lower() == 'true'
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        return False

def main():
    """Main setup and run function"""
    logger.info("Setting up JobLens Dash Dashboard...")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        logger.error("Failed to create directories")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        logger.error("Failed to setup environment")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        logger.error("Failed to install requirements")
        sys.exit(1)
    
    # Check database (optional)
    check_database_connection()
    
    # Run dashboard
    logger.info("Setup complete! Starting dashboard...")
    if not run_dashboard():
        logger.error("Failed to start dashboard")
        sys.exit(1)

if __name__ == "__main__":
    main()