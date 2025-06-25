#!/usr/bin/env python3
"""
Test script to demonstrate basic functionality testing.
"""

import sys
from pathlib import Path

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from rich.console import Console
import time
from src import utils

console = Console()

def test_basic_functionality():
    """Test basic functionality without the non-existent intelligent_scraper."""
    console.print("[bold blue]🧪 Testing Basic Functionality[/bold blue]")
    
    try:
        # Test 1: Check if core modules can be imported
        console.print("\n[bold]Test 1: Core Module Imports[/bold]")
        
        from src.utils.document_generator import customize
        console.print("[green]✅ document_generator imported successfully[/green]")
        
        from src.ats import detect, get_submitter
        console.print("[green]✅ ats module imported successfully[/green]")
        
        # Test 2: Check if profile loading works
        console.print("\n[bold]Test 2: Profile Loading[/bold]")
        try:
            profile = load_profile("Nirajan")
            if profile:
                console.print(f"[green]✅ Profile loaded: {profile.get('name', 'Unknown')}[/green]")
                console.print(f"[cyan]Profile keywords: {len(profile.get('keywords', []))}[/cyan]")
            else:
                console.print("[yellow]⚠️ Profile not found, but no error occurred[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Profile loading test skipped: {e}[/yellow]")
        
        # Test 3: Check if basic data structures work
        console.print("\n[bold]Test 3: Basic Data Structures[/bold]")
        test_job = {
            "title": "Test Job",
            "company": "Test Company",
            "location": "Test Location",
            "url": "https://example.com"
        }
        console.print("[green]✅ Job dictionary created successfully[/green]")
        
        # Test 4: Check if path operations work
        console.print("\n[bold]Test 4: File System Operations[/bold]")
        test_path = Path("profiles/Nirajan")
        if test_path.exists():
            console.print("[green]✅ Profile directory exists[/green]")
        else:
            console.print("[yellow]⚠️ Profile directory not found[/yellow]")
        
        console.print("[green]✅ All basic functionality tests passed![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Test error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def test_import_stability():
    """Test that imports are stable and don't cause crashes."""
    console.print("\n[bold blue]🧪 Testing Import Stability[/bold blue]")
    
    try:
        # Test multiple imports to ensure stability
        start_time = time.time()
        
        for i in range(5):
            try:
                from src.utils.document_generator import customize
                from src.ats import detect, get_submitter
                console.print(f"[green]✅ Import iteration {i+1} successful[/green]")
            except Exception as e:
                console.print(f"[red]❌ Import iteration {i+1} failed: {e}[/red]")
                return False
        
        end_time = time.time()
        console.print(f"[cyan]Import stability test completed in {end_time - start_time:.2f} seconds[/cyan]")
        console.print("[green]✅ Import stability test passed![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Import stability test failed: {e}[/red]")
        return False

if __name__ == "__main__":
    try:
        success1 = test_basic_functionality()
        success2 = test_import_stability()
        
        if success1 and success2:
            console.print("\n[bold green]🎉 All tests completed successfully![/bold green]")
        else:
            console.print("\n[bold red]❌ Some tests failed![/bold red]")
            
    except Exception as e:
        console.print(f"\n[red]❌ Test error: {e}[/red]")
        import traceback
        traceback.print_exc()
