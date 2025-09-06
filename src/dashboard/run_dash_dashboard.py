#!/usr/bin/env python3
"""
JobQst Dash Dashboard Launcher
Run the professional Dash dashboard
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.dash_app.app import dashboard

if __name__ == '__main__':
    print("🚀 Starting JobQst Professional Dashboard...")
    print("📊 Open your browser to: http://localhost:8050")
    print("⚡ Features included:")
    print("   - Modern job management with DataTable")
    print("   - Beautiful analytics with Plotly charts")
    print("   - Real-time processing controls")
    print("   - System monitoring dashboard")
    print("   - Comprehensive settings panel")
    print("")
    
    try:
        dashboard.run(
            debug=True,
            host='0.0.0.0',
            port=8050
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("💡 Make sure you have installed the requirements:")
        print("   pip install -r src/dashboard/requirements_dash.txt")
