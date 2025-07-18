from typing import List, Dict, Optional


class ManualReviewManager:
    def __init__(self, db):
        self.db = db  # Pass in a database manager instance

    def add_to_review_queue(self, job: Dict):
        """Add a job to the manual review queue in the database."""
        self.db.add_manual_review_job(job)

    def get_pending_reviews(self) -> List[Dict]:
        """Retrieve jobs pending manual review from the database."""
        return self.db.get_manual_review_jobs(status="pending")

    def approve_job(self, job_id: str):
        """Mark a job as approved in the manual review queue."""
        self.db.update_manual_review_status(job_id, "approved")

    def reject_job(self, job_id: str):
        """Mark a job as rejected in the manual review queue."""
        self.db.update_manual_review_status(job_id, "rejected")
