"""
CLI utility for managing skills and job titles.

Usage:
    python scripts/manage_skills.py add-skills --industry healthcare --category surgical_skills --skills "Laparoscopy,Endoscopy,Suturing"
    python scripts/manage_skills.py add-titles --category nursing --titles "Nurse Practitioner,Clinical Nurse Specialist"
    python scripts/manage_skills.py list-industries
    python scripts/manage_skills.py search --query "python"
    python scripts/manage_skills.py export --output skills_backup.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.skills_manager import get_skills_manager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def add_skills(args):
    """Add new skills to an industry category."""
    manager = get_skills_manager()
    skills = [s.strip() for s in args.skills.split(',')]
    
    manager.add_skills(args.industry, args.category, skills)
    
    console.print(f"✅ Added {len(skills)} skills to {args.industry}/{args.category}", style="green bold")
    console.print(f"Skills: {', '.join(skills)}", style="cyan")


def add_titles(args):
    """Add new job titles to a category."""
    manager = get_skills_manager()
    titles = [t.strip() for t in args.titles.split(',')]
    
    manager.add_job_titles(args.category, titles)
    
    console.print(f"✅ Added {len(titles)} job titles to {args.category}", style="green bold")
    console.print(f"Titles: {', '.join(titles)}", style="cyan")


def list_industries(args):
    """List all available industries and their skill counts."""
    manager = get_skills_manager()
    
    table = Table(title="Available Industries", show_header=True, header_style="bold magenta")
    table.add_column("Industry", style="cyan")
    table.add_column("Categories", justify="right", style="green")
    table.add_column("Total Skills", justify="right", style="yellow")
    
    for industry, categories in sorted(manager.industries.items()):
        skill_count = sum(len(skills) for skills in categories.values() if isinstance(skills, list))
        table.add_row(industry, str(len(categories)), str(skill_count))
    
    console.print(table)
    console.print(f"\n📊 Total Skills in Database: {len(manager.skills)}", style="bold")
    console.print(f"📊 Total Job Titles: {len(manager.job_titles)}", style="bold")


def list_categories(args):
    """List all categories for a specific industry."""
    manager = get_skills_manager()
    
    if args.industry not in manager.industries:
        console.print(f"❌ Industry '{args.industry}' not found", style="red bold")
        return
    
    industry_data = manager.industries[args.industry]
    
    table = Table(title=f"Categories in {args.industry}", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Skill Count", justify="right", style="green")
    
    for category, skills in sorted(industry_data.items()):
        if isinstance(skills, list):
            table.add_row(category, str(len(skills)))
    
    console.print(table)


def search_skills(args):
    """Search for skills matching a query."""
    manager = get_skills_manager()
    results = manager.search_skills(args.query)
    
    if not results:
        console.print(f"❌ No skills found matching '{args.query}'", style="red bold")
        return
    
    console.print(f"\n🔍 Found {len(results)} skills matching '{args.query}':\n", style="bold")
    
    # Group by first letter for better readability
    from itertools import groupby
    
    for letter, group in groupby(sorted(results), key=lambda x: x[0].upper()):
        skills = list(group)
        console.print(f"[bold cyan]{letter}:[/] {', '.join(skills)}")


def export_config(args):
    """Export current configuration to a backup file."""
    manager = get_skills_manager()
    
    export_data = {
        "industries": manager.industries,
        "job_titles": {
            "all_titles": sorted(list(manager.job_titles))
        },
        "statistics": {
            "total_skills": len(manager.skills),
            "total_titles": len(manager.job_titles),
            "total_industries": len(manager.industries)
        }
    }
    
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"✅ Exported configuration to {output_path}", style="green bold")
    console.print(f"📊 Total skills: {len(manager.skills)}", style="cyan")
    console.print(f"📊 Total titles: {len(manager.job_titles)}", style="cyan")


def show_stats(args):
    """Show comprehensive statistics about the skills database."""
    manager = get_skills_manager()
    
    console.print(Panel.fit(
        "[bold cyan]Skills Database Statistics[/]\n\n"
        f"[green]Total Skills:[/] {len(manager.skills)}\n"
        f"[green]Total Job Titles:[/] {len(manager.job_titles)}\n"
        f"[green]Total Industries:[/] {len(manager.industries)}\n",
        border_style="blue"
    ))
    
    # Most comprehensive industries
    table = Table(title="Industry Coverage", show_header=True, header_style="bold magenta")
    table.add_column("Industry", style="cyan")
    table.add_column("Skills", justify="right", style="green")
    
    industry_counts = []
    for industry, categories in manager.industries.items():
        skill_count = sum(len(skills) for skills in categories.values() if isinstance(skills, list))
        industry_counts.append((industry, skill_count))
    
    for industry, count in sorted(industry_counts, key=lambda x: x[1], reverse=True):
        table.add_row(industry, str(count))
    
    console.print("\n", table)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage skills and job titles for JobLens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add healthcare skills
  python scripts/manage_skills.py add-skills --industry healthcare --category surgical --skills "Laparoscopy,Endoscopy"
  
  # Add job titles
  python scripts/manage_skills.py add-titles --category nursing --titles "Nurse Practitioner,Clinical Nurse"
  
  # List all industries
  python scripts/manage_skills.py list-industries
  
  # Search for skills
  python scripts/manage_skills.py search --query python
  
  # Export configuration
  python scripts/manage_skills.py export --output backup.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add skills command
    add_skills_parser = subparsers.add_parser('add-skills', help='Add new skills to an industry')
    add_skills_parser.add_argument('--industry', required=True, help='Industry name (e.g., healthcare, technology)')
    add_skills_parser.add_argument('--category', required=True, help='Skill category (e.g., clinical_skills, programming)')
    add_skills_parser.add_argument('--skills', required=True, help='Comma-separated list of skills')
    
    # Add titles command
    add_titles_parser = subparsers.add_parser('add-titles', help='Add new job titles')
    add_titles_parser.add_argument('--category', required=True, help='Job category (e.g., nursing, engineering)')
    add_titles_parser.add_argument('--titles', required=True, help='Comma-separated list of job titles')
    
    # List industries command
    subparsers.add_parser('list-industries', help='List all available industries')
    
    # List categories command
    list_cat_parser = subparsers.add_parser('list-categories', help='List categories in an industry')
    list_cat_parser.add_argument('--industry', required=True, help='Industry name')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for skills')
    search_parser.add_argument('--query', required=True, help='Search query')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration to file')
    export_parser.add_argument('--output', default='skills_export.json', help='Output file path')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = {
        'add-skills': add_skills,
        'add-titles': add_titles,
        'list-industries': list_industries,
        'list-categories': list_categories,
        'search': search_skills,
        'export': export_config,
        'stats': show_stats,
    }
    
    commands[args.command](args)


if __name__ == '__main__':
    main()
