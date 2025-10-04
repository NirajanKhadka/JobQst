#!/usr/bin/env python3
"""
Skills Database Manager - Add/update industries without touching code

Usage:
    # View all industries
    python scripts/utils/manage_skills_db.py list
    
    # Add new industry
    python scripts/utils/manage_skills_db.py add "Marketing Analytics" \
        --skills "Google Analytics,SEO,SEM,Conversion Rate Optimization" \
        --roles "Marketing Analyst,Digital Marketing Analyst" \
        --keywords "Marketing,Analytics,Digital Marketing"
    
    # View specific industry
    python scripts/utils/manage_skills_db.py show data_analytics
    
    # Export to CSV for bulk editing
    python scripts/utils/manage_skills_db.py export industries.csv
"""

import json
import sys
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table

console = Console()


class SkillsDatabaseManager:
    """Manage skills database without code changes."""
    
    def __init__(self, config_path: str = "config/skills_database.json"):
        self.config_path = Path(config_path)
        self.load_database()
    
    def load_database(self):
        """Load skills database."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
    
    def save_database(self):
        """Save skills database."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2)
        console.print(f"[green]✅ Saved to {self.config_path}[/green]")
    
    def list_industries(self):
        """List all industries."""
        table = Table(title="📊 Industries in Database", show_header=True)
        table.add_column("Key", style="cyan", width=30)
        table.add_column("Name", style="green", width=40)
        table.add_column("Skills", style="yellow", justify="right")
        table.add_column("Roles", style="magenta", justify="right")
        
        for key, data in sorted(self.db['industries'].items()):
            table.add_row(
                key,
                data['name'],
                str(len(data['skills'])),
                str(len(data.get('role_patterns', [])))
            )
        
        console.print(table)
        console.print(f"\n[bold]Total Industries:[/bold] {len(self.db['industries'])}")
    
    def show_industry(self, industry_key: str):
        """Show details of specific industry."""
        if industry_key not in self.db['industries']:
            console.print(f"[red]❌ Industry '{industry_key}' not found[/red]")
            return
        
        data = self.db['industries'][industry_key]
        
        console.print(f"\n[bold cyan]📋 {data['name']}[/bold cyan]")
        console.print(f"[dim]Key: {industry_key}[/dim]\n")
        
        console.print(f"[yellow]Skills ({len(data['skills'])}):[/yellow]")
        for i in range(0, len(data['skills']), 5):
            skills_chunk = data['skills'][i:i+5]
            console.print(f"  {', '.join(skills_chunk)}")
        
        console.print(f"\n[yellow]Role Patterns ({len(data.get('role_patterns', []))}):[/yellow]")
        for role in data.get('role_patterns', []):
            console.print(f"  • {role}")
        
        console.print(f"\n[yellow]Keywords ({len(data.get('keywords', []))}):[/yellow]")
        for keyword in data.get('keywords', []):
            console.print(f"  • {keyword}")
    
    def add_industry(self, name: str, key: str = None, skills: List[str] = None,
                     roles: List[str] = None, keywords: List[str] = None):
        """Add new industry to database."""
        if key is None:
            key = name.lower().replace(' ', '_').replace('&', 'and')
        
        if key in self.db['industries']:
            console.print(f"[yellow]⚠️  Industry '{key}' already exists. Use update command.[/yellow]")
            return
        
        self.db['industries'][key] = {
            'name': name,
            'skills': skills or [],
            'role_patterns': roles or [],
            'keywords': keywords or []
        }
        
        self.save_database()
        console.print(f"[green]✅ Added industry: {name}[/green]")
    
    def export_csv(self, output_path: str):
        """Export industries to CSV for bulk editing."""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Industry Key', 'Industry Name', 'Skills (comma-separated)', 
                           'Role Patterns (comma-separated)', 'Keywords (comma-separated)'])
            
            for key, data in sorted(self.db['industries'].items()):
                writer.writerow([
                    key,
                    data['name'],
                    ','.join(data['skills']),
                    ','.join(data.get('role_patterns', [])),
                    ','.join(data.get('keywords', []))
                ])
        
        console.print(f"[green]✅ Exported to {output_path}[/green]")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        console.print("[yellow]Usage:[/yellow]")
        console.print("  python manage_skills_db.py list")
        console.print("  python manage_skills_db.py show <industry_key>")
        console.print("  python manage_skills_db.py add <name> --skills <list> --roles <list>")
        console.print("  python manage_skills_db.py export <output.csv>")
        return
    
    manager = SkillsDatabaseManager()
    command = sys.argv[1]
    
    if command == "list":
        manager.list_industries()
    
    elif command == "show":
        if len(sys.argv) < 3:
            console.print("[red]❌ Usage: show <industry_key>[/red]")
            return
        manager.show_industry(sys.argv[2])
    
    elif command == "add":
        if len(sys.argv) < 3:
            console.print("[red]❌ Usage: add <name> --skills <list>[/red]")
            return
        
        name = sys.argv[2]
        skills = []
        roles = []
        keywords = []
        
        # Parse arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--skills' and i + 1 < len(sys.argv):
                skills = [s.strip() for s in sys.argv[i+1].split(',')]
                i += 2
            elif sys.argv[i] == '--roles' and i + 1 < len(sys.argv):
                roles = [r.strip() for r in sys.argv[i+1].split(',')]
                i += 2
            elif sys.argv[i] == '--keywords' and i + 1 < len(sys.argv):
                keywords = [k.strip() for k in sys.argv[i+1].split(',')]
                i += 2
            else:
                i += 1
        
        manager.add_industry(name, skills=skills, roles=roles, keywords=keywords)
    
    elif command == "export":
        if len(sys.argv) < 3:
            console.print("[red]❌ Usage: export <output.csv>[/red]")
            return
        manager.export_csv(sys.argv[2])
    
    else:
        console.print(f"[red]❌ Unknown command: {command}[/red]")


if __name__ == "__main__":
    main()
