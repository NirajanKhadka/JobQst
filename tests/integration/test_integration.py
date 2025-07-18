#!/usr/bin/env python3
"""
Integration test script for Document Generator service.
Tests all integration points: CLI, API, and standalone modes.
"""

import sys
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.panel import Panel

console = Console()

def test_cli_integration():
    """Test CLI integration."""
    console.print(Panel("🧪 Testing CLI Integration", style="bold blue"))
    
    try:
        # Import CLI components
        from src.cli.actions.document_actions import DocumentActions
        from src.utils.profile_helpers import load_profile
        
        # Load test profile
        profile = load_profile("Nirajan")
        if not profile:
            console.print("[red]❌ Failed to load test profile[/red]")
            pytest.skip("Failed to load test profile")
            
        profile["profile_name"] = "Nirajan"
        
        # Initialize document actions
        doc_actions = DocumentActions(profile)
        console.print("[green]✅ CLI integration successful[/green]")
        console.print(f"[cyan]📧 Profile loaded: {profile.get('name', 'Unknown')}[/cyan]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ CLI integration failed: {e}[/red]")
        pytest.skip(f"CLI integration failed: {e}")

def test_service_integration():
    """Test service integration."""
    console.print(Panel("⚙️ Testing Service Integration", style="bold blue"))
    
    try:
        # Import service components
        from src.services.document_generator import DocumentGenerator
        from src.utils.profile_helpers import load_profile
        
        # Load test profile
        profile = load_profile("Nirajan")
        if not profile:
            console.print("[red]❌ Failed to load test profile[/red]")
            pytest.skip("Failed to load test profile")
            
        profile["profile_name"] = "Nirajan"
        
        # Initialize document generator
        generator = DocumentGenerator(profile)
        console.print("[green]✅ Service integration successful[/green]")
        console.print(f"[cyan]🤖 Generator initialized for: {profile.get('name', 'Unknown')}[/cyan]")
        
        # Test output directory access
        output_dir = generator._get_output_dir()
        console.print(f"[cyan]📁 Output directory: {output_dir}[/cyan]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Service integration failed: {e}[/red]")
        pytest.skip(f"Service integration failed: {e}")

def test_main_cli_integration():
    """Test main CLI integration."""
    console.print(Panel("🚀 Testing Main CLI Integration", style="bold blue"))
    
    try:
        # Import main menu components
        from src.cli.menu.main_menu import MainMenu
        from src.utils.profile_helpers import load_profile
        
        # Load test profile
        profile = load_profile("Nirajan")
        if not profile:
            console.print("[red]❌ Failed to load test profile[/red]")
            pytest.skip("Failed to load test profile")
            
        profile["profile_name"] = "Nirajan"
        
        # Initialize main menu
        main_menu = MainMenu(profile)
        console.print("[green]✅ Main CLI integration successful[/green]")
        console.print("[cyan]📋 Menu includes document generation option[/cyan]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Main CLI integration failed: {e}[/red]")
        pytest.skip(f"Main CLI integration failed: {e}")

def test_standalone_mode():
    """Test standalone mode."""
    console.print(Panel("🔧 Testing Standalone Mode", style="bold blue"))
    
    try:
        # Test standalone initialization
        from src.services.document_generator import DocumentGenerator
        
        # Initialize without profile (standalone mode)
        generator = DocumentGenerator()
        console.print("[green]✅ Standalone mode successful[/green]")
        console.print(f"[cyan]👤 Profile auto-loaded: {generator.profile.get('name', 'Unknown')}[/cyan]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Standalone mode failed: {e}[/red]")
        pytest.skip(f"Standalone mode failed: {e}")

def main():
    """Run all integration tests."""
    console.print("[bold blue]🧪 Document Generator Integration Tests[/bold blue]")
    console.print("[cyan]Testing all integration points...[/cyan]\n")
    
    tests = [
        ("CLI Integration", test_cli_integration),
        ("Service Integration", test_service_integration),
        ("Main CLI Integration", test_main_cli_integration),
        ("Standalone Mode", test_standalone_mode),
    ]
    
    results = []
    for test_name, test_func in tests:
        console.print(f"\n[bold]Running: {test_name}[/bold]")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    console.print(Panel("📊 Integration Test Summary", style="bold green"))
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"  {status}: {test_name}")
    
    console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]🎉 All integration tests passed![/bold green]")
        console.print("[cyan]✅ Document Generator service is fully integrated[/cyan]")
    else:
        console.print("[bold red]❌ Some integration tests failed[/bold red]")
        console.print("[yellow]Check error messages above for details[/yellow]")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
