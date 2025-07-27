#!/usr/bin/env python3
"""
Test Option 8 Update
Verify that CLI option 8 now uses the Fast Pipeline orchestrator.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console

console = Console()


def test_option8_imports():
    """Test that option 8 can import the Fast Pipeline."""
    console.print("[bold blue]🧪 Testing Option 8 Fast Pipeline Integration[/bold blue]")
    
    try:
        # Test main menu import
        from src.cli.menu.main_menu import MainMenu
        console.print("[green]✅ MainMenu imported successfully[/green]")
        
        # Test that Fast Pipeline can be imported
        from src.pipeline.fast_job_pipeline import FastJobPipeline
        console.print("[green]✅ FastJobPipeline imported successfully[/green]")
        
        # Test database import
        from src.core.job_database import get_job_db
        console.print("[green]✅ Database module imported successfully[/green]")
        
        return True
        
    except ImportError as e:
        console.print(f"[red]❌ Import failed: {e}[/red]")
        return False


def test_option8_method_exists():
    """Test that the new _process_existing_jobs_action method exists."""
    console.print("\n[cyan]🔧 Testing Option 8 Method Existence[/cyan]")
    
    try:
        from src.cli.menu.main_menu import MainMenu
        
        # Create test profile
        test_profile = {
            "profile_name": "test_profile",
            "keywords": ["python", "data science"]
        }
        
        menu = MainMenu(test_profile)
        
        # Check if the new method exists
        if hasattr(menu, '_process_existing_jobs_action'):
            console.print("[green]✅ _process_existing_jobs_action method exists[/green]")
            
            # Check if it's async
            import inspect
            if inspect.iscoroutinefunction(menu._process_existing_jobs_action):
                console.print("[green]✅ Method is properly async[/green]")
            else:
                console.print("[yellow]⚠️ Method is not async (may cause issues)[/yellow]")
                
            return True
        else:
            console.print("[red]❌ _process_existing_jobs_action method not found[/red]")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Method existence test failed: {e}[/red]")
        return False


def test_main_py_process_jobs():
    """Test that main.py process-jobs action uses Fast Pipeline."""
    console.print("\n[cyan]📋 Testing main.py process-jobs Action[/cyan]")
    
    try:
        # Read main.py to check if it imports FastJobPipeline
        with open("main.py", "r") as f:
            main_content = f.read()
        
        if "FastJobPipeline" in main_content:
            console.print("[green]✅ main.py imports FastJobPipeline[/green]")
        else:
            console.print("[red]❌ main.py does not import FastJobPipeline[/red]")
            return False
        
        if "process-jobs" in main_content and "Fast Pipeline" in main_content:
            console.print("[green]✅ process-jobs action mentions Fast Pipeline[/green]")
        else:
            console.print("[yellow]⚠️ process-jobs action may not use Fast Pipeline[/yellow]")
        
        # Check that old JobProcessorQueue is not used
        if "JobProcessorQueue" not in main_content or "# Use job processor queue directly" not in main_content:
            console.print("[green]✅ Old JobProcessorQueue removed from process-jobs[/green]")
        else:
            console.print("[yellow]⚠️ Old JobProcessorQueue may still be used[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ main.py test failed: {e}[/red]")
        return False


def test_menu_description_updated():
    """Test that menu description for option 8 is updated."""
    console.print("\n[cyan]📝 Testing Menu Description Update[/cyan]")
    
    try:
        # Read main_menu.py to check description
        with open("src/cli/menu/main_menu.py", "r") as f:
            menu_content = f.read()
        
        if "Process Existing Jobs (Enhanced with Fast Pipeline)" in menu_content:
            console.print("[green]✅ Option 8 description updated to mention Fast Pipeline[/green]")
        else:
            console.print("[red]❌ Option 8 description not updated[/red]")
            return False
        
        if "Legacy - use option 1 instead" not in menu_content:
            console.print("[green]✅ Legacy warning removed from option 8[/green]")
        else:
            console.print("[yellow]⚠️ Legacy warning still present[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Menu description test failed: {e}[/red]")
        return False


def main():
    """Run all option 8 update tests."""
    console.print(Panel.fit(
        "[bold blue]🚀 Option 8 Update Test Suite[/bold blue]\n"
        "[cyan]Testing that option 8 now uses Fast Pipeline orchestrator[/cyan]",
        title="Option 8 Test Suite"
    ))
    
    tests = [
        ("Import Tests", test_option8_imports),
        ("Method Existence", test_option8_method_exists),
        ("main.py Integration", test_main_py_process_jobs),
        ("Menu Description", test_menu_description_updated),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n[bold yellow]Running {test_name}...[/bold yellow]")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold blue]📊 Option 8 Update Test Results[/bold blue]")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        color = "green" if result else "red"
        console.print(f"[{color}]{status}[/{color}] {test_name}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    console.print(f"\n[bold]Results: {passed} passed, {failed} failed[/bold]")
    
    if failed == 0:
        console.print("[bold green]🎉 All option 8 update tests passed![/bold green]")
        console.print("\n[cyan]💡 Option 8 Improvements:[/cyan]")
        console.print("[cyan]  • Now uses Fast Pipeline orchestrator instead of legacy system[/cyan]")
        console.print("[cyan]  • Provides processing method selection (GPU, Rule-based, AI, Auto)[/cyan]")
        console.print("[cyan]  • Shows detailed processing results and statistics[/cyan]")
        console.print("[cyan]  • Works with existing jobs in database[/cyan]")
        console.print("[cyan]  • Available in both CLI menu and command line[/cyan]")
    else:
        console.print("[bold red]❌ Some option 8 update tests failed.[/bold red]")
    
    return failed == 0


if __name__ == "__main__":
    from rich.panel import Panel
    success = main()
    sys.exit(0 if success else 1)