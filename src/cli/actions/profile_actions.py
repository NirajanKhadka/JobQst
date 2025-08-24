"""
Profile Actions for AutoJobAgent CLI.

Contains action processors for profile management:
- Create new profiles from resumes
- Watch folders for resume uploads
- Auto-scan resumes
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

console = Console()


class ResumeWatcher(FileSystemEventHandler):
    """Watch for resume files in profile folder."""
    
    def __init__(self, profile_path: str, profile_name: str):
        self.profile_path = profile_path
        self.profile_name = profile_name
        self.processed_files = set()
        
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = event.src_path
        file_ext = Path(file_path).suffix.lower()
        
        # Check if it's a resume file
        if file_ext in ['.pdf', '.doc', '.docx', '.txt']:
            if file_path not in self.processed_files:
                console.print(f"📄 [green]Resume detected: {Path(file_path).name}[/green]")
                time.sleep(1)  # Wait for file to be fully written
                self._process_resume(file_path)
                self.processed_files.add(file_path)
    
    def _process_resume(self, resume_path: str):
        """Process the detected resume file."""
        try:
            from src.utils.auto_profile_creator import AutoProfileCreator
            
            console.print("🤖 [cyan]Auto-scanning resume...[/cyan]")
            
            creator = AutoProfileCreator()
            result = creator.create_profile_from_resume(
                resume_path=resume_path,
                profile_name=self.profile_name
            )
            
            if result['success']:
                console.print("✅ [green]Profile auto-created successfully![/green]")
                console.print(f"📝 [cyan]Keywords extracted: {len(result.get('keywords', []))}[/cyan]")
                console.print(f"🎯 [cyan]Skills identified: {len(result.get('skills', []))}[/cyan]")
                
                # Show first few keywords
                keywords = result.get('keywords', [])
                if keywords:
                    console.print(f"🔍 [dim]Top keywords: {', '.join(keywords[:5])}...[/dim]")
            else:
                console.print(f"❌ [red]Failed to process resume: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"❌ [red]Error processing resume: {str(e)}[/red]")


class ProfileActions:
    """Handles all profile action processing."""

    def __init__(self, profile: Dict):
        self.profile = profile

    def create_profile_action(self, args) -> bool:
        """Create new profile with optional resume watching."""
        if not args.name:
            console.print("❌ [red]Profile name is required. Use --name argument.[/red]")
            return False
            
        profile_name = args.name
        profile_path = Path("profiles") / profile_name
        
        # Check if profile already exists
        if profile_path.exists():
            if not Confirm.ask(f"Profile '{profile_name}' already exists. Overwrite?"):
                return False
        
        # Create profile directory
        profile_path.mkdir(parents=True, exist_ok=True)
        console.print(f"📁 [green]Created profile directory: {profile_path}[/green]")
        
        # Create basic profile structure
        self._create_basic_profile(profile_path, profile_name)
        
        # If resume path provided, process immediately
        if args.resume_path:
            self._process_resume_file(args.resume_path, profile_name)
            return True
            
        # If watch mode, set up file watching
        if args.watch:
            return self._start_resume_watching(str(profile_path), profile_name)
        else:
            # Just show instructions
            self._show_resume_instructions(profile_path)
            return True

    def scan_resume_action(self, args) -> bool:
        """Scan resume in existing profile."""
        profile_name = args.profile
        profile_path = Path("profiles") / profile_name
        
        if not profile_path.exists():
            console.print(f"❌ [red]Profile '{profile_name}' not found.[/red]")
            return False
            
        # Look for resume files in the profile folder
        resume_files = []
        for ext in ['*.pdf', '*.doc', '*.docx', '*.txt']:
            resume_files.extend(profile_path.glob(ext))
            
        if not resume_files:
            console.print(f"❌ [red]No resume files found in {profile_path}[/red]")
            console.print("📝 [cyan]Supported formats: PDF, DOC, DOCX, TXT[/cyan]")
            return False
            
        # If multiple files, let user choose
        if len(resume_files) > 1:
            console.print("\n[bold]Multiple resume files found:[/bold]")
            for i, file in enumerate(resume_files, 1):
                console.print(f"  {i}. {file.name}")
                
            choice = Prompt.ask(
                "Select file to scan",
                choices=[str(i) for i in range(1, len(resume_files) + 1)],
                default="1"
            )
            resume_file = resume_files[int(choice) - 1]
        else:
            resume_file = resume_files[0]
            
        console.print(f"📄 [cyan]Scanning resume: {resume_file.name}[/cyan]")
        return self._process_resume_file(str(resume_file), profile_name)

    def _create_basic_profile(self, profile_path: Path, profile_name: str):
        """Create basic profile JSON structure."""
        basic_profile = {
            "profile_name": profile_name,
            "name": profile_name,
            "email": "",
            "keywords": [],
            "skills": [],
            "experience_level": "entry",
            "locations": ["United States"],
            "job_sites": ["indeed", "linkedin", "glassdoor"],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "auto_generated": True
        }
        
        # Save basic profile
        profile_file = profile_path / f"{profile_name}.json"
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(basic_profile, f, indent=2)
            
        console.print(f"📄 [green]Created basic profile: {profile_file.name}[/green]")

    def _process_resume_file(self, resume_path: str, profile_name: str) -> bool:
        """Process a specific resume file."""
        try:
            from src.utils.auto_profile_creator import AutoProfileCreator
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Processing resume...", total=None)
                
                creator = AutoProfileCreator()
                result = creator.create_profile_from_resume(
                    resume_path=resume_path,
                    profile_name=profile_name
                )
                
                progress.update(task, description="✅ Complete!")
                
            if result['success']:
                console.print("🎉 [green]Profile enhanced successfully![/green]")
                
                # Show extraction results
                keywords = result.get('keywords', [])
                skills = result.get('skills', [])
                
                console.print(f"🔍 [cyan]Keywords extracted: {len(keywords)}[/cyan]")
                console.print(f"🎯 [cyan]Skills identified: {len(skills)}[/cyan]")
                
                if keywords:
                    console.print(f"📝 [dim]Top keywords: {', '.join(keywords[:10])}[/dim]")
                if skills:
                    console.print(f"💼 [dim]Key skills: {', '.join(skills[:10])}[/dim]")
                    
                return True
            else:
                console.print(f"❌ [red]Failed: {result.get('error', 'Unknown error')}[/red]")
                return False
                
        except Exception as e:
            console.print(f"❌ [red]Error: {str(e)}[/red]")
            return False

    def _start_resume_watching(self, profile_path: str, profile_name: str) -> bool:
        """Start watching profile folder for resume files."""
        console.print("\n" + "="*60)
        console.print(Panel(
            f"👀 [bold green]WATCHING FOR RESUME FILES[/bold green]\n\n"
            f"📁 Profile folder: [cyan]{profile_path}[/cyan]\n"
            f"📄 Drop your resume file here (PDF, DOC, DOCX, TXT)\n"
            f"🤖 It will be automatically processed!\n\n"
            f"[dim]Press Ctrl+C to stop watching[/dim]",
            title=f"Profile: {profile_name}",
            border_style="green"
        ))
        
        # Set up file watcher
        event_handler = ResumeWatcher(profile_path, profile_name)
        observer = Observer()
        observer.schedule(event_handler, profile_path, recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            console.print("\n🛑 [yellow]Stopped watching for files.[/yellow]")
            
        observer.join()
        return True

    def _show_resume_instructions(self, profile_path: Path):
        """Show instructions for manual resume placement."""
        console.print("\n" + "="*60)
        console.print(Panel(
            f"📁 [bold]Profile created successfully![/bold]\n\n"
            f"📂 Profile folder: [cyan]{profile_path}[/cyan]\n\n"
            f"📄 [yellow]Next Steps:[/yellow]\n"
            f"1. Copy your resume file to the profile folder\n"
            f"2. Run: [cyan]python main.py --action scan-resume {profile_path.name}[/cyan]\n\n"
            f"🔧 [green]Supported formats:[/green] PDF, DOC, DOCX, TXT",
            title="Ready for Resume",
            border_style="blue"
        ))
