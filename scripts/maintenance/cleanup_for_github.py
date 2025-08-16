#!/usr/bin/env python3
"""
GitHub Repository Cleanup Script
Removes memory bank, AI model files, and other files that shouldn't be in the repository
"""

import os
import shutil
import subprocess
from pathlib import Path

def run_git_command(cmd):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=".")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def remove_files_and_folders():
    """Remove files and folders that shouldn't be in GitHub"""
    
    # Files and folders to remove
    items_to_remove = [
        # Memory bank (AI-related)
        "memory-bank/",
        
        # AI service files
        "src/ai/",
        
        # Workflow data (session-specific)
        "workflow_data/",
        
        # Cache directories
        "cache/",
        "src/dashboard/caching/",
        
        # Backup directories
        "backups/",
        "archive/",
        
        # Temporary/generated files
        "JobSpy/",
        "jobspy_test/",
        
        # Log files
        "*.log",
        "logs/",
        "error_logs.log",
        "mississauga_job_search.log",
        
        # Test database files
        "data/test_*.db",
        
        # Marketing/project management files
        "MARKETING_FLUFF_CLEANUP_PLAN.md",
        "MARKETING_FLUFF_CLEANUP_RESULTS.md", 
        "MARKETING_FLUFF_REMOVAL_COMPLETE.md",
        "PHASE_*_COMPLETION_REPORT.md",
        "PHASE_1_MODULARIZATION_SUCCESS.md",
        "PROJECT_CLEANUP_SUMMARY.md",
        "DASHBOARD_FIX_SUMMARY.md",
        "QUICK_FIX_REPORT.md",
        
        # Temporary analysis files
        "analyze_dashboard_data.py",
        "check_db_data.py",
        "process_all_nirajan_jobs.py",
        "run_auto_fix.py",
        "quick_jobspy_test.py",
        
        # Test files that should be in tests/ directory
        "test_*.py",
        
        # Documentation that's outdated
        "docs/Nirajan/",
        "docs/PHASE_1_IMPLEMENTATION_SUMMARY.md",
        "docs/dashboard/",
        
        # Examples directory (can be recreated with better examples)
        "examples/",
        
        # Config dashboard (environment-specific)
        "config/dashboard/",
        
        # Various cleanup and utility scripts
        "scripts/analyze_duplicates.py",
        "scripts/auto_fix_redundancies.py",
        "scripts/auto_fix_system.py",
        "scripts/benchmarks/",
        "scripts/clear_dashboard_cache.py",
        "scripts/consolidate_profile_databases.py",
        "scripts/database_tools.py",
        "scripts/document_validator.py",
        "scripts/final_cleanup.py",
        "scripts/job_application_cli.py",
        "scripts/launch_dashboard.py",
        "scripts/monster_integration.py",
        "scripts/remove_marketing_fluff.py",
        "scripts/verify_cleanup.py",
        "scripts/verify_documentation.py",
        
        # Source cleanup
        "src/CLEANUP_SUMMARY.md",
        
        # Additional new files that are environment-specific
        "src/simple_job_processor_llama3.py",
        "src/utils/gemini_document_generator.py",
        "src/utils/ssl_certificate_fix.py",
        
        # More test files
        "test_dashboard_functionality.py",
        "test_jobspy_50_jobs_5_keywords.py", 
        "test_modular_dashboard.py",
        "test_phase4_services.py",
        "test_session_state_fix.py",
        "test_working_sites.py",
        
        # Additional integration test directories
        "tests/dashboard/integration/",
        "tests/unit/test_dashboard_connection.py",
        "tests/unit/test_real_database_jobs.py",
        "tests/unit/test_scrapers/scraper_job_limit_test.py",
        "tests/unit/test_scrapers/test_unified_eluta_scraper.py",
        "tests/unit/test_scraping_performance_improved.py",
    ]
    
    print("🧹 Cleaning up repository for GitHub...")
    
    removed_count = 0
    
    for item in items_to_remove:
        if "*" in item:
            # Handle wildcard patterns
            import glob
            matches = glob.glob(item)
            for match in matches:
                if os.path.exists(match):
                    try:
                        if os.path.isdir(match):
                            shutil.rmtree(match)
                        else:
                            os.remove(match)
                        print(f"✅ Removed: {match}")
                        removed_count += 1
                    except Exception as e:
                        print(f"❌ Failed to remove {match}: {e}")
        else:
            if os.path.exists(item):
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                    else:
                        os.remove(item)
                    print(f"✅ Removed: {item}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to remove {item}: {e}")
    
    print(f"\n📊 Removed {removed_count} items")
    return removed_count > 0

def update_gitignore():
    """Update .gitignore to prevent these files from being tracked again"""
    
    gitignore_additions = """
# Memory bank and AI session data
memory-bank/
workflow_data/

# Cache directories
cache/
src/dashboard/caching/
__pycache__/
*.pyc
*.pyo

# Log files
*.log
logs/
error_logs.log

# Temporary and backup files
backups/
archive/
temp/
*.tmp
*.bak

# Database files (except schema)
*.db
!schema.sql

# Environment specific configs
config/dashboard/
.env
.env.local

# IDE specific files
.vscode/
.idea/
*.swp
*.swo

# OS specific files
.DS_Store
Thumbs.db

# AI model files and training data
models/
training_data/
*.pkl
*.model

# Test outputs and temporary test files
test_output/
test_results/
test_*.py
!tests/

# Examples with sensitive data
examples/
JobSpy/
jobspy_test/

# Documentation that's environment specific
docs/dashboard/
docs/Nirajan/

# Project management files
*_COMPLETION_REPORT.md
*_CLEANUP_*.md
*_FIX_*.md
PROJECT_*.md
PHASE_*.md
MARKETING_*.md
"""
    
    gitignore_path = ".gitignore"
    
    # Read existing .gitignore
    existing_content = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            existing_content = f.read()
    
    # Check if we need to add anything
    lines_to_add = []
    for line in gitignore_additions.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and line not in existing_content:
            lines_to_add.append(line)
    
    if lines_to_add:
        with open(gitignore_path, 'a') as f:
            f.write(gitignore_additions)
        print(f"✅ Updated .gitignore with {len(lines_to_add)} new patterns")
        return True
    else:
        print("✅ .gitignore is already up to date")
        return False

def git_remove_tracked_files():
    """Remove files from git tracking that are now in .gitignore"""
    
    # Files that should be removed from tracking
    tracked_files_to_remove = [
        "memory-bank/",
        "workflow_data/",
        "cache/",
        "logs/",
        "*.log",
        "backups/",
        "archive/",
        "JobSpy/",
        "jobspy_test/",
    ]
    
    print("\n🗑️ Removing files from Git tracking...")
    
    for pattern in tracked_files_to_remove:
        success, stdout, stderr = run_git_command(f'git rm -r --cached "{pattern}"')
        if success:
            print(f"✅ Removed from tracking: {pattern}")
        elif "did not match any files" not in stderr:
            print(f"⚠️ Could not remove {pattern}: {stderr}")

def main():
    """Main cleanup function"""
    
    print("🚀 Starting GitHub Repository Cleanup")
    print("=" * 50)
    
    # Step 1: Remove files and folders
    print("\n📁 Step 1: Removing files and folders...")
    files_removed = remove_files_and_folders()
    
    # Step 2: Update .gitignore
    print("\n📝 Step 2: Updating .gitignore...")
    gitignore_updated = update_gitignore()
    
    # Step 3: Remove from git tracking
    print("\n🗑️ Step 3: Removing from Git tracking...")
    git_remove_tracked_files()
    
    # Step 4: Git status
    print("\n📊 Step 4: Current Git status...")
    success, stdout, stderr = run_git_command("git status --porcelain")
    if success:
        lines = stdout.strip().split('\n') if stdout.strip() else []
        print(f"📈 Files changed: {len([l for l in lines if l])}")
        
        # Show first 10 changes
        for line in lines[:10]:
            print(f"   {line}")
        
        if len(lines) > 10:
            print(f"   ... and {len(lines) - 10} more")
    
    print("\n" + "=" * 50)
    print("✅ Cleanup completed!")
    print("\nNext steps:")
    print("1. Review the changes with: git status")
    print("2. Add files to staging: git add .")
    print("3. Commit changes: git commit -m 'Clean up repository - remove memory bank and AI files'")
    print("4. Push to GitHub: git push origin main")
    
    print(f"\n💡 Summary:")
    print(f"   - Files removed: {'Yes' if files_removed else 'No'}")
    print(f"   - .gitignore updated: {'Yes' if gitignore_updated else 'No'}")
    print(f"   - Repository is now clean for GitHub")

if __name__ == "__main__":
    main()
