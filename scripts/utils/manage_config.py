#!/usr/bin/env python3
"""
Config Management Utility - Interactive tool for managing JobQst configuration files
Part of the Config-Driven Architecture Pattern

This utility allows non-developers to:
- Add/remove skills from skills_database.json
- Adjust matching weights in job_matching_config.json
- Update salary ranges and patterns
- View and validate configuration files

Usage:
    python scripts/utils/manage_config.py
    python scripts/utils/manage_config.py --add-skill "Python"
    python scripts/utils/manage_config.py --show-skills
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config_loader import ConfigLoader

console = Console()


class ConfigManager:
    """Interactive configuration manager"""
    
    def __init__(self):
        """Initialize config manager"""
        self.loader = ConfigLoader()
        self.config_dir = self.loader.config_dir
        console.print(f"[green]Config directory: {self.config_dir}[/green]")
    
    def show_skills(self, industry: str = None):
        """Display skills from skills_database.json"""
        skills_db = self.loader.load_config("skills_database.json")
        industries = skills_db.get("industries", {})
        
        if industry:
            # Show specific industry
            if industry not in industries:
                console.print(f"[red]Industry '{industry}' not found[/red]")
                return
            
            ind_data = industries[industry]
            skills = ind_data.get("skills", [])
            
            console.print(f"\n[bold cyan]{industry}[/bold cyan]")
            console.print(f"Name: {ind_data.get('name', 'N/A')}")
            console.print(f"Skills ({len(skills)}):")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Skill", style="cyan")
            
            for skill in sorted(skills):
                table.add_row(skill)
            
            console.print(table)
        else:
            # Show all industries summary
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Industry Key", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("# Skills", justify="right")
            table.add_column("# Role Patterns", justify="right")
            
            for ind_key, ind_data in industries.items():
                skills_count = len(ind_data.get("skills", []))
                roles_count = len(ind_data.get("role_patterns", []))
                
                table.add_row(
                    ind_key,
                    ind_data.get("name", "N/A"),
                    str(skills_count),
                    str(roles_count)
                )
            
            console.print("\n[bold]Skills Database Summary[/bold]")
            console.print(table)
    
    def add_skill(self, skill: str, industry: str):
        """Add a skill to an industry"""
        config_path = self.config_dir / "skills_database.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            skills_db = json.load(f)
        
        industries = skills_db.get("industries", {})
        
        if industry not in industries:
            console.print(f"[red]Industry '{industry}' not found[/red]")
            return
        
        skills = industries[industry].get("skills", [])
        
        if skill in skills:
            console.print(f"[yellow]Skill '{skill}' already exists in {industry}[/yellow]")
            return
        
        # Add skill
        skills.append(skill)
        skills.sort()
        industries[industry]["skills"] = skills
        
        # Save
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(skills_db, f, indent=2)
        
        console.print(f"[green]✓ Added '{skill}' to {industry}[/green]")
        
        # Clear cache
        self.loader.clear_cache()
    
    def remove_skill(self, skill: str, industry: str):
        """Remove a skill from an industry"""
        config_path = self.config_dir / "skills_database.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            skills_db = json.load(f)
        
        industries = skills_db.get("industries", {})
        
        if industry not in industries:
            console.print(f"[red]Industry '{industry}' not found[/red]")
            return
        
        skills = industries[industry].get("skills", [])
        
        if skill not in skills:
            console.print(f"[yellow]Skill '{skill}' not found in {industry}[/yellow]")
            return
        
        # Remove skill
        skills.remove(skill)
        industries[industry]["skills"] = skills
        
        # Save
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(skills_db, f, indent=2)
        
        console.print(f"[green]✓ Removed '{skill}' from {industry}[/green]")
        
        # Clear cache
        self.loader.clear_cache()
    
    def show_matching_weights(self):
        """Display matching weights"""
        config = self.loader.load_config("job_matching_config.json")
        weights = config.get("matching_weights", {})
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Weight", justify="right")
        table.add_column("Percentage", justify="right")
        
        for component, weight in weights.items():
            if component != "description":
                percentage = f"{weight * 100:.0f}%"
                table.add_row(component, f"{weight:.2f}", percentage)
        
        console.print("\n[bold]Matching Weights[/bold]")
        console.print(table)
    
    def update_matching_weight(self, component: str, new_weight: float):
        """Update a matching weight"""
        config_path = self.config_dir / "job_matching_config.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        weights = config.get("matching_weights", {})
        
        if component not in weights:
            console.print(f"[red]Component '{component}' not found[/red]")
            console.print(f"Available: {', '.join(k for k in weights.keys() if k != 'description')}")
            return
        
        old_weight = weights[component]
        weights[component] = new_weight
        
        # Save
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]✓ Updated {component}: {old_weight} → {new_weight}[/green]")
        
        # Clear cache
        self.loader.clear_cache()
    
    def list_configs(self):
        """List all available configuration files"""
        configs = self.loader.list_available_configs()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Config File", style="cyan")
        table.add_column("Version")
        table.add_column("Description", style="dim")
        
        for config_file in configs:
            try:
                config = self.loader.load_config(config_file)
                version = config.get("version", "N/A")
                description = config.get("description", "No description")
                table.add_row(config_file, version, description[:50])
            except Exception as e:
                table.add_row(config_file, "Error", str(e)[:50])
        
        console.print("\n[bold]Available Configuration Files[/bold]")
        console.print(table)
    
    def interactive_menu(self):
        """Show interactive menu"""
        while True:
            console.print("\n[bold cyan]JobQst Configuration Manager[/bold cyan]")
            console.print("1. Show all skills by industry")
            console.print("2. Show skills for specific industry")
            console.print("3. Add skill to industry")
            console.print("4. Remove skill from industry")
            console.print("5. Show matching weights")
            console.print("6. Update matching weight")
            console.print("7. List all config files")
            console.print("8. Exit")
            
            choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                self.show_skills()
            
            elif choice == "2":
                industry = Prompt.ask("Industry key (e.g., data_analytics)")
                self.show_skills(industry)
            
            elif choice == "3":
                industry = Prompt.ask("Industry key")
                skill = Prompt.ask("Skill name")
                self.add_skill(skill, industry)
            
            elif choice == "4":
                industry = Prompt.ask("Industry key")
                skill = Prompt.ask("Skill name")
                if Confirm.ask(f"Remove '{skill}' from {industry}?"):
                    self.remove_skill(skill, industry)
            
            elif choice == "5":
                self.show_matching_weights()
            
            elif choice == "6":
                self.show_matching_weights()
                component = Prompt.ask("Component to update")
                weight = float(Prompt.ask("New weight (0.0-1.0)"))
                self.update_matching_weight(component, weight)
            
            elif choice == "7":
                self.list_configs()
            
            elif choice == "8":
                console.print("[green]Goodbye![/green]")
                break


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="JobQst Configuration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Skills management
    parser.add_argument("--show-skills", action="store_true",
                       help="Show all skills")
    parser.add_argument("--industry", type=str,
                       help="Filter by industry")
    parser.add_argument("--add-skill", type=str,
                       help="Add a skill")
    parser.add_argument("--remove-skill", type=str,
                       help="Remove a skill")
    
    # Matching weights
    parser.add_argument("--show-weights", action="store_true",
                       help="Show matching weights")
    parser.add_argument("--update-weight", type=str,
                       help="Component to update")
    parser.add_argument("--weight-value", type=float,
                       help="New weight value")
    
    # General
    parser.add_argument("--list-configs", action="store_true",
                       help="List all config files")
    parser.add_argument("--interactive", action="store_true",
                       help="Interactive menu")
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    # Handle command line arguments
    if args.show_skills:
        manager.show_skills(args.industry)
    
    elif args.add_skill:
        if not args.industry:
            console.print("[red]Error: --industry required[/red]")
            sys.exit(1)
        manager.add_skill(args.add_skill, args.industry)
    
    elif args.remove_skill:
        if not args.industry:
            console.print("[red]Error: --industry required[/red]")
            sys.exit(1)
        manager.remove_skill(args.remove_skill, args.industry)
    
    elif args.show_weights:
        manager.show_matching_weights()
    
    elif args.update_weight:
        if args.weight_value is None:
            console.print("[red]Error: --weight-value required[/red]")
            sys.exit(1)
        manager.update_matching_weight(args.update_weight, args.weight_value)
    
    elif args.list_configs:
        manager.list_configs()
    
    else:
        # Default to interactive menu
        manager.interactive_menu()


if __name__ == "__main__":
    main()
