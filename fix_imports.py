#!/usr/bin/env python3
"""
Import Fix Script for AutoJobAgent

This script fixes all import issues in test files by updating import paths
to use the correct src. prefix and ensuring all modules are properly imported.
"""

import os
import re
import glob
from src.utils.profile_helpers import load_profile, get_available_profiles
from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
from src.utils.document_generator import customize, DocumentGenerator
from pathlib import Path
from typing import List, Dict, Tuple


def find_test_files() -> List[str]:
    """Find all test files in the project."""
    test_files = []
    
    # Find all test files
    for pattern in ['tests/**/*.py', 'test_*.py']:
        test_files.extend(glob.glob(pattern, recursive=True))
    
    return test_files


def get_import_fixes() -> Dict[str, str]:
    """Get mapping of old imports to new imports."""
    return {
        # ATS imports
        'from ats import': 'from src.ats import',
        'import ats': 'import src.ats',
        'from ats.': 'from src.ats.',
        
        # Scraper imports
        'from scrapers import': 'from src.scrapers import',
        'import scrapers': 'import src.scrapers',
        'from scrapers.': 'from src.scrapers.',
        
        # Core imports
        'from core import': 'from src.core import',
        'import core': 'import src.core',
        'from core.': 'from src.core.',
        
        # Utils imports
        'from utils import': 'from src.utils import',
        'import utils': '',
        'from utils.': 'from src.utils.',
        
        # Dashboard imports
        'from dashboard import': 'from src.dashboard import',
        'import dashboard': 'import src.dashboard',
        'from dashboard.': 'from src.dashboard.',
        
        # CLI imports
        'from cli import': 'from src.cli import',
        'import cli': 'import src.cli',
        'from cli.': 'from src.cli.',
        
        # Specific module fixes
        'from job_database import': 'from src.core.job_database import',
        'import job_database': 'import src.core.job_database',
        'from document_generator import': 'from src.utils.document_generator import',
        'import document_generator': '.document_generator',
        'from dashboard_api import': 'from src.dashboard.api import',
        'import dashboard_api': 'import src.dashboard.api',
        'from csv_applicator import': 'from src.ats.csv_applicator import',
        'import csv_applicator': 'import src.ats.csv_applicator',
        'from intelligent_scraper import': 'from src.scrapers.comprehensive_eluta_scraper import',
        'import intelligent_scraper': 'import src.scrapers.comprehensive_eluta_scraper',
        
        # Test-specific imports
        'from src.main import': 'from main import',
        'import src.main': 'import main',
    }


def fix_imports_in_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Fix imports in a single file.
    
    Args:
        file_path: Path to the file to fix
        
    Returns:
        Tuple of (was_modified, list_of_changes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        changes = []
        import_fixes = get_import_fixes()
        
        # Apply import fixes
        for old_import, new_import in import_fixes.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"  {old_import} → {new_import}")
        
        # Fix specific import patterns
        patterns_to_fix = [
            # Fix @patch decorators
            (r'@patch\([\'"]([^\'"]+)\.([^\'"]+)[\'"]\)', r'@patch("\1.\2")'),
            
            # Fix relative imports that should be absolute
            (r'from \.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from src.\1 import'),
            (r'import \.([a-zA-Z_][a-zA-Z0-9_]*)', r'import src.\1'),
        ]
        
        for pattern, replacement in patterns_to_fix:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes.append(f"  Fixed pattern: {pattern}")
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False, [f"Error: {e}"]


def fix_specific_test_imports():
    """Fix specific import issues in test files."""
    specific_fixes = {
        # Test files with specific import issues
        'tests/unit/test_ats_components.py': [
            ('from src.ats.base_submitter import TestBaseSubmitter', 'from src.ats.base_submitter import BaseSubmitter as TestBaseSubmitter'),
            ('from src.ats.fallback_submitters import FallbackATSSubmitter', 'from src.ats.fallback_submitters import FallbackATSSubmitter'),
        ],
        'tests/unit/test_scraper_components.py': [
            ('from src.scrapers.eluta_optimized_parallel import ElutaOptimizedParallelScraper', 'from src.scrapers.eluta_optimized_parallel import ElutaOptimizedParallelScraper'),
            ('from src.scrapers.eluta_multi_ip import ElutaMultiIPScraper', 'from src.scrapers.eluta_multi_ip import ElutaMultiIPScraper'),
            ('from src.scrapers.indeed_enhanced import IndeedEnhancedScraper', 'from src.scrapers.indeed_enhanced import IndeedEnhancedScraper'),
            ('from src.scrapers.linkedin_enhanced import LinkedInEnhancedScraper', 'from src.scrapers.linkedin_enhanced import LinkedInEnhancedScraper'),
            ('from src.scrapers.jobbank_enhanced import JobBankEnhancedScraper', 'from src.scrapers.jobbank_enhanced import JobBankEnhancedScraper'),
            ('from src.scrapers.monster_enhanced import MonsterEnhancedScraper', 'from src.scrapers.monster_enhanced import MonsterEnhancedScraper'),
        ],
        'tests/test_integration.py': [
            ('from src.scrapers.human_behavior import HumanBehaviorMixin', 'from src.scrapers.human_behavior import HumanBehaviorMixin'),
        ],
        'tests/test_session_manager.py': [
            ('from src.scrapers.session_manager import CookieSessionManager', 'from src.scrapers.session_manager import CookieSessionManager'),
        ],
    }
    
    for file_path, fixes in specific_fixes.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                for old_line, new_line in fixes:
                    if old_line in content:
                        content = content.replace(old_line, new_line)
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Fixed specific imports in {file_path}")
                    
            except Exception as e:
                print(f"❌ Error fixing specific imports in {file_path}: {e}")


def main():
    """Main function to fix all imports."""
    print("🔧 AutoJobAgent Import Fix Script")
    print("=" * 50)
    
    # Find all test files
    test_files = find_test_files()
    print(f"📁 Found {len(test_files)} test files")
    
    # Fix general imports
    modified_files = 0
    total_changes = 0
    
    for file_path in test_files:
        print(f"\n🔍 Processing: {file_path}")
        was_modified, changes = fix_imports_in_file(file_path)
        
        if was_modified:
            modified_files += 1
            total_changes += len(changes)
            print(f"✅ Modified: {file_path}")
            for change in changes:
                print(change)
        else:
            print(f"⏭️  No changes needed: {file_path}")
    
    # Fix specific import issues
    print(f"\n🔧 Fixing specific import issues...")
    fix_specific_test_imports()
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Files processed: {len(test_files)}")
    print(f"  Files modified: {modified_files}")
    print(f"  Total changes: {total_changes}")
    
    if modified_files > 0:
        print(f"\n✅ Import fixes completed successfully!")
    else:
        print(f"\n⏭️  No import fixes were needed.")


if __name__ == "__main__":
    main() 