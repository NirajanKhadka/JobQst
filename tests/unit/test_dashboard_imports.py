#!/usr/bin/env python3
"""
Test script to check dashboard import issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 Testing dashboard imports...")

try:
    print("✅ Testing basic imports...")
    import streamlit as st

    print("  ✅ streamlit")

    import pandas as pd

    print("  ✅ pandas")

    from datetime import datetime

    print("  ✅ datetime")

    print("\n🔍 Testing project imports...")

    # Test core imports
    try:
        from src.core.job_database import get_job_db
        from src.core.duckdb_database import DuckDBJobDatabase

        print("  ✅ job_database")
    except ImportError as e:
        print(f"  ❌ job_database: {e}")

    # Test utils imports
    try:
        from src.utils.profile_helpers import get_available_profiles

        print("  ✅ profile_helpers")
    except ImportError as e:
        print(f"  ❌ profile_helpers: {e}")

    # Test dashboard services
    try:
        from src.dashboard.services import get_data_service

        print("  ✅ dashboard services")
    except ImportError as e:
        print(f"  ❌ dashboard services: {e}")

    # Test dashboard components
    try:
        from src.dashboard.components.base import BaseComponent

        print("  ✅ dashboard components")
    except ImportError as e:
        print(f"  ❌ dashboard components: {e}")

    print("\n🔍 Testing data service...")
    try:
        data_service = get_data_service()
        health = data_service.get_health_status()
        print(f"  ✅ Data service health: {health['status']}")
    except Exception as e:
        print(f"  ❌ Data service error: {e}")

    print("\n✅ All critical imports successful!")

except Exception as e:
    print(f"❌ Critical import error: {e}")
    import traceback

    print(traceback.format_exc())
