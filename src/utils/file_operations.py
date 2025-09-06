import json
import csv
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging
# Removed self-import: from src.utils.file_operations import save_jobs_to_json

logger = logging.getLogger(__name__)


def save_jobs_to_json(jobs: List[Dict], filename: str) -> str:
    """Saves a list of jobs to a JSON file."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / f"{filename}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(jobs)} jobs to {file_path}")
    return str(file_path)


def load_jobs_from_json(file_path: str) -> List[Dict]:
    """Loads a list of jobs from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs_to_csv(jobs: List[Dict], filename: str) -> str:
    """Saves a list of jobs to a CSV file."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    file_path = output_dir / f"{filename}.csv"

    if not jobs:
        return ""

    fieldnames = list(jobs[0].keys())
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs)

    logger.info(f"Saved {len(jobs)} jobs to {file_path}")
    return str(file_path)


def backup_file(file_path: str, backup_dir: str = "backups") -> bool:
    """Creates a timestamped backup of a file."""
    source_path = Path(file_path)
    if not source_path.exists():
        return False

    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"{source_path.stem}_{timestamp}{source_path.suffix}"

    shutil.copy2(source_path, backup_file)
    return True

