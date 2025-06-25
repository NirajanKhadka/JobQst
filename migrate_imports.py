#!/usr/bin/env python3
"""
Migration script to update all root-level imports to use src/ structure.
This script will:
1. Find all Python files with root-level imports
2. Update them to use src/ structure
3. Create a backup of changed files
4. Report the changes made
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

def find_python_files(directory="."):
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and .git directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def update_imports_in_file(file_path):
    """Update imports in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Update root-level imports to src/ structure
    # Pattern: from src.scrapers. -> from src.scrapers.
    content = re.sub(r'from scrapers\.', 'from src.scrapers.', content)
    content = re.sub(r'import src.scrapers', 'import src.scrapers', content)
    
    # Pattern: from src.ats. -> from src.ats.
    content = re.sub(r'from ats\.', 'from src.ats.', content)
    content = re.sub(r'import src.ats', 'import src.ats', content)
    
    # If content changed, write it back
    if content != original_content:
        # Create backup
        backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, backup_path
    
    return False, None

def main():
    """Main migration function."""
    print("🔄 Starting import migration...")
    
    # Find all Python files
    python_files = find_python_files()
    print(f"📁 Found {len(python_files)} Python files")
    
    # Track changes
    changed_files = []
    backup_files = []
    
    # Process each file
    for file_path in python_files:
        try:
            changed, backup_path = update_imports_in_file(file_path)
            if changed:
                changed_files.append(file_path)
                if backup_path:
                    backup_files.append(backup_path)
                print(f"✅ Updated: {file_path}")
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    # Summary
    print(f"\n📊 Migration Summary:")
    print(f"   Files updated: {len(changed_files)}")
    print(f"   Backup files created: {len(backup_files)}")
    
    if changed_files:
        print(f"\n📝 Updated files:")
        for file_path in changed_files:
            print(f"   - {file_path}")
    
    if backup_files:
        print(f"\n💾 Backup files:")
        for backup_path in backup_files:
            print(f"   - {backup_path}")
    
    print(f"\n✅ Migration complete!")

if __name__ == "__main__":
    main() 