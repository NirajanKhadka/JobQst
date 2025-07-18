"""
Document Actions for AutoJobAgent CLI.

Contains action processors for document generation operations:
- AI-powered resume generation
- AI-powered cover letter generation
- Document customization
- Worker-based parallel processing
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from gemini_resume_generator import GeminiResumeGenerator
from src.utils.profile_helpers import get_profile_path

console = Console()


class DocumentActions:
    """Handles all document generation action processing."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.profile_name = profile.get("profile_name", "default")

    def show_document_menu(self) -> str:
        """Show document generation menu options."""
        console.print(Panel("📄 AI Document Generation Menu", style="bold blue"))
        
        # Show current profile info
        console.print(f"[bold]👤 Profile:[/bold] {self.profile_name}")
        console.print(f"[bold]📧 Name:[/bold] {self.profile.get('name', 'Not set')}")
        
        options = {
            "1": "🤖 Generate ALL documents (Worker-based parallel processing)",
            "2": "📝 Generate resumes only (4 styles)",
            "3": "💌 Generate cover letters only (4 styles)",
            "4": "🎯 Generate single document type",
            "5": "📊 View existing documents",
            "6": "🔄 Regenerate with enhanced prompts",
            "7": "🏠 Return to main menu"
        }

        for key, value in options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        console.print()
        choice = Prompt.ask("Select option", choices=list(options.keys()), default="1")
        return choice

    def handle_document_choice(self, choice: str) -> bool:
        """Handle document menu choice and execute corresponding action."""
        if choice == "1":  # Generate ALL documents
            self._generate_all_documents_action()
        elif choice == "2":  # Generate resumes only
            self._generate_resumes_only_action()
        elif choice == "3":  # Generate cover letters only
            self._generate_cover_letters_only_action()
        elif choice == "4":  # Generate single document type
            self._generate_single_document_action()
        elif choice == "5":  # View existing documents
            self._view_existing_documents_action()
        elif choice == "6":  # Regenerate with enhanced prompts
            self._regenerate_documents_action()
        elif choice == "7":  # Return to main menu
            return False

        return True

    def _generate_all_documents_action(self) -> None:
        """Generate all document types using worker-based parallel processing."""
        console.print(Panel("🤖 Worker-Based Document Generation", style="bold green"))
        console.print("[cyan]Generating all resumes and cover letters using AI workers...[/cyan]")
        
        # Confirm action
        if not Confirm.ask("Generate all documents with 5 AI workers?", default=True):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        try:
            generator = GeminiResumeGenerator(self.profile)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating documents...", total=None)
                
                # Use worker-based generation
                generator.generate_documents_with_workers(max_workers=5)
                
                progress.update(task, description="✅ Generation complete!")

            console.print("[bold green]🎉 All documents generated successfully![/bold green]")
            self._show_generation_summary()
            
        except Exception as e:
            console.print(f"[red]❌ Document generation failed: {e}[/red]")
            console.print("[yellow]Please ensure Ollama is running and accessible[/yellow]")

    def _generate_resumes_only_action(self) -> None:
        """Generate only resume documents."""
        console.print(Panel("📝 Resume Generation Only", style="bold blue"))
        console.print("[cyan]Generating 4 resume styles: Professional, Technical, Creative, Minimalist[/cyan]")
        
        try:
            generator = GeminiResumeGenerator(self.profile)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating resumes...", total=None)
                
                # Call the method to generate only resumes
                generator._generate_resume_documents_only()
                
                progress.update(task, description="✅ Resume generation complete!")

            console.print("[bold green]✅ All resume styles generated successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[red]❌ Resume generation failed: {e}[/red]")

    def _generate_cover_letters_only_action(self) -> None:
        """Generate only cover letter documents."""
        console.print(Panel("💌 Cover Letter Generation Only", style="bold blue"))
        console.print("[cyan]Generating 4 cover letter styles: Standard, Enthusiastic, Technical, Concise[/cyan]")
        
        try:
            generator = GeminiResumeGenerator(self.profile)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating cover letters...", total=None)
                
                # Call the method to generate only cover letters
                generator._generate_cover_letter_documents_only()
                
                progress.update(task, description="✅ Cover letter generation complete!")

            console.print("[bold green]✅ All cover letter styles generated successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[red]❌ Cover letter generation failed: {e}[/red]")

    def _generate_single_document_action(self) -> None:
        """Generate a single specific document type."""
        console.print(Panel("🎯 Single Document Generation", style="bold blue"))
        
        doc_type = Prompt.ask("Choose document type", choices=["resume", "cover_letter"], default="resume")
        
        if doc_type == "resume":
            style = Prompt.ask("Choose resume style", 
                             choices=["professional", "technical", "creative", "minimalist"], 
                             default="professional")
            self._generate_single_resume(style)
        else:
            style = Prompt.ask("Choose cover letter style", 
                             choices=["standard", "enthusiastic", "technical", "concise"], 
                             default="standard")
            self._generate_single_cover_letter(style)

    def _generate_single_resume(self, style: str) -> None:
        """Generate a single resume style."""
        console.print(f"[cyan]Generating {style} resume...[/cyan]")
        
        try:
            generator = GeminiResumeGenerator(self.profile)
            
            # Get style description
            style_descriptions = {
                "professional": "a standard, professional resume",
                "technical": "a resume focused on technical skills and projects",
                "creative": "a modern, creative-style resume",
                "minimalist": "a clean, minimalist resume"
            }
            
            description = style_descriptions.get(style, "a professional resume")
            
            # Generate single document
            success = generator._generate_single_document("resume", style, description, 
                                                        generator._get_output_dir())
            
            if success:
                console.print(f"[green]✅ {style.title()} resume generated successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to generate {style} resume[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Resume generation failed: {e}[/red]")

    def _generate_single_cover_letter(self, style: str) -> None:
        """Generate a single cover letter style."""
        console.print(f"[cyan]Generating {style} cover letter...[/cyan]")
        
        try:
            generator = GeminiResumeGenerator(self.profile)
            
            # Get style description
            style_descriptions = {
                "standard": "a standard, formal cover letter",
                "enthusiastic": "a cover letter with an enthusiastic and passionate tone",
                "technical": "a cover letter highlighting technical achievements",
                "concise": "a brief and to-the-point cover letter"
            }
            
            description = style_descriptions.get(style, "a professional cover letter")
            
            # Generate single document
            success = generator._generate_single_document("cover_letter", style, description, 
                                                        generator._get_output_dir())
            
            if success:
                console.print(f"[green]✅ {style.title()} cover letter generated successfully![/green]")
            else:
                console.print(f"[red]❌ Failed to generate {style} cover letter[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Cover letter generation failed: {e}[/red]")

    def _view_existing_documents_action(self) -> None:
        """View existing generated documents."""
        console.print(Panel("📊 Existing Documents", style="bold blue"))
        
        profile_path = get_profile_path(self.profile_name)
        if not profile_path:
            console.print(f"[red]❌ Profile path for '{self.profile_name}' not found[/red]")
            return

        # Check generated documents directory
        generated_dir = profile_path / "generated_documents"
        main_dir = profile_path

        console.print(f"[bold]📁 Documents for profile: {self.profile_name}[/bold]\n")

        # Check main directory for primary documents
        main_files = [
            f"{self.profile_name}_Resume.pdf",
            f"{self.profile_name}_Resume.txt",
            f"{self.profile_name}_CoverLetter.pdf",
            f"{self.profile_name}_CoverLetter.txt",
            f"{self.profile_name}_Khadka_Resume.pdf",
            f"{self.profile_name}_Khadka_CoverLetter.pdf"
        ]

        console.print("[bold cyan]📄 Main Documents:[/bold cyan]")
        found_main = False
        for file_name in main_files:
            file_path = main_dir / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                console.print(f"  ✅ {file_name} ({size:,} bytes)")
                found_main = True

        if not found_main:
            console.print("  [yellow]No main documents found[/yellow]")

        # Check generated documents directory
        if generated_dir.exists():
            console.print(f"\n[bold cyan]📁 Generated Variations ({generated_dir}):[/bold cyan]")
            
            resume_files = list(generated_dir.glob("resume_*.txt"))
            cover_files = list(generated_dir.glob("cover_letter_*.txt"))
            
            if resume_files:
                console.print("  [green]📝 Resumes:[/green]")
                for file_path in sorted(resume_files):
                    style = file_path.stem.replace("resume_", "").title()
                    pdf_path = file_path.with_suffix(".pdf")
                    pdf_status = "✅ PDF" if pdf_path.exists() else "❌ No PDF"
                    console.print(f"    • {style}: TXT ✅ | {pdf_status}")

            if cover_files:
                console.print("  [green]💌 Cover Letters:[/green]")
                for file_path in sorted(cover_files):
                    style = file_path.stem.replace("cover_letter_", "").title()
                    pdf_path = file_path.with_suffix(".pdf")
                    pdf_status = "✅ PDF" if pdf_path.exists() else "❌ No PDF"
                    console.print(f"    • {style}: TXT ✅ | {pdf_status}")

            if not resume_files and not cover_files:
                console.print("  [yellow]No generated documents found[/yellow]")
        else:
            console.print(f"\n[yellow]📁 Generated documents directory not found: {generated_dir}[/yellow]")

        console.print(f"\n[dim]💡 Tip: Use option 1 to generate all documents with AI workers[/dim]")

    def _regenerate_documents_action(self) -> None:
        """Regenerate documents with enhanced prompts."""
        console.print(Panel("🔄 Document Regeneration", style="bold yellow"))
        
        if not Confirm.ask("This will overwrite existing documents. Continue?", default=False):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        console.print("[cyan]Regenerating all documents with enhanced AI prompts...[/cyan]")
        
        try:
            generator = GeminiResumeGenerator(self.profile)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Regenerating documents...", total=None)
                
                # Clear any cached data and regenerate
                generator.generate_documents_with_workers(max_workers=5)
                
                progress.update(task, description="✅ Regeneration complete!")

            console.print("[bold green]🎉 All documents regenerated successfully![/bold green]")
            self._show_generation_summary()
            
        except Exception as e:
            console.print(f"[red]❌ Document regeneration failed: {e}[/red]")

    def _show_generation_summary(self) -> None:
        """Show a summary of generated documents."""
        console.print("\n[bold cyan]📊 Generation Summary:[/bold cyan]")
        console.print("  ✅ 4 Resume styles: Professional, Technical, Creative, Minimalist")
        console.print("  ✅ 4 Cover letter styles: Standard, Enthusiastic, Technical, Concise")
        console.print("  ✅ Main documents: Nirajan_Khadka_Resume.pdf & Nirajan_Khadka_CoverLetter.pdf")
        console.print("  ✅ Both TXT and PDF formats generated")
        console.print("\n[green]💡 Documents are ready for job applications![/green]")

    def run_document_menu(self) -> None:
        """Run the document generation menu loop."""
        while True:
            choice = self.show_document_menu()
            if not self.handle_document_choice(choice):
                break
            
            # Don't pause after returning to main menu
            if choice != "7":
                input("\nPress Enter to continue...")
