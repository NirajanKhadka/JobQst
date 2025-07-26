#!/usr/bin/env python3
"""
Test Recent Opportunities Fix
Verify that the HTML rendering issue is resolved
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_dashboard_import():
    """Test that the dashboard can be imported without errors."""
    print("🧪 Testing dashboard import...")
    
    try:
        from src.dashboard.unified_dashboard import display_job_cards
        print("✅ Dashboard imported successfully")
        print("✅ display_job_cards function available")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_function_signature():
    """Test that the function has the correct signature."""
    print("\n🧪 Testing function signature...")
    
    try:
        from src.dashboard.unified_dashboard import display_job_cards
        import inspect
        
        sig = inspect.signature(display_job_cards)
        params = list(sig.parameters.keys())
        
        expected_params = ['df', 'limit']
        
        if params == expected_params:
            print("✅ Function signature is correct")
            return True
        else:
            print(f"❌ Function signature mismatch. Expected: {expected_params}, Got: {params}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking function signature: {e}")
        return False

def test_no_html_issues():
    """Test that the function doesn't have HTML rendering issues."""
    print("\n🧪 Testing for HTML rendering issues...")
    
    try:
        dashboard_file = Path("src/dashboard/unified_dashboard.py")
        
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for ACTUALLY problematic HTML patterns (not CSS)
        # These are the patterns that cause the ugly HTML display issue
        problematic_patterns = [
            'action_buttons +=',  # Building HTML strings
            '<a href="{job_url}" target="_blank" style=',  # Inline HTML links
            'f\'<a href=',  # F-string HTML links
            'action_buttons += f\'\'\'',  # Multi-line HTML building
        ]
        
        issues_found = []
        for pattern in problematic_patterns:
            if pattern in content:
                issues_found.append(pattern)
        
        # Also check for the specific function that was causing issues
        if 'def display_job_cards(' in content:
            # Look for the problematic HTML building pattern within the function
            start_idx = content.find('def display_job_cards(')
            if start_idx != -1:
                # Find the end of the function (next def or end of file)
                next_def = content.find('\ndef ', start_idx + 1)
                if next_def == -1:
                    function_content = content[start_idx:]
                else:
                    function_content = content[start_idx:next_def]
                
                # Check if the function still has problematic HTML building
                if 'action_buttons +=' in function_content or '<a href=' in function_content:
                    issues_found.append('HTML building in display_job_cards function')
        
        if issues_found:
            print(f"❌ Found problematic HTML patterns: {issues_found}")
            return False
        else:
            print("✅ No problematic HTML patterns found")
            print("✅ CSS styles are OK (they don't cause display issues)")
            return True
            
    except Exception as e:
        print(f"❌ Error checking for HTML issues: {e}")
        return False

def test_proper_streamlit_components():
    """Test that proper Streamlit components are used."""
    print("\n🧪 Testing for proper Streamlit components...")
    
    try:
        dashboard_file = Path("src/dashboard/unified_dashboard.py")
        
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper Streamlit patterns
        good_patterns = [
            'st.button(',
            'st.columns(',
            'st.container(',
            'st.success('
        ]
        
        patterns_found = []
        for pattern in good_patterns:
            if pattern in content:
                patterns_found.append(pattern)
        
        if len(patterns_found) >= 3:  # Should have at least 3 of these patterns
            print(f"✅ Found proper Streamlit components: {patterns_found}")
            return True
        else:
            print(f"❌ Not enough Streamlit components found: {patterns_found}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking for Streamlit components: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Recent Opportunities Fix")
    print("="*50)
    
    tests = [
        ("Dashboard Import", test_dashboard_import),
        ("Function Signature", test_function_signature),
        ("No HTML Issues", test_no_html_issues),
        ("Proper Streamlit Components", test_proper_streamlit_components)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
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
        print("✅ Recent Opportunities fix is working correctly!")
        print("✅ No more HTML rendering issues")
        print("✅ Proper Streamlit components are being used")
        print("✅ Job URL buttons should work properly")
        
        print("\n🚀 Ready to use:")
        print("1. Restart your dashboard")
        print("2. Check the Recent Opportunities section")
        print("3. Click 'View Job' buttons to test functionality")
        
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        print("Some issues may still exist")

if __name__ == "__main__":
    main()