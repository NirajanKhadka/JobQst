#!/usr/bin/env python3
"""
Neural Network Components Verification Script
Checks if all Llama 3 8B retraining components are ready and functional.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import importlib.util

console = Console()

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()

def check_module_imports():
    """Check if neural network modules can be imported."""
    results = {}
    
    # Core files that should exist
    core_files = {
        "llama_retraining_architecture.py": "src/neural_network/llama_retraining_architecture.py",
        "data_processor.py": "src/neural_network/data_processor.py", 
        "training_orchestrator.py": "src/neural_network/training_orchestrator.py",
        "__init__.py": "src/neural_network/__init__.py",
        "README.md": "src/neural_network/README.md",
        "requirements_neural_network.txt": "requirements_neural_network.txt"
    }
    
    console.print("[cyan]Checking core files...[/cyan]")
    for name, path in core_files.items():
        exists = check_file_exists(path)
        results[f"File: {name}"] = "✅ Present" if exists else "❌ Missing"
        console.print(f"  {name}: {'✅' if exists else '❌'}")
    
    # Check Python imports (without dependencies)
    console.print("\n[cyan]Checking basic module structure...[/cyan]")
    
    # Check if files are valid Python
    python_files = [
        "src/neural_network/llama_retraining_architecture.py",
        "src/neural_network/data_processor.py",
        "src/neural_network/training_orchestrator.py",
        "setup_neural_network.py"
    ]
    
    for file_path in python_files:
        try:
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec and spec.loader:
                results[f"Syntax: {Path(file_path).name}"] = "✅ Valid"
                console.print(f"  {Path(file_path).name}: ✅ Valid Python syntax")
            else:
                results[f"Syntax: {Path(file_path).name}"] = "❌ Invalid"
                console.print(f"  {Path(file_path).name}: ❌ Invalid")
        except Exception as e:
            results[f"Syntax: {Path(file_path).name}"] = f"❌ Error: {e}"
            console.print(f"  {Path(file_path).name}: ❌ Syntax error")
    
    return results

def check_dependencies():
    """Check if neural network dependencies are available."""
    dependencies = {
        "torch": "PyTorch - Core ML framework",
        "transformers": "Hugging Face Transformers",
        "peft": "Parameter Efficient Fine-tuning",
        "wandb": "Weights & Biases (optional)",
        "rich": "Rich console output",
        "pandas": "Data processing",
        "numpy": "Numerical computing"
    }
    
    console.print("\n[cyan]Checking dependencies...[/cyan]")
    results = {}
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            results[f"Package: {package}"] = "✅ Installed"
            console.print(f"  {package}: ✅ Installed")
        except ImportError:
            results[f"Package: {package}"] = "❌ Missing"
            console.print(f"  {package}: ❌ Not installed")
    
    return results

def check_neural_network_module():
    """Check if the neural network module loads properly."""
    console.print("\n[cyan]Checking neural network module...[/cyan]")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # Try to import the module
        from src.neural_network import get_module_status
        status = get_module_status()
        
        console.print(f"  Module version: {status.get('version', 'Unknown')}")
        console.print(f"  Llama components: {'✅' if status.get('llama_components') else '❌'}")
        console.print(f"  Legacy components: {'✅' if status.get('legacy_components') else '❌'}")
        
        return {
            "Module Import": "✅ Success",
            "Llama Components": "✅ Available" if status.get('llama_components') else "❌ Unavailable",
            "Module Version": status.get('version', 'Unknown')
        }
        
    except Exception as e:
        console.print(f"  ❌ Module import failed: {e}")
        return {
            "Module Import": f"❌ Failed: {e}",
            "Llama Components": "❌ Unknown",
            "Module Version": "Unknown"
        }

def create_status_report():
    """Create a comprehensive status report."""
    console.print(Panel(
        "[bold blue]🧠 AutoJobAgent Neural Network Components Status[/bold blue]",
        expand=False
    ))
    
    # Collect all results
    file_results = check_module_imports()
    dependency_results = check_dependencies()
    module_results = check_neural_network_module()
    
    # Create status table
    table = Table(title="Component Status Report")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    # Add all results to table
    all_results = {**file_results, **dependency_results, **module_results}
    
    for component, status in all_results.items():
        # Color code the status
        if "✅" in status:
            status_style = "[green]" + status + "[/green]"
        elif "❌" in status:
            status_style = "[red]" + status + "[/red]"
        else:
            status_style = "[yellow]" + status + "[/yellow]"
        
        table.add_row(component, status_style)
    
    console.print(table)
    
    # Summary
    total_checks = len(all_results)
    successful_checks = len([r for r in all_results.values() if "✅" in r])
    
    console.print(f"\n[bold]Summary: {successful_checks}/{total_checks} components ready[/bold]")
    
    if successful_checks == total_checks:
        console.print("[bold green]🎉 All components are ready for Llama 3 8B training![/bold green]")
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("2. Then: python src/neural_network/training_orchestrator.py --mode status")
    elif successful_checks >= total_checks * 0.8:
        console.print("[bold yellow]⚠️ Most components ready, some dependencies missing[/bold yellow]")
        console.print("\n[cyan]To complete setup:[/cyan]")
        console.print("1. Install missing dependencies: pip install -r requirements_neural_network.txt")
    else:
        console.print("[bold red]❌ Several components missing or broken[/bold red]")
        console.print("\n[cyan]Troubleshooting:[/cyan]")
        console.print("1. Check that all files are properly created")
        console.print("2. Verify Python syntax in neural network files")
        console.print("3. Install dependencies: pip install -r requirements_neural_network.txt")
    
    return successful_checks, total_checks

def main():
    """Main verification function."""
    try:
        successful, total = create_status_report()
        return 0 if successful == total else 1
    except Exception as e:
        console.print(f"[red]❌ Verification failed: {e}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
