#!/usr/bin/env python3
"""
Manual Review Manager for handling jobs that require human intervention.
Provides a comprehensive system for tracking and resolving manual review items.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.job_database import get_job_db

console = Console()


class ManualReviewManager:
    """
    Manager for handling manual review queue and error resolution.
    """

    def __init__(self, profile_name: str = "default"):
        """
        Initialize the manual review manager.

        Args:
            profile_name: Name of the user profile
        """
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)

    def add_review_item(
        self,
        job_id: int,
        review_type: str,
        title: str,
        description: str,
        context: Dict = {},
        priority: int = 2,
        screenshot_path: str = "",
    ) -> int:
        """
        Add an item to the manual review queue.

        Args:
            job_id: Database ID of the job
            review_type: Type of review needed
            title: Brief description
            description: Detailed description
            context: Additional context information
            priority: Priority level (1=low, 2=medium, 3=high, 4=urgent)
            screenshot_path: Path to screenshot

        Returns:
            Review queue ID
        """
        # TODO: Implement real DB support for manual review queue
        if context is None:
            context = {}
        review_id = 1  # Dummy ID
        safe_title = title if title is not None else "(no title)"
        console.print(
            f"[yellow]📋 [STUB] Added to manual review queue (ID: {review_id}): {safe_title}[/yellow]"
        )
        return review_id

    def get_pending_reviews(self) -> List[Dict]:
        """
        Get all pending manual review items.

        Returns:
            List of pending review items
        """
        # TODO: Implement real DB support for manual review queue
        return []

    def get_all_reviews(self) -> List[Dict]:
        """
        Get all manual review items regardless of status.

        Returns:
            List of all review items
        """
        # TODO: Implement real DB support for manual review queue
        return []

    def display_review_queue(self, status: str = "pending") -> None:
        """
        Display the manual review queue in a formatted table.

        Args:
            status: Status filter for items to display
        """
        # TODO: Implement real DB support for manual review queue
        items = []

        if not items:
            console.print(f"[green]✅ No {status} manual review items found![/green]")
            return

        table = Table(title=f"Manual Review Queue - {status.title()} Items")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Priority", style="red", no_wrap=True)
        table.add_column("Type", style="blue", no_wrap=True)
        table.add_column("Job Title", style="green")
        table.add_column("Company", style="yellow")
        table.add_column("Issue", style="white")
        table.add_column("Created", style="dim", no_wrap=True)

        for item in items:
            priority_map = {1: "Low", 2: "Med", 3: "High", 4: "URGENT"}
            priority_str = priority_map.get(item["priority"], str(item["priority"]))

            created_date = datetime.fromisoformat(item["created_at"]).strftime("%m/%d %H:%M")

            table.add_row(
                str(item["id"]),
                priority_str,
                item["review_type"],
                (
                    item["job_title"][:30] + "..."
                    if len(item["job_title"]) > 30
                    else item["job_title"]
                ),
                item["company"][:20] + "..." if len(item["company"]) > 20 else item["company"],
                item["title"][:40] + "..." if len(item["title"]) > 40 else item["title"],
                created_date,
            )

        console.print(table)

    def get_review_details(self, review_id: int) -> Dict:
        """
        Get detailed information about a specific review item.

        Args:
            review_id: Review queue ID

        Returns:
            Dictionary with review details
        """
        try:
            import sqlite3

            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute(
                    """
                    SELECT mrq.*, j.title, j.company, j.url, j.location, j.summary
                    FROM manual_review_queue mrq
                    JOIN jobs j ON mrq.job_id = j.id
                    WHERE mrq.id = ?
                """,
                    (review_id,),
                )

                row = cursor.fetchone()
                if row:
                    details = dict(row)
                    # Parse JSON context data
                    if details.get("context_data"):
                        try:
                            details["context_data"] = json.loads(details["context_data"])
                        except:
                            pass
                    return details

        except Exception as e:
            console.print(f"[red]❌ Error getting review details: {e}[/red]")

        return {}

    def display_review_details(self, review_id: int) -> None:
        """
        Display detailed information about a review item.

        Args:
            review_id: Review queue ID
        """
        details = self.get_review_details(review_id)

        if not details:
            console.print(f"[red]❌ Review item {review_id} not found[/red]")
            return

        # Create detailed panel
        safe_title = details.get("title") or "(no title)"
        safe_company = details.get("company") or "(no company)"
        safe_url = details.get("url") or ""
        safe_location = details.get("location") or "N/A"
        safe_review_type = details.get("review_type") or ""
        safe_priority = details.get("priority") or ""
        safe_status = details.get("status") or ""
        safe_created = details.get("created_at") or ""
        safe_description = details.get("description") or ""
        safe_context = json.dumps(details.get("context_data", {}), indent=2)
        content = f"""
[bold blue]Job Information:[/bold blue]
• Title: {safe_title}
• Company: {safe_company}
• Location: {safe_location}
• URL: {safe_url}

[bold yellow]Review Details:[/bold yellow]
• Type: {safe_review_type}
• Priority: {safe_priority} (1=Low, 2=Med, 3=High, 4=Urgent)
• Status: {safe_status}
• Created: {safe_created}

[bold red]Issue Description:[/bold red]
{safe_description}

[bold green]Context Information:[/bold green]
{safe_context}
        """
        safe_screenshot = details.get("screenshot_path") or ""
        if safe_screenshot:
            content += f"\n[bold cyan]Screenshot:[/bold cyan] {safe_screenshot}"
        if not isinstance(safe_title, str):
            safe_title = "(no title)"
        panel_title = f"Manual Review #{review_id} - {safe_title[:50]}"
        panel = Panel(content, title=panel_title)
        console.print(panel)

    def resolve_review_item(self, review_id: int, resolution: str, reviewer: str = None) -> bool:
        """
        Mark a review item as resolved.

        Args:
            review_id: Review queue ID
            resolution: Description of how it was resolved
            reviewer: Who resolved it

        Returns:
            True if successful
        """
        try:
            import sqlite3

            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute(
                    """
                    UPDATE manual_review_queue 
                    SET status = 'resolved', 
                        resolution = ?, 
                        reviewer = ?,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (resolution, reviewer or self.profile_name, review_id),
                )

                conn.commit()
                console.print(f"[green]✅ Review item {review_id} marked as resolved[/green]")
                return True

        except Exception as e:
            console.print(f"[red]❌ Error resolving review item: {e}[/red]")
            return False

    def skip_review_item(self, review_id: int, reason: str = "") -> bool:
        """
        Skip a review item (mark as not applicable).

        Args:
            review_id: Review queue ID
            reason: Reason for skipping

        Returns:
            True if successful
        """
        try:
            import sqlite3

            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute(
                    """
                    UPDATE manual_review_queue 
                    SET status = 'skipped', 
                        resolution = ?, 
                        reviewer = ?,
                        reviewed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (f"Skipped: {reason}", self.profile_name, review_id),
                )

                conn.commit()
                console.print(f"[yellow]⏭️ Review item {review_id} skipped[/yellow]")
                return True

        except Exception as e:
            console.print(f"[red]❌ Error skipping review item: {e}[/red]")
            return False

    def get_review_statistics(self) -> Dict:
        """
        Get statistics about the manual review queue.

        Returns:
            Dictionary with review statistics
        """
        try:
            import sqlite3

            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT 
                        status,
                        review_type,
                        priority,
                        COUNT(*) as count
                    FROM manual_review_queue
                    GROUP BY status, review_type, priority
                """
                )

                stats = {"by_status": {}, "by_type": {}, "by_priority": {}, "total": 0}

                for row in cursor.fetchall():
                    status, review_type, priority, count = row
                    stats["by_status"][status] = stats["by_status"].get(status, 0) + count
                    stats["by_type"][review_type] = stats["by_type"].get(review_type, 0) + count
                    stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + count
                    stats["total"] += count

                return stats

        except Exception as e:
            console.print(f"[red]❌ Error getting review statistics: {e}[/red]")
            return {"by_status": {}, "by_type": {}, "by_priority": {}, "total": 0}

    def add_job_for_review(self, job: dict) -> bool:
        """Stub: Add a job for manual review."""
        return True

    def get_queue_size(self) -> int:
        """Stub: Return the size of the manual review queue."""
        return 0

    def calculate_priority(self, job: dict) -> int:
        """Stub: Calculate priority for a job."""
        return 1

    def should_auto_approve(self, job: dict) -> bool:
        """Stub: Determine if a job should be auto-approved."""
        return False

