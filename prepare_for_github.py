#!/usr/bin/env python3
"""
Script to prepare AutoJobAgent for GitHub repository upload.
This script helps clean up sensitive data and prepare the codebase for public release.
"""

import os
import shutil
import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def clean_sensitive_data():
    """Remove sensitive data from profiles and sessions."""
    console.print("[yellow]🧹 Cleaning sensitive data...[/yellow]")
    
    # Clean profile directories
    profiles_dir = Path("profiles")
    if profiles_dir.exists():
        for profile_dir in profiles_dir.iterdir():
            if profile_dir.is_dir():
                # Remove browser data
                browser_dirs = ["opera_data", "edge_data", "chromium_data", "playwright"]
                for browser_dir in browser_dirs:
                    browser_path = profile_dir / browser_dir
                    if browser_path.exists():
                        shutil.rmtree(browser_path)
                        console.print(f"  ✅ Removed {browser_path}")
                
                # Remove session data
                session_dirs = ["browser_sessions", "applications"]
                for session_dir in session_dirs:
                    session_path = profile_dir / session_dir
                    if session_path.exists():
                        shutil.rmtree(session_path)
                        console.print(f"  ✅ Removed {session_path}")
                
                # Remove generated files
                for file_pattern in ["*.pdf", "session.json", "*.xlsx"]:
                    for file_path in profile_dir.glob(file_pattern):
                        file_path.unlink()
                        console.print(f"  ✅ Removed {file_path}")
    
    # Clean output directory
    output_dir = Path("output")
    if output_dir.exists():
        shutil.rmtree(output_dir)
        console.print(f"  ✅ Removed {output_dir}")
    
    # Clean temp directory
    temp_dir = Path("temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        console.print(f"  ✅ Removed {temp_dir}")

def sanitize_profile_config():
    """Sanitize profile configuration files."""
    console.print("[yellow]🔧 Sanitizing profile configurations...[/yellow]")
    
    profiles_dir = Path("profiles")
    if profiles_dir.exists():
        for profile_dir in profiles_dir.iterdir():
            if profile_dir.is_dir():
                config_file = profile_dir / f"{profile_dir.name}.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        
                        # Sanitize sensitive fields
                        if "email" in config:
                            config["email"] = "your.email@example.com"
                        if "phone" in config:
                            config["phone"] = "+1-234-567-8900"
                        if "address" in config:
                            config["address"] = "123 Main St, Your City, Province"
                        
                        # Keep example credentials pattern but sanitize
                        if "credentials" in config:
                            config["credentials"]["email"] = "your.email@gmail.com"
                            # Keep the pattern as it's educational
                        
                        with open(config_file, 'w') as f:
                            json.dump(config, f, indent=2)
                        
                        console.print(f"  ✅ Sanitized {config_file}")
                    except Exception as e:
                        console.print(f"  ❌ Error sanitizing {config_file}: {e}")

def create_github_files():
    """Ensure all GitHub-related files are present."""
    console.print("[yellow]📁 Checking GitHub files...[/yellow]")
    
    required_files = [
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        ".gitignore",
        "requirements.txt",
        "requirements-dev.txt",
        "setup.py"
    ]
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            console.print(f"  ✅ {file_name} exists")
        else:
            console.print(f"  ❌ {file_name} missing")

def update_version_info():
    """Update version information in files."""
    console.print("[yellow]🔢 Updating version information...[/yellow]")
    
    version = "2.0.0"
    
    # Update main.py if it has version info
    main_file = Path("main.py")
    if main_file.exists():
        content = main_file.read_text()
        if "__version__" not in content:
            # Add version info
            lines = content.split('\n')
            # Insert after imports
            for i, line in enumerate(lines):
                if line.startswith('from') or line.startswith('import'):
                    continue
                else:
                    lines.insert(i, f'__version__ = "{version}"')
                    break
            
            main_file.write_text('\n'.join(lines))
            console.print(f"  ✅ Added version {version} to main.py")

def check_file_sizes():
    """Check for large files that might cause issues."""
    console.print("[yellow]📏 Checking file sizes...[/yellow]")
    
    large_files = []
    for file_path in Path(".").rglob("*"):
        if file_path.is_file():
            size = file_path.stat().st_size
            if size > 50 * 1024 * 1024:  # 50MB
                large_files.append((file_path, size))
    
    if large_files:
        console.print("  ⚠️ Large files found (>50MB):")
        for file_path, size in large_files:
            console.print(f"    {file_path}: {size / 1024 / 1024:.1f}MB")
        console.print("  Consider using Git LFS for these files")
    else:
        console.print("  ✅ No large files found")

def generate_git_commands(username):
    """Generate git commands for repository setup."""
    console.print(f"\n[bold green]🚀 Git Commands for Repository Setup[/bold green]")
    
    commands = f"""
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "feat: initial release of AutoJobAgent v2.0.0

- Enhanced Indeed scraper with 2025 anti-detection techniques
- Opera browser integration with persistent sessions
- Auto-login system with credential management
- AI-powered job matching with Ollama
- Multi-ATS support (Workday, iCIMS, Greenhouse, BambooHR)
- Real-time dashboard with WebSocket updates
- Comprehensive documentation and guides"

# Add remote origin
git remote add origin https://github.com/{username}/AutoJobAgent.git

# Push to GitHub
git branch -M main
git push -u origin main
"""
    
    console.print(commands)
    
    # Save to file
    with open("git_setup_commands.txt", "w") as f:
        f.write(commands.strip())
    
    console.print(f"[green]✅ Commands saved to git_setup_commands.txt[/green]")

def main():
    """Main preparation function."""
    console.print("[bold blue]🤖 AutoJobAgent GitHub Preparation Tool[/bold blue]")
    console.print("This tool will prepare your codebase for GitHub upload by:")
    console.print("• Removing sensitive data and browser sessions")
    console.print("• Sanitizing configuration files")
    console.print("• Checking required files")
    console.print("• Generating git setup commands")
    
    if not Confirm.ask("\nProceed with preparation?"):
        console.print("[yellow]Preparation cancelled.[/yellow]")
        return
    
    # Get GitHub username
    username = Prompt.ask("Enter your GitHub username")
    
    # Run preparation steps
    clean_sensitive_data()
    sanitize_profile_config()
    create_github_files()
    update_version_info()
    check_file_sizes()
    generate_git_commands(username)
    
    console.print("\n[bold green]✅ Preparation complete![/bold green]")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("1. Create a new repository on GitHub named 'AutoJobAgent'")
    console.print("2. Run the commands from git_setup_commands.txt")
    console.print("3. Follow the GITHUB_SETUP_GUIDE.md for detailed instructions")
    
    console.print(f"\n[cyan]Repository URL will be: https://github.com/{username}/AutoJobAgent[/cyan]")

if __name__ == "__main__":
    main()
