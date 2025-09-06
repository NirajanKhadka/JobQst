"""
CSV Applicator Module

This module handles job applications from CSV files, providing batch processing
and CSV-based job application functionality.
"""

from typing import Dict, Any, List, Optional, Iterator
import csv
import os
from pathlib import Path
from .base_submitter import BaseSubmitter


class CSVJobApplicator:
    """
    CSV Job Applicator - Alias for CSVApplicator for backward compatibility.

    Handles job applications from CSV files with Improved functionality.
    """

    def __init__(self, profile_name: str, csv_file_path: Optional[str] = None):
        """
        Initialize the CSV job applicator.

        Args:
            profile_name: Name of the user profile
            csv_file_path: Path to CSV file with job data
        """
        self.profile_name = profile_name
        self.csv_file_path = csv_file_path
        self.jobs = []
        self.results = []

    def load_jobs_from_csv(self, csv_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load jobs from a CSV file.

        Args:
            csv_file_path: Path to CSV file (optional if set in constructor)

        Returns:
            List of job dictionaries
        """
        file_path = csv_file_path or self.csv_file_path
        if not file_path or not os.path.exists(file_path):
            return []

        jobs = []
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    job = {
                        "id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "company": row.get("company", ""),
                        "location": row.get("location", ""),
                        "url": row.get("url", ""),
                        "ats_type": row.get("ats_type", "unknown"),
                        "job_type": row.get("job_type", ""),
                        "description": row.get("description", ""),
                        "requirements": row.get("requirements", ""),
                        "salary": row.get("salary", ""),
                        "posted_date": row.get("posted_date", ""),
                    }
                    jobs.append(job)

        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return []

        self.jobs = jobs
        return jobs

    def apply_to_jobs_batch(
        self, submitter: BaseSubmitter, max_jobs: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply to multiple jobs in batch.

        Args:
            submitter: ATS submitter instance
            max_jobs: Maximum number of jobs to apply to

        Returns:
            List of application results
        """
        if not self.jobs:
            return []

        jobs_to_process = self.jobs[:max_jobs] if max_jobs else self.jobs
        results = []

        for job in jobs_to_process:
            try:
                # Create a mock profile and file paths for now
                mock_profile = {"name": "Test User", "email": "test@example.com"}
                mock_resume_path = "resume.pdf"
                mock_cover_letter_path = "cover_letter.pdf"

                result = submitter.submit(
                    job, mock_profile, mock_resume_path, mock_cover_letter_path
                )
                result_dict = {
                    "success": result == "Applied",
                    "status": result,
                    "job_id": job.get("id"),
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                }
                results.append(result_dict)
            except Exception as e:
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "job_id": job.get("id"),
                        "job_title": job.get("title"),
                        "company": job.get("company"),
                    }
                )

        self.results = results
        return results

    def save_results_to_csv(self, output_file_path: str) -> bool:
        """
        Save application results to a CSV file.

        Args:
            output_file_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        if not self.results:
            return False

        try:
            with open(output_file_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["job_id", "job_title", "company", "success", "error", "timestamp"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for result in self.results:
                    writer.writerow(
                        {
                            "job_id": result.get("job_id", ""),
                            "job_title": result.get("job_title", ""),
                            "company": result.get("company", ""),
                            "success": result.get("success", False),
                            "error": result.get("error", ""),
                            "timestamp": result.get("timestamp", "2025-06-24T16:00:00Z"),
                        }
                    )
            return True
        except Exception as e:
            print(f"Error saving results to CSV: {e}")
            return False

    def get_success_rate(self) -> float:
        """
        Calculate success rate of batch applications.

        Returns:
            Success rate as a percentage
        """
        if not self.results:
            return 0.0

        successful = sum(1 for result in self.results if result.get("success", False))
        return (successful / len(self.results)) * 100

    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of failed job applications.

        Returns:
            List of failed job results
        """
        return [result for result in self.results if not result.get("success", False)]

    def get_successful_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of successful job applications.

        Returns:
            List of successful job results
        """
        return [result for result in self.results if result.get("success", False)]

    def validate_csv_format(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Validate CSV file format and required columns.

        Args:
            csv_file_path: Path to CSV file

        Returns:
            Validation result dictionary
        """
        if not os.path.exists(csv_file_path):
            return {"valid": False, "error": "File does not exist"}

        required_columns = ["title", "company", "url"]
        optional_columns = [
            "id",
            "location",
            "ats_type",
            "job_type",
            "description",
            "requirements",
            "salary",
            "posted_date",
        ]

        try:
            with open(csv_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames or []

                missing_required = [col for col in required_columns if col not in headers]
                present_optional = [col for col in optional_columns if col in headers]

                return {
                    "valid": len(missing_required) == 0,
                    "missing_required": missing_required,
                    "present_optional": present_optional,
                    "total_columns": len(headers),
                }
        except Exception as e:
            return {"valid": False, "error": str(e)}


class CSVApplicator:
    """
    Handles job applications from CSV files.

    Provides batch processing, CSV parsing, and application tracking
    for jobs loaded from CSV files.
    """

    def __init__(self, profile_name: str, csv_file_path: Optional[str] = None):
        """
        Initialize the CSV applicator.

        Args:
            profile_name: Name of the user profile
            csv_file_path: Path to CSV file with job data
        """
        self.profile_name = profile_name
        self.csv_file_path = csv_file_path
        self.jobs = []
        self.results = []

    def load_jobs_from_csv(self, csv_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load jobs from a CSV file.

        Args:
            csv_file_path: Path to CSV file (optional if set in constructor)

        Returns:
            List of job dictionaries
        """
        file_path = csv_file_path or self.csv_file_path
        if not file_path or not os.path.exists(file_path):
            return []

        jobs = []
        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    job = {
                        "id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "company": row.get("company", ""),
                        "location": row.get("location", ""),
                        "url": row.get("url", ""),
                        "ats_type": row.get("ats_type", "unknown"),
                        "job_type": row.get("job_type", ""),
                        "description": row.get("description", ""),
                        "requirements": row.get("requirements", ""),
                        "salary": row.get("salary", ""),
                        "posted_date": row.get("posted_date", ""),
                    }
                    jobs.append(job)

        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return []

        self.jobs = jobs
        return jobs

    def apply_to_jobs_batch(
        self, submitter: BaseSubmitter, max_jobs: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply to multiple jobs in batch.

        Args:
            submitter: ATS submitter instance
            max_jobs: Maximum number of jobs to apply to

        Returns:
            List of application results
        """
        if not self.jobs:
            return []

        jobs_to_process = self.jobs[:max_jobs] if max_jobs else self.jobs
        results = []

        for job in jobs_to_process:
            try:
                # Create a mock profile and file paths for now
                mock_profile = {"name": "Test User", "email": "test@example.com"}
                mock_resume_path = "resume.pdf"
                mock_cover_letter_path = "cover_letter.pdf"

                result = submitter.submit(
                    job, mock_profile, mock_resume_path, mock_cover_letter_path
                )
                result_dict = {
                    "success": result == "Applied",
                    "status": result,
                    "job_id": job.get("id"),
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                }
                results.append(result_dict)
            except Exception as e:
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "job_id": job.get("id"),
                        "job_title": job.get("title"),
                        "company": job.get("company"),
                    }
                )

        self.results = results
        return results

    def save_results_to_csv(self, output_file_path: str) -> bool:
        """
        Save application results to a CSV file.

        Args:
            output_file_path: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        if not self.results:
            return False

        try:
            with open(output_file_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["job_id", "job_title", "company", "success", "error", "timestamp"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for result in self.results:
                    writer.writerow(
                        {
                            "job_id": result.get("job_id", ""),
                            "job_title": result.get("job_title", ""),
                            "company": result.get("company", ""),
                            "success": result.get("success", False),
                            "error": result.get("error", ""),
                            "timestamp": result.get("timestamp", "2025-06-24T16:00:00Z"),
                        }
                    )
            return True
        except Exception as e:
            print(f"Error saving results to CSV: {e}")
            return False

    def get_success_rate(self) -> float:
        """
        Calculate success rate of batch applications.

        Returns:
            Success rate as a percentage
        """
        if not self.results:
            return 0.0

        successful = sum(1 for result in self.results if result.get("success", False))
        return (successful / len(self.results)) * 100

    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of failed job applications.

        Returns:
            List of failed job results
        """
        return [result for result in self.results if not result.get("success", False)]

    def get_successful_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of successful job applications.

        Returns:
            List of successful job results
        """
        return [result for result in self.results if result.get("success", False)]

    def validate_csv_format(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Validate CSV file format and required columns.

        Args:
            csv_file_path: Path to CSV file

        Returns:
            Validation result dictionary
        """
        if not os.path.exists(csv_file_path):
            return {"valid": False, "error": "File does not exist"}

        required_columns = ["title", "company", "url"]
        optional_columns = [
            "id",
            "location",
            "ats_type",
            "job_type",
            "description",
            "requirements",
            "salary",
            "posted_date",
        ]

        try:
            with open(csv_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames or []

                missing_required = [col for col in required_columns if col not in headers]
                present_optional = [col for col in optional_columns if col in headers]

                return {
                    "valid": len(missing_required) == 0,
                    "missing_required": missing_required,
                    "present_optional": present_optional,
                    "total_columns": len(headers),
                    "headers": headers,
                }
        except Exception as e:
            return {"valid": False, "error": str(e)}


def create_csv_applicator(profile_name: str, csv_file_path: Optional[str] = None) -> CSVApplicator:
    """
    Factory function to create a CSV applicator.

    Args:
        profile_name: Name of the user profile
        csv_file_path: Path to CSV file

    Returns:
        CSVApplicator instance
    """
    return CSVApplicator(profile_name, csv_file_path)


def apply_from_csv(profile_name: str, csv_file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Apply to jobs from a CSV file.
    
    This function provides a simple interface for applying to jobs from CSV files,
    as expected by the test suite.
    
    Args:
        profile_name: Name of the user profile
        csv_file_path: Path to CSV file containing job data
        **kwargs: Additional options for job application
        
    Returns:
        Dictionary containing application results
    """
    try:
        applicator = CSVJobApplicator(profile_name, csv_file_path)
        jobs = applicator.load_jobs_from_csv()
        
        if not jobs:
            return {
                "success": False,
                "error": "No jobs found in CSV file",
                "jobs_processed": 0
            }
        
        # Process applications
        results = []
        for job in jobs:
            try:
                result = applicator.apply_to_job(job)
                results.append(result)
            except Exception as e:
                results.append({
                    "job": job,
                    "success": False,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r.get("success", False))
        
        return {
            "success": True,
            "jobs_processed": len(jobs),
            "successful_applications": successful,
            "failed_applications": len(jobs) - successful,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "jobs_processed": 0
        }

