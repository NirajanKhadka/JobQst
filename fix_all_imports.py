#!/usr/bin/env python3
"""
Comprehensive import fix script for AutoJobAgent.
Fixes all incorrect utils imports to use the correct utility modules.
"""

import os
import re
import glob
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix 1: Replace "from src.core import utils" with specific imports
    if "from src.core import utils" in content:
        # Add specific imports at the top
        specific_imports = [
            "from src.utils.profile_helpers import load_profile, get_available_profiles",
            "from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs",
            "from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv",
            "from src.utils.document_generator import customize, DocumentGenerator"
        ]
        
        # Remove the problematic import
        content = content.replace("from src.core import utils", "")
        
        # Add specific imports after other imports
        import_pattern = r'^import\s+.*$'
        import_lines = re.findall(import_pattern, content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            content = content.replace(last_import, last_import + "\n" + "\n".join(specific_imports))
        else:
            # If no imports found, add at the beginning
            content = "\n".join(specific_imports) + "\n\n" + content
    
    # Fix 2: Replace "import src.utils" with specific imports
    if "import src.utils" in content:
        # Add specific imports at the top
        specific_imports = [
            "from src.utils.profile_helpers import load_profile, get_available_profiles",
            "from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs",
            "from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv",
            "from src.utils.document_generator import customize, DocumentGenerator"
        ]
        
        # Remove the problematic import
        content = content.replace("import src.utils", "")
        
        # Add specific imports after other imports
        import_pattern = r'^import\s+.*$'
        import_lines = re.findall(import_pattern, content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            content = content.replace(last_import, last_import + "\n" + "\n".join(specific_imports))
        else:
            # If no imports found, add at the beginning
            content = "\n".join(specific_imports) + "\n\n" + content
    
    # Fix 3: Replace "from src.utils import src.utils.document_generator" with correct import
    content = content.replace("from src.utils import src.utils.document_generator", "from src.utils.document_generator import DocumentGenerator, customize")
    
    # Fix 4: Replace utils.function() calls with direct function calls
    function_mappings = {
        'utils.load_profile': 'load_profile',
        'utils.get_available_profiles': 'get_available_profiles',
        'utils.generate_job_hash': 'generate_job_hash',
        'utils.is_duplicate_job': 'is_duplicate_job',
        'utils.sort_jobs': 'sort_jobs',
        'utils.save_jobs_to_json': 'save_jobs_to_json',
        'utils.load_jobs_from_json': 'load_jobs_from_json',
        'utils.save_jobs_to_csv': 'save_jobs_to_csv',
        'utils.customize': 'customize',
        'utils.hash_job': 'generate_job_hash',
        'utils.convert_doc_to_pdf': 'convert_doc_to_pdf',  # This might need a different fix
        'utils.create_browser_context': 'create_browser_context',  # This might need a different fix
        'utils.detect_available_browsers': 'detect_available_browsers'  # This might need a different fix
    }
    
    for old_call, new_call in function_mappings.items():
        content = content.replace(old_call, new_call)
    
    # Fix 5: Replace "from src.core.utils import load_profile" with correct import
    content = content.replace("from src.core.utils import load_profile", "from src.utils.profile_helpers import load_profile")
    
    # Fix 6: Replace "from src.core.utils import *" with specific imports
    if "from src.core.utils import *" in content:
        specific_imports = [
            "from src.utils.profile_helpers import load_profile, get_available_profiles",
            "from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs",
            "from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv",
            "from src.utils.document_generator import customize, DocumentGenerator"
        ]
        content = content.replace("from src.core.utils import *", "\n".join(specific_imports))
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix all imports."""
    print("🔧 Starting comprehensive import fix...")
    
    # Find all Python files
    python_files = []
    python_files.extend(glob.glob("*.py"))
    python_files.extend(glob.glob("src/**/*.py", recursive=True))
    python_files.extend(glob.glob("tests/**/*.py", recursive=True))
    
    # Remove the script itself
    python_files = [f for f in python_files if f != "fix_all_imports.py"]
    
    print(f"📁 Found {len(python_files)} Python files to check")
    
    fixed_files = []
    for file_path in python_files:
        try:
            if fix_imports_in_file(file_path):
                fixed_files.append(file_path)
                print(f"✅ Fixed imports in: {file_path}")
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
    
    print(f"\n🎉 Import fix complete!")
    print(f"📊 Files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print("\n📝 Fixed files:")
        for file_path in fixed_files:
            print(f"  - {file_path}")

if __name__ == "__main__":
    main() 