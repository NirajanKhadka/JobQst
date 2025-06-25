#!/usr/bin/env python3
"""
Comprehensive syntax fix script for AutoJobAgent test files.
Fixes incomplete imports, try/except blocks, and invalid syntax.
"""

import os
import re
import glob
from pathlib import Path

def fix_syntax_in_file(file_path):
    """Fix syntax errors in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix 1: Remove stray .document_generator lines
    content = re.sub(r'^\s*\.document_generator\s*$', '', content, flags=re.MULTILINE)
    
    # Fix 2: Fix incomplete import statements like "from src.utils .document_generator"
    content = re.sub(r'from src\.utils \.document_generator', 'from src.utils.document_generator', content)
    
    # Fix 3: Remove incomplete import lines that are just dots
    content = re.sub(r'^\s*\.\w+\s*$', '', content, flags=re.MULTILINE)
    
    # Fix 4: Fix incomplete try/except blocks
    # Look for try blocks that don't have corresponding except/finally
    lines = content.split('\n')
    fixed_lines = []
    in_try_block = False
    try_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if we're starting a try block
        if stripped.startswith('try:'):
            in_try_block = True
            try_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
        # Check if we're in a try block and hit an incomplete import
        elif in_try_block and stripped.startswith('from ') and 'import' in stripped:
            # This might be an incomplete import in a try block
            fixed_lines.append(line)
        # Check if we're ending a try block
        elif in_try_block and (stripped.startswith('except') or stripped.startswith('finally')):
            in_try_block = False
            fixed_lines.append(line)
        # If we're in a try block and hit something that's not except/finally, add it
        elif in_try_block:
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Fix 5: Remove any remaining incomplete import statements
    content = re.sub(r'^\s*from\s+[^\s]+\s+import\s*$', '', content, flags=re.MULTILINE)
    
    # Fix 6: Remove any lines that are just dots or incomplete syntax
    content = re.sub(r'^\s*\.\s*$', '', content, flags=re.MULTILINE)
    
    # Fix 7: Fix any remaining syntax issues with imports
    content = re.sub(r'from src\.utils\s+\.', 'from src.utils.', content)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix all syntax errors."""
    print("🔧 Starting comprehensive syntax fix...")
    
    # Find all test Python files
    test_files = []
    test_files.extend(glob.glob("tests/**/*.py", recursive=True))
    
    print(f"📁 Found {len(test_files)} test files to check")
    
    fixed_files = []
    for file_path in test_files:
        try:
            if fix_syntax_in_file(file_path):
                fixed_files.append(file_path)
                print(f"✅ Fixed syntax in: {file_path}")
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
    
    print(f"\n🎉 Syntax fix complete!")
    print(f"📊 Files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print("\n📝 Fixed files:")
        for file_path in fixed_files:
            print(f"  - {file_path}")

if __name__ == "__main__":
    main() 