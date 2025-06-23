"""
File utilities for AutoJobAgent.
Handles JSON, CSV, backup, temp files, and output directory management.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FileUtils:
    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ FileUtils initialized")

    def save_jobs_to_json(self, jobs: List[Dict], filename: Optional[str] = None) -> str:
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"jobs_{timestamp}.json"
            file_path = self.output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved {len(jobs)} jobs to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"❌ Failed to save jobs to JSON: {e}")
            return ""

    def load_jobs_from_json(self, file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            logger.info(f"✅ Loaded {len(jobs)} jobs from {file_path}")
            return jobs
        except Exception as e:
            logger.error(f"❌ Failed to load jobs from JSON: {e}")
            return []

    def save_jobs_to_csv(self, jobs: List[Dict], filename: Optional[str] = None) -> str:
        try:
            import csv
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"jobs_{timestamp}.csv"
            file_path = self.output_dir / filename
            if not jobs:
                logger.warning("⚠️ No jobs to save")
                return ""
            fieldnames = set()
            for job in jobs:
                fieldnames.update(job.keys())
            fieldnames = sorted(list(fieldnames))
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for job in jobs:
                    row = job.copy()
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = ", ".join(str(v) for v in value)
                    writer.writerow(row)
            logger.info(f"✅ Saved {len(jobs)} jobs to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"❌ Failed to save jobs to CSV: {e}")
            return ""

    def backup_file(self, file_path: str, backup_dir: str = "backups") -> bool:
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(file_path, backup_path)
            logger.info(f"✅ Backed up {file_path} to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to backup file: {e}")
            return False

    def create_output_directory(self, name: str) -> Path:
        path = self.output_dir / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def create_temp_file(self, content: str, extension: str = ".txt") -> str:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension, mode='w', encoding='utf-8') as tmp:
            tmp.write(content)
            return tmp.name 