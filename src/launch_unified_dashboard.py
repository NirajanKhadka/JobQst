#!/usr/bin/env python3
"""
Launch script for the Unified AutoJobAgent Dashboard
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("💡 Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def main():
    """Launch the unified dashboard."""
    print("🚀 AutoJobAgent - Unified Dashboard Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/dashboard/unified_dashboard.py").exists():
        print("❌ Please run this script from the project root directory")
        print("💡 Current directory should contain: src/dashboard/unified_dashboard.py")
        return 1
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        return 1
    
    print("✅ All dependencies found")
    
    # Check for existing Streamlit processes
    print("🔍 Checking for existing Streamlit processes...")
    try:
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        
        if ":8502" in result.stdout:
            print("⚠️  Port 8502 is already in use")
            response = input("Do you want to use port 8503 instead? (y/n): ")
            if response.lower() == 'y':
                port = 8503
            else:
                print("❌ Exiting to avoid port conflict")
                return 1
        else:
            port = 8502
            
    except Exception:
        # If netstat fails, just use default port
        port = 8502
    
    # Launch the dashboard
    print(f"🚀 Starting unified dashboard on port {port}...")
    print(f"🌐 Dashboard will be available at: http://localhost:{port}")
    print("💡 Press Ctrl+C to stop the dashboard")
    print("-" * 50)
    
    try:
        # Start Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "src/dashboard/unified_dashboard.py",
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
