#!/usr/bin/env python3
"""
Multi-Agent Job Application Orchestrator
Coordinates three agents:
1. Application Agent - Applies to jobs and marks as 'pending_verification'
2. Background Gmail Agent - Monitors Gmail and verifies applications
3. Database Agent - Updates job status based on Gmail confirmations
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt, Confirm

from Improved_application_agent import ImprovedApplicationAgent, run_application_agent
from background_gmail_monitor import BackgroundGmailMonitor
from src.core.job_database import get_job_db

console = Console()


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents for automated job applications:
    - Application Agent: Applies to jobs
    - Gmail Monitor: Verifies applications via email
    - Database Manager: Updates job statuses
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the multi-agent orchestrator."""
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)

        # Agent instances
        self.application_agent = None
        self.gmail_monitor = None

        # Orchestrator settings
        self.gmail_check_interval = 60  # Check Gmail every 60 seconds
        self.application_batch_size = 5  # Apply to 5 jobs at a time

        # Statistics
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "applications_submitted": 0,
            "applications_verified": 0,
            "applications_failed": 0,
            "gmail_checks": 0,
            "total_runtime": 0,
        }

    async def start_multi_agent_system(
        self, max_applications: int = 20, run_gmail_monitor: bool = True, enhance_jobs: bool = True
    ) -> None:
        """
        Start the complete multi-agent job application system.

        Args:
            max_applications: Maximum number of jobs to apply to
            run_gmail_monitor: Whether to run background Gmail monitoring
            enhance_jobs: Whether to enhance job data before applying
        """
        console.print(Panel.fit("🤖 MULTI-AGENT JOB APPLICATION SYSTEM", style="bold blue"))
        console.print(f"[cyan]Profile: {self.profile_name}[/cyan]")
        console.print(f"[cyan]Max Applications: {max_applications}[/cyan]")
        console.print(
            f"[cyan]Gmail Monitoring: {'✅ Enabled' if run_gmail_monitor else '❌ Disabled'}[/cyan]"
        )
        console.print(
            f"[cyan]Job Enhancement: {'✅ Enabled' if enhance_jobs else '❌ Disabled'}[/cyan]"
        )

        start_time = time.time()

        try:
            # Show system overview
            # self._display_system_overview()

            if not Confirm.ask("Start the multi-agent system?"):
                return

            # Option 1: Run agents sequentially (recommended for first time)
            if Confirm.ask("Run agents sequentially? (Recommended for first time)", default=True):
                await self._run_sequential_mode(max_applications, enhance_jobs, run_gmail_monitor)
            else:
                # Option 2: Run agents in parallel (Improved)
                await self._run_parallel_mode(max_applications, enhance_jobs, run_gmail_monitor)

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ Multi-agent system stopped by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]❌ Multi-agent system error: {e}[/red]")
        finally:
            # Final statistics
            total_runtime = time.time() - start_time
            self.stats["total_runtime"] = total_runtime
            self._display_final_statistics()

    def _display_system_overview(self) -> None:
        """Display system overview and agent descriptions."""
        console.print("\n[bold]🤖 AGENT OVERVIEW:[/bold]")

        agents_table = Table()
        agents_table.add_column("Agent", style="cyan")
        agents_table.add_column("Function", style="green")
        agents_table.add_column("Status Updates", style="yellow")

        agents_table.add_row(
            "🎯 Application Agent",
            "Scrapes job data, modifies resume/cover letter, applies to jobs",
            "pending_verification → failed",
        )
        agents_table.add_row(
            "📧 Gmail Monitor",
            "Monitors Gmail for confirmation emails, matches with applications",
            "pending_verification → applied",
        )
        agents_table.add_row(
            "💾 Database Manager",
            "Updates job statuses based on agent results",
            "Maintains data consistency",
        )

        console.print(agents_table)

        console.print("\n[bold]📊 CURRENT DATABASE STATUS:[/bold]")
        stats = self.db.get_stats()
        console.print(f"• Total Jobs: {stats.get('total_jobs', 0)}")
        console.print(f"• Unapplied Jobs: {stats.get('unapplied_jobs', 0)}")
        console.print(f"• Applied Jobs: {stats.get('applied_jobs', 0)}")

    async def _run_sequential_mode(
        self, max_applications: int, enhance_jobs: bool, run_gmail_monitor: bool
    ) -> None:
        """Run agents sequentially (safer, easier to debug)."""
        console.print(Panel.fit("🔄 SEQUENTIAL MODE", style="bold green"))

        # Step 1: Run Application Agent
        console.print("\n[bold]Step 1: Running Application Agent[/bold]")
        application_results = await self._run_application_agent(max_applications, enhance_jobs)

        if not application_results:
            console.print("[yellow]No applications submitted, skipping Gmail monitoring[/yellow]")
            return

        # Step 2: Run Gmail Monitor (if enabled)
        if run_gmail_monitor:
            console.print("\n[bold]Step 2: Starting Gmail Monitor[/bold]")
            console.print(
                "[yellow]Gmail monitor will run for 10 minutes to check for confirmations[/yellow]"
            )

            if Confirm.ask("Start Gmail monitoring now?"):
                await self._run_gmail_monitor(duration_minutes=10)

        # Step 3: Show final results
        console.print("\n[bold]Step 3: Final Results[/bold]")
        self._show_application_status_summary()

    async def _run_parallel_mode(
        self, max_applications: int, enhance_jobs: bool, run_gmail_monitor: bool
    ) -> None:
        """Run agents in parallel (Improved mode)."""
        console.print(Panel.fit("⚡ PARALLEL MODE", style="bold yellow"))
        console.print("[yellow]⚠️ Improved mode: Agents will run simultaneously[/yellow]")

        tasks = []

        # Start Gmail monitor in background
        if run_gmail_monitor:
            gmail_task = asyncio.create_task(self._run_gmail_monitor_background())
            tasks.append(gmail_task)

        # Run application agent
        app_task = asyncio.create_task(self._run_application_agent(max_applications, enhance_jobs))
        tasks.append(app_task)

        # Wait for application agent to complete
        await app_task

        # Let Gmail monitor run for a bit longer
        if run_gmail_monitor:
            console.print("[cyan]Letting Gmail monitor run for 5 more minutes...[/cyan]")
            await asyncio.sleep(300)  # 5 minutes
            gmail_task.cancel()

        # Show results
        self._show_application_status_summary()

    async def _run_application_agent(self, max_applications: int, enhance_jobs: bool) -> List:
        """Run the application agent."""
        try:
            console.print(
                f"[cyan]🎯 Starting application agent for {max_applications} jobs...[/cyan]"
            )

            results = await run_application_agent(
                profile_name=self.profile_name,
                limit=max_applications,
                enhance_jobs=enhance_jobs,
                modify_documents=True,
            )

            # Update statistics
            for result in results:
                if result.status == "pending_verification":
                    self.stats["applications_submitted"] += 1
                elif result.status == "failed":
                    self.stats["applications_failed"] += 1

            console.print(
                f"[green]✅ Application agent completed: {len(results)} jobs processed[/green]"
            )
            return results

        except Exception as e:
            console.print(f"[red]❌ Application agent failed: {e}[/red]")
            return []

    async def _run_gmail_monitor(self, duration_minutes: int = 10) -> None:
        """Run Gmail monitor for specified duration."""
        try:
            console.print(
                f"[cyan]📧 Starting Gmail monitor for {duration_minutes} minutes...[/cyan]"
            )

            monitor = BackgroundGmailMonitor(self.profile_name)

            # Create a task that will run for the specified duration
            monitor_task = asyncio.create_task(
                monitor.start_monitoring(check_interval=self.gmail_check_interval)
            )

            # Wait for specified duration
            await asyncio.sleep(duration_minutes * 60)

            # Stop monitoring
            monitor.stop_monitoring()

            # Get statistics
            monitor_stats = monitor.get_stats()
            self.stats["gmail_checks"] = monitor_stats.get("emails_checked", 0)
            self.stats["applications_verified"] = monitor_stats.get("jobs_verified", 0)

            console.print(
                f"[green]✅ Gmail monitor completed: {monitor_stats.get('confirmations_found', 0)} confirmations found[/green]"
            )

        except Exception as e:
            console.print(f"[red]❌ Gmail monitor failed: {e}[/red]")

    async def _run_gmail_monitor_background(self) -> None:
        """Run Gmail monitor in background (for parallel mode)."""
        try:
            monitor = BackgroundGmailMonitor(self.profile_name)
            await monitor.start_monitoring(check_interval=self.gmail_check_interval)
        except asyncio.CancelledError:
            console.print("[yellow]📧 Gmail monitor stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Background Gmail monitor error: {e}[/red]")

    def _show_application_status_summary(self) -> None:
        """Show summary of application statuses."""
        try:
            # Get current job statistics
            stats = self.db.get_stats()

            console.print("\n[bold]📊 APPLICATION STATUS SUMMARY:[/bold]")

            status_table = Table(title="Job Application Status")
            status_table.add_column("Status", style="cyan")
            status_table.add_column("Count", style="green")
            status_table.add_column("Description", style="yellow")

            status_table.add_row(
                "Applied", str(stats.get("applied_jobs", 0)), "Confirmed via Gmail"
            )
            status_table.add_row("Pending Verification", "?", "Waiting for Gmail confirmation")
            status_table.add_row(
                "Failed", str(self.stats["applications_failed"]), "Application failed"
            )
            status_table.add_row(
                "Unapplied", str(stats.get("unapplied_jobs", 0)), "Not yet processed"
            )

            console.print(status_table)

        except Exception as e:
            console.print(f"[red]❌ Error getting status summary: {e}[/red]")

    def _display_final_statistics(self) -> None:
        """Display final session statistics."""
        console.print("\n" + "=" * 60)
        console.print(Panel.fit("📊 MULTI-AGENT SESSION SUMMARY", style="bold magenta"))

        # Session statistics
        session_table = Table(title="Session Statistics")
        session_table.add_column("Metric", style="cyan")
        session_table.add_column("Value", style="green")

        runtime_hours = self.stats["total_runtime"] / 3600

        session_table.add_row(
            "Session Duration",
            f"{self.stats['total_runtime']:.1f} seconds ({runtime_hours:.2f} hours)",
        )
        session_table.add_row("Applications Submitted", str(self.stats["applications_submitted"]))
        session_table.add_row("Applications Verified", str(self.stats["applications_verified"]))
        session_table.add_row("Applications Failed", str(self.stats["applications_failed"]))
        session_table.add_row("Gmail Checks Performed", str(self.stats["gmail_checks"]))

        console.print(session_table)

        # Success rate
        total_apps = self.stats["applications_submitted"] + self.stats["applications_failed"]
        if total_apps > 0:
            success_rate = (self.stats["applications_verified"] / total_apps) * 100
            console.print(f"\n[green]📈 Verification Rate: {success_rate:.1f}%[/green]")

        # Next steps
        console.print("\n[bold]🔄 NEXT STEPS:[/bold]")
        console.print("• Check dashboard for updated job statuses")
        console.print("• Review any failed applications for improvements")
        console.print("• Run Gmail monitor again if needed")
        console.print("• Continue with more job applications")


# Convenience functions
async def start_job_application_system(
    profile_name: str = "Nirajan", max_applications: int = 10, run_gmail_monitor: bool = True
) -> None:
    """
    Start the complete job application system.

    Args:
        profile_name: Profile name
        max_applications: Maximum number of jobs to apply to
        run_gmail_monitor: Whether to run Gmail monitoring
    """
    orchestrator = MultiAgentOrchestrator(profile_name)
    await orchestrator.start_multi_agent_system(max_applications, run_gmail_monitor)


async def test_gmail_monitor_only(profile_name: str = "Nirajan") -> None:
    """Test only the Gmail monitor."""
    console.print(Panel.fit("📧 GMAIL MONITOR TEST", style="bold cyan"))

    monitor = BackgroundGmailMonitor(profile_name)
    await monitor.start_monitoring(check_interval=30)


if __name__ == "__main__":
    import asyncio

    # Show menu for different modes
    console.print(Panel.fit("🤖 MULTI-AGENT JOB APPLICATION SYSTEM", style="bold blue"))
    console.print("1. 🚀 Start Complete System (Application + Gmail)")
    console.print("2. 🎯 Application Agent Only")
    console.print("3. 📧 Gmail Monitor Only")
    console.print("4. 🧪 Test Mode (5 jobs)")

    choice = Prompt.ask("Select mode", choices=["1", "2", "3", "4"], default="1")

    if choice == "1":
        asyncio.run(start_job_application_system())
    elif choice == "2":
        asyncio.run(run_application_agent(limit=10))
    elif choice == "3":
        asyncio.run(test_gmail_monitor_only())
    elif choice == "4":
        asyncio.run(start_job_application_system(max_applications=5))

