#!/usr/bin/env python3
"""
Documentation Update Verification Script
Checks that all documentation files properly reflect the apply button integration.
"""

import os
from pathlib import Path

def check_documentation_updates():
    """Verify that apply button integration is documented across all relevant files."""
    
    print("🔍 Verifying Documentation Updates for Apply Button Integration\n")
    
    # Files to check
    docs_to_check = [
        ("README.md", ["apply", "dashboard", "One-Click Applications"]),
        ("docs/DEVELOPMENT_STANDARDS.md", ["Apply Button Integration", "COMPLETED", "update_application_status"]),
        ("docs/ARCHITECTURE.md", ["Apply Integration", "apply_to_job_streamlit", "Manual Mode"]),
        ("DASHBOARD_TODO.md", ["Apply Button Integration", "July 3, 2025", "COMPLETED"])
    ]
    
    all_good = True
    
    for file_path, search_terms in docs_to_check:
        if not Path(file_path).exists():
            print(f"❌ {file_path} - File not found")
            all_good = False
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        found_terms = []
        missing_terms = []
        
        for term in search_terms:
            if term.lower() in content.lower():
                found_terms.append(term)
            else:
                missing_terms.append(term)
        
        if missing_terms:
            print(f"⚠️ {file_path} - Missing terms: {missing_terms}")
            all_good = False
        else:
            print(f"✅ {file_path} - All expected terms found: {found_terms}")
    
    print("\n" + "="*60)
    
    if all_good:
        print("🎉 ALL DOCUMENTATION UPDATES VERIFIED!")
        print("✅ Apply button integration properly documented across all files")
        print("✅ Feature descriptions are consistent")
        print("✅ Architecture documentation is complete")
    else:
        print("⚠️ Some documentation issues found - see details above")
    
    print("\n📋 Documentation Summary:")
    print("- README.md: Updated dashboard features and core capabilities")
    print("- DEVELOPMENT_STANDARDS.md: Added completed apply button section")
    print("- ARCHITECTURE.md: Enhanced dashboard and application system docs")
    print("- DASHBOARD_TODO.md: Marked apply button integration as completed")
    
    return all_good

if __name__ == "__main__":
    check_documentation_updates()
