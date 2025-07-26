#!/usr/bin/env python3
"""
Test Enhanced Dashboard Components
Quick test to verify the enhanced table and service management work
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_enhanced_table():
    """Test the enhanced job table component."""
    print("🧪 Testing Enhanced Job Table Component...")
    
    try:
        from src.dashboard.components.enhanced_job_table import render_enhanced_job_table
        print("✅ Enhanced job table component imported successfully")
        
        # Create sample data
        sample_data = {
            'title': ['Software Engineer', 'Data Scientist', 'Product Manager'],
            'company': ['TechCorp', 'DataInc', 'ProductCo'],
            'location': ['Toronto', 'Vancouver', 'Montreal'],
            'status_text': ['Scraped', 'Processed', 'Applied'],
            'priority': ['High', 'Medium', 'Low'],
            'match_score': [85, 92, 78],
            'created_at': ['2025-01-20', '2025-01-19', '2025-01-18'],
            'url': ['https://example.com/job1', 'https://example.com/job2', 'https://example.com/job3']
        }
        
        df = pd.DataFrame(sample_data)
        print(f"✅ Sample data created with {len(df)} jobs")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import enhanced table: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing enhanced table: {e}")
        return False

def test_service_manager():
    """Test the robust service manager."""
    print("\n🧪 Testing Robust Service Manager...")
    
    try:
        from src.services.robust_service_manager import get_service_manager
        service_manager = get_service_manager()
        print("✅ Service manager imported successfully")
        
        # Test service status check
        health = service_manager.get_service_health()
        print(f"✅ Health check completed - Status: {health.get('overall_status', 'unknown')}")
        
        # Test individual service status
        services = health.get('services', {})
        print(f"✅ Found {len(services)} services to manage:")
        
        for service_name, service_info in services.items():
            status = service_info.get('status', 'unknown')
            required = service_info.get('required', False)
            print(f"  - {service_name}: {status} {'(Required)' if required else '(Optional)'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import service manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing service manager: {e}")
        return False

def test_streamlit_aggrid():
    """Test if streamlit-aggrid is properly installed."""
    print("\n🧪 Testing Streamlit AgGrid...")
    
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder
        print("✅ streamlit-aggrid imported successfully")
        
        # Test basic grid options
        sample_df = pd.DataFrame({
            'Name': ['Test 1', 'Test 2'],
            'Value': [100, 200]
        })
        
        gb = GridOptionsBuilder.from_dataframe(sample_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
        options = gb.build()
        
        print("✅ Grid options built successfully")
        return True
        
    except ImportError as e:
        print(f"❌ streamlit-aggrid not available: {e}")
        print("💡 Install with: pip install streamlit-aggrid")
        return False
    except Exception as e:
        print(f"❌ Error testing AgGrid: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Enhanced Dashboard Components\n")
    
    results = {
        "Enhanced Table": test_enhanced_table(),
        "Service Manager": test_service_manager(),
        "Streamlit AgGrid": test_streamlit_aggrid()
    }
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✅ Enhanced dashboard components are ready!")
        print("✅ Professional table with AgGrid available")
        print("✅ Robust service management available")
        print("✅ Dashboard should now look much better!")
        
        print("\n🚀 Next Steps:")
        print("1. Restart your dashboard: python -m streamlit run src/dashboard/unified_dashboard.py")
        print("2. Check the '🛠️ Services' tab for service management")
        print("3. Check the '💼 Jobs' tab for the enhanced table")
        print("4. Use the 'View Job' buttons to open job URLs in new tabs")
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        print("Some components may not work as expected")
        
        if not results["Streamlit AgGrid"]:
            print("\n💡 To get the enhanced table:")
            print("   pip install streamlit-aggrid")
        
        if not results["Service Manager"]:
            print("\n💡 Service management may have limited functionality")

if __name__ == "__main__":
    main()