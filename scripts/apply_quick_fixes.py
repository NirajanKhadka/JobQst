"""
JobQst Startup Speed Optimizer
Apply immediate performance fixes
"""

# Quick Fix 1: Update main.py to use Dash instead of Streamlit
import re

def update_main_py_references():
    """Replace Streamlit references with Dash"""
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Replace Streamlit references
    content = content.replace(
        'streamlit run src/dashboard/unified_dashboard.py',
        'python src/dashboard/dash_app/app.py'
    )
    
    content = content.replace(
        'Dashboard: For visual interface, launch: streamlit run',
        'Dashboard: For visual interface, launch: python'
    )
    
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated main.py Streamlit → Dash references")

# Quick Fix 2: Add feature flags for heavy imports
def create_feature_flags():
    """Create feature flags to disable heavy ML imports"""
    feature_config = """
# JobQst Feature Flags
# Set to False to disable heavy ML features and speed up startup

ENABLE_AI_ANALYSIS = False  # Disable by default for faster startup
ENABLE_TRANSFORMERS = False  # Only enable if actually needed
ENABLE_PYTORCH = False  # Personal projects don't need this by default
ENABLE_TENSORFLOW = False  # Most users won't need this

# Basic features (always enabled)
ENABLE_BASIC_ANALYSIS = True
ENABLE_DASH_DASHBOARD = True  # Keep Dash enabled
ENABLE_STREAMLIT = False  # Disable Streamlit to avoid confusion
"""
    
    with open('config/features.py', 'w') as f:
        f.write(feature_config)
    
    print("✅ Created feature flags config")

# Quick Fix 3: Database connection optimization
def optimize_sqlite_settings():
    """Add SQLite optimization wrapper"""
    sqlite_optimizer = '''
import sqlite3
import logging

logger = logging.getLogger(__name__)

def optimize_sqlite_connection(db_path):
    """Apply performance optimizations to SQLite"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Speed optimizations
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL") 
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    
    conn.commit()
    return conn

def get_optimized_connection(db_path):
    """Get optimized database connection"""
    try:
        return optimize_sqlite_connection(db_path)
    except Exception as e:
        logger.warning(f"Could not optimize SQLite: {e}")
        return sqlite3.connect(db_path)
'''
    
    with open('src/utils/db_optimizer.py', 'w') as f:
        f.write(sqlite_optimizer)
    
    print("✅ Created database optimizer")

if __name__ == "__main__":
    print("🚀 Applying JobQst Quick Performance Fixes...")
    
    update_main_py_references()
    create_feature_flags() 
    optimize_sqlite_settings()
    
    print("\n✅ Quick fixes applied!")
    print("\nNext steps:")
    print("1. Restart JobQst - should be faster now")
    print("2. Use 'python src/dashboard/dash_app/app.py' for dashboard") 
    print("3. AI features disabled by default (edit config/features.py to enable)")
