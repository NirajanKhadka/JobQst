#!/usr/bin/env python3
"""
Project Cleanup Script
Organizes files according to the cleanup plan while preserving essential utilities.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ProjectCleaner:
    """Handles project file organization and cleanup."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dry_run = True  # Set to False to actually move files
        
        # Define file categories and their destinations
        self.file_categories = {
            'essential_utils': {
                'destination': 'scripts/utils',
                'files': [
                    'check_jobs.py',
                    'check_all_job_statuses.py',
                    'check_processed_jobs.py',
                    'check_real_jobs.py',
                    'clean_broken_urls.py',
                    'create_sample_jobs.py',
                    'process_pending_jobs.py',
                    'monitor_progress.py',
                    'verify_dashboard_fixes.py',
                    'check_full_urls.py'
                ]
            },
            'dev_tools': {
                'destination': 'scripts/dev',
                'files': [
                    'analyze_job_processing.py',
                    'analyze_problematic_job.py',
                    'analyze_workday_jobs.py',
                    'debug_eluta_selectors.py',
                    'explain_enhanced_workflow.py',
                    'test_enhanced_job_processor.py',
                    'test_hybrid_processor.py',
                    'test_job_worker.py',
                    'test_extractor_simple.py'
                ]
            },
            'archive_fixes': {
                'destination': 'archive/fixes',
                'files': [
                    'comprehensive_job_processor_fix.py',
                    'fix_company_extraction.py',
                    'fix_database_and_llama_config.py',
                    'fix_invalid_job_urls.py',
                    'fix_job_processing_urgent.py',
                    'fix_job_processing.py',
                    'fix_job_statuses.py',
                    'fix_llm_integration.py',
                    'fix_recent_opportunities.py',
                    'fix_remaining_issues.py',
                    'fix_scraper_issues.py',
                    'fix_scraper_with_popup_handling.py',
                    'fix_workday_scraper.py',
                    'fixed_comprehensive_processor.py',
                    'fixed_eluta_scraper.py'
                ]
            },
            'archive_processors': {
                'destination': 'archive/processors',
                'files': [
                    'openhermes_job_processor.py',
                    'reliable_job_processor.py',
                    'simple_job_processor_llama3.py',
                    'setup_openhermes_job_processor.py'
                ]
            },
            'archive_scrapers': {
                'destination': 'archive/scrapers',
                'files': [
                    'improved_test_scraper.py',
                    'robust_eluta_scraper.py',
                    'simple_test_scraper.py',
                    'smart_job_scraper.py'
                ]
            },
            'archive_tests': {
                'destination': 'archive/tests',
                'files': [
                    'test_all_jobs_with_logging.py',
                    'test_all_scrapers.py',
                    'test_company_extraction.py',
                    'test_document_generator_demo.py',
                    'test_eluta_scraping.py',
                    'test_eluta_selectors.py',
                    'test_eluta_url.py',
                    'test_enhanced_dashboard.py',
                    'test_fixed_eluta_scraper.py',
                    'test_fixed_scraper.py',
                    'test_fresh_scraping.py',
                    'test_gemini_docs.py',
                    'test_jobs.py',
                    'test_job_processor.py',
                    'test_job_processor_demo.py',
                    'test_job_processor_fake_urls.py',
                    'test_openhermes_integration.py',
                    'test_popup_fix.py',
                    'test_recent_opportunities_fix.py',
                    'test_robust_scrapers.py',
                    'test_scraper_with_limit.py',
                    'test_scraper_with_url_filter.py',
                    'test_url_filter_integration.py',
                    'test_verified_job_processor.py'
                ]
            },
            'move_to_logs': {
                'destination': 'logs',
                'files': [
                    'error_logs.log',
                    'job_processing_errors.log',
                    'test_output.log'
                ]
            },
            'move_to_temp': {
                'destination': 'temp',
                'files': [
                    'test_cover_letter_output.txt',
                    'test_customized_output.txt',
                    'test_resume_output.txt',
                    'test_scraper_result.json',
                    'towardsai_job_links.txt',
                    'eluta_page.png'
                ]
            }
        }
    
    def create_directories(self):
        """Create necessary directories."""
        directories = [
            'scripts/utils',
            'scripts/dev',
            'archive/fixes',
            'archive/processors',
            'archive/scrapers',
            'archive/tests',
            'logs',
            'temp'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                print(f"Creating directory: {directory}")
                if not self.dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
    
    def move_files(self):
        """Move files according to categorization."""
        for category, config in self.file_categories.items():
            destination = config['destination']
            files = config['files']
            
            print(f"\n📁 Processing {category} -> {destination}")
            
            for filename in files:
                source_path = self.project_root / filename
                dest_path = self.project_root / destination / filename
                
                if source_path.exists():
                    print(f"  Moving: {filename}")
                    if not self.dry_run:
                        shutil.move(str(source_path), str(dest_path))
                else:
                    print(f"  ⚠️  Not found: {filename}")
    
    def create_readme_files(self):
        """Create README files for organized directories."""
        readme_contents = {
            'scripts/utils/README.md': '''# Utility Scripts

Essential utilities for database management and system monitoring.

## Database Management
- `check_jobs.py` - Check job database status and statistics
- `check_all_job_statuses.py` - Comprehensive job status analysis
- `check_processed_jobs.py` - Verify processed job results
- `check_real_jobs.py` - Validate real job data quality
- `clean_broken_urls.py` - Remove invalid URLs from database

## Job Processing
- `create_sample_jobs.py` - Generate test data for development
- `process_pending_jobs.py` - Process jobs with pending status
- `monitor_progress.py` - Real-time progress monitoring

## System Verification
- `verify_dashboard_fixes.py` - Verify dashboard functionality
- `check_full_urls.py` - URL validation utility

## Usage
Run any script directly:
```bash
python scripts/utils/check_jobs.py
python scripts/utils/monitor_progress.py
```
''',
            'scripts/dev/README.md': '''# Development Tools

Tools for debugging, analysis, and development workflow.

## Analysis & Debugging
- `analyze_job_processing.py` - Analyze processing performance
- `analyze_problematic_job.py` - Debug specific job issues
- `analyze_workday_jobs.py` - Workday-specific analysis
- `debug_eluta_selectors.py` - Debug scraping selectors
- `explain_enhanced_workflow.py` - Workflow documentation

## Testing & Validation
- `test_enhanced_job_processor.py` - Test main processor
- `test_hybrid_processor.py` - Test hybrid processing
- `test_job_worker.py` - Test worker functionality
- `test_extractor_simple.py` - Test data extraction

## Usage
These are development tools for debugging and analysis:
```bash
python scripts/dev/analyze_job_processing.py
python scripts/dev/debug_eluta_selectors.py
```
''',
            'archive/README.md': '''# Archive

Historical files kept for reference and rollback purposes.

## Structure
- `fixes/` - Historical fix scripts and patches
- `processors/` - Old processor implementations
- `scrapers/` - Legacy scraper versions
- `tests/` - One-time test scripts

## Purpose
These files are archived but not deleted to:
1. Provide historical context
2. Enable rollback if needed
3. Reference old implementations
4. Maintain project history

## Note
Files in archive are not actively maintained and may not work with current codebase.
'''
        }
        
        for filepath, content in readme_contents.items():
            full_path = self.project_root / filepath
            print(f"Creating README: {filepath}")
            if not self.dry_run:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
    
    def update_imports(self):
        """Update import statements in moved files."""
        print("\n🔧 Updating import statements...")
        
        # Files that might need import updates
        files_to_update = [
            'scripts/utils/check_jobs.py',
            'scripts/utils/create_sample_jobs.py',
            'scripts/utils/process_pending_jobs.py',
            'scripts/utils/monitor_progress.py'
        ]
        
        for filepath in files_to_update:
            full_path = self.project_root / filepath
            if full_path.exists():
                print(f"  Checking imports in: {filepath}")
                # In a real implementation, we'd update the imports here
                # For now, just note that this needs to be done
    
    def generate_cleanup_report(self):
        """Generate a report of what was cleaned up."""
        report_path = self.project_root / 'CLEANUP_REPORT.md'
        
        report_content = f'''# Project Cleanup Report

Generated on: {os.popen("date").read().strip()}

## Summary
- **Essential utilities**: Moved to `scripts/utils/`
- **Development tools**: Moved to `scripts/dev/`
- **Historical fixes**: Archived in `archive/fixes/`
- **Old processors**: Archived in `archive/processors/`
- **Legacy scrapers**: Archived in `archive/scrapers/`
- **One-time tests**: Archived in `archive/tests/`
- **Log files**: Moved to `logs/`
- **Temporary files**: Moved to `temp/`

## File Counts
'''
        
        for category, config in self.file_categories.items():
            count = len(config['files'])
            destination = config['destination']
            report_content += f"- **{category}**: {count} files → `{destination}/`\n"
        
        report_content += '''
## Next Steps
1. Test that moved utilities still work correctly
2. Update any hardcoded paths in scripts
3. Update documentation references
4. Consider removing archive files after verification period

## Rollback
If needed, files can be moved back from their new locations.
Archive contains all historical implementations.
'''
        
        print(f"Generating cleanup report: CLEANUP_REPORT.md")
        if not self.dry_run:
            with open(report_path, 'w') as f:
                f.write(report_content)
    
    def run_cleanup(self, dry_run: bool = True):
        """Run the complete cleanup process."""
        self.dry_run = dry_run
        
        print("🧹 AutoJobAgent Project Cleanup")
        print("=" * 50)
        
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be moved")
        else:
            print("⚠️  LIVE MODE - Files will be moved!")
        
        print(f"Project root: {self.project_root}")
        
        # Step 1: Create directories
        print("\n1. Creating directory structure...")
        self.create_directories()
        
        # Step 2: Move files
        print("\n2. Moving files...")
        self.move_files()
        
        # Step 3: Create README files
        print("\n3. Creating documentation...")
        self.create_readme_files()
        
        # Step 4: Update imports (placeholder)
        print("\n4. Updating imports...")
        self.update_imports()
        
        # Step 5: Generate report
        print("\n5. Generating cleanup report...")
        self.generate_cleanup_report()
        
        print("\n✅ Cleanup completed!")
        
        if dry_run:
            print("\n🔄 To actually perform cleanup, run:")
            print("python scripts/cleanup_project.py --live")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up AutoJobAgent project structure")
    parser.add_argument("--live", action="store_true", help="Actually move files (default is dry run)")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).parent.parent,
                       help="Project root directory")
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner(args.project_root)
    cleaner.run_cleanup(dry_run=not args.live)


if __name__ == "__main__":
    main()