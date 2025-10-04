"""
Database Backup Strategy for JobQst
Automated backup system for profile DuckDB files with rotation and recovery
Follows JobQst development standards for data protection
"""

import shutil
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import gzip
import json
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for backup operations"""

    profile_name: str
    backup_type: str  # 'full', 'incremental', 'emergency'
    timestamp: str
    file_size: int
    checksum: str
    source_path: str
    backup_path: str
    compression_ratio: float = 1.0
    success: bool = True
    error_message: str = ""


class DatabaseBackupManager:
    """
    Comprehensive backup manager for JobQst profile databases

    Features:
    - Automated scheduled backups
    - Rotation policy (daily/weekly/monthly)
    - Compression for space efficiency
    - Integrity verification
    - Recovery procedures
    - Emergency backup triggers
    """

    def __init__(
        self,
        backup_root: Path = None,
        max_daily_backups: int = 7,
        max_weekly_backups: int = 4,
        max_monthly_backups: int = 12,
        compress_backups: bool = True,
    ):
        """
        Initialize backup manager

        Args:
            backup_root: Root directory for backups
            max_daily_backups: Maximum daily backups to retain
            max_weekly_backups: Maximum weekly backups to retain
            max_monthly_backups: Maximum monthly backups to retain
            compress_backups: Whether to compress backup files
        """
        # Default backup location
        if backup_root is None:
            project_root = Path(__file__).parent.parent.parent.parent
            backup_root = project_root / "backups" / "databases"

        self.backup_root = Path(backup_root)
        self.max_daily_backups = max_daily_backups
        self.max_weekly_backups = max_weekly_backups
        self.max_monthly_backups = max_monthly_backups
        self.compress_backups = compress_backups

        # Create backup directories
        self.backup_root.mkdir(parents=True, exist_ok=True)
        (self.backup_root / "daily").mkdir(exist_ok=True)
        (self.backup_root / "weekly").mkdir(exist_ok=True)
        (self.backup_root / "monthly").mkdir(exist_ok=True)
        (self.backup_root / "emergency").mkdir(exist_ok=True)

        # Backup history
        self.metadata_file = self.backup_root / "backup_metadata.json"
        self._backup_history = self._load_backup_history()

        # Thread safety
        self._lock = threading.Lock()

        logger.info(f"Backup manager initialized: {self.backup_root}")

    def backup_profile(
        self, profile_name: str, backup_type: str = "daily", force: bool = False
    ) -> BackupMetadata:
        """
        Create backup for a specific profile

        Args:
            profile_name: Name of the profile to backup
            backup_type: Type of backup ('daily', 'weekly', 'monthly', 'emergency')
            force: Force backup even if recent backup exists

        Returns:
            BackupMetadata with backup results
        """
        with self._lock:
            try:
                # Find profile database
                source_db = self._find_profile_database(profile_name)
                if not source_db or not source_db.exists():
                    return BackupMetadata(
                        profile_name=profile_name,
                        backup_type=backup_type,
                        timestamp=datetime.now().isoformat(),
                        file_size=0,
                        checksum="",
                        source_path="",
                        backup_path="",
                        success=False,
                        error_message=f"Database not found for profile {profile_name}",
                    )

                # Check if backup needed (unless forced)
                if not force and self._is_recent_backup_available(profile_name, backup_type):
                    logger.info(f"Recent backup exists for {profile_name}, skipping")
                    return self._get_latest_backup_metadata(profile_name, backup_type)

                # Generate backup path
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{profile_name}_{backup_type}_{timestamp}.db"

                if self.compress_backups:
                    backup_filename += ".gz"

                backup_dir = self.backup_root / backup_type
                backup_path = backup_dir / backup_filename

                # Perform backup
                file_size, checksum, compression_ratio = self._copy_and_verify(
                    source_db, backup_path
                )

                # Create metadata
                metadata = BackupMetadata(
                    profile_name=profile_name,
                    backup_type=backup_type,
                    timestamp=datetime.now().isoformat(),
                    file_size=file_size,
                    checksum=checksum,
                    source_path=str(source_db),
                    backup_path=str(backup_path),
                    compression_ratio=compression_ratio,
                    success=True,
                )

                # Update history
                self._add_backup_to_history(metadata)

                # Cleanup old backups
                self._cleanup_old_backups(backup_type)

                logger.info(f"Backup completed for {profile_name}: {backup_path}")
                return metadata

            except Exception as e:
                logger.error(f"Backup failed for {profile_name}: {e}")
                return BackupMetadata(
                    profile_name=profile_name,
                    backup_type=backup_type,
                    timestamp=datetime.now().isoformat(),
                    file_size=0,
                    checksum="",
                    source_path="",
                    backup_path="",
                    success=False,
                    error_message=str(e),
                )

    def backup_all_profiles(
        self, backup_type: str = "daily", max_workers: int = 3
    ) -> List[BackupMetadata]:
        """
        Backup all available profiles in parallel

        Args:
            backup_type: Type of backup to perform
            max_workers: Maximum concurrent backup operations

        Returns:
            List of backup metadata for all profiles
        """
        try:
            profiles = self._discover_profiles()

            if not profiles:
                logger.warning("No profiles found for backup")
                return []

            logger.info(f"Starting {backup_type} backup for {len(profiles)} profiles")

            # Parallel backup execution
            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.backup_profile, profile, backup_type): profile
                    for profile in profiles
                }

                for future in futures:
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout
                        results.append(result)
                    except Exception as e:
                        profile = futures[future]
                        logger.error(f"Backup failed for {profile}: {e}")
                        results.append(
                            BackupMetadata(
                                profile_name=profile,
                                backup_type=backup_type,
                                timestamp=datetime.now().isoformat(),
                                file_size=0,
                                checksum="",
                                source_path="",
                                backup_path="",
                                success=False,
                                error_message=str(e),
                            )
                        )

            successful = sum(1 for r in results if r.success)
            logger.info(f"Backup completed: {successful}/{len(results)} successful")

            return results

        except Exception as e:
            logger.error(f"Batch backup failed: {e}")
            return []

    def restore_profile(
        self,
        profile_name: str,
        backup_timestamp: str = None,
        backup_type: str = "daily",
        verify_integrity: bool = True,
    ) -> Dict[str, Any]:
        """
        Restore profile from backup

        Args:
            profile_name: Name of profile to restore
            backup_timestamp: Specific backup timestamp (latest if None)
            backup_type: Type of backup to restore from
            verify_integrity: Whether to verify backup integrity

        Returns:
            Dictionary with restoration results
        """
        try:
            # Find backup file
            backup_path = self._find_backup_file(profile_name, backup_timestamp, backup_type)

            if not backup_path:
                return {
                    "success": False,
                    "message": f"No backup found for {profile_name}",
                    "profile_name": profile_name,
                }

            # Verify integrity if requested
            if verify_integrity:
                if not self._verify_backup_integrity(backup_path):
                    return {
                        "success": False,
                        "message": "Backup integrity verification failed",
                        "profile_name": profile_name,
                        "backup_path": str(backup_path),
                    }

            # Determine target location
            target_db = self._find_profile_database(profile_name)
            if not target_db:
                # Create new database location
                target_db = self._get_default_database_path(profile_name)
                target_db.parent.mkdir(parents=True, exist_ok=True)

            # Create backup of current database if it exists
            if target_db.exists():
                emergency_backup = self.backup_profile(profile_name, "emergency", force=True)
                if not emergency_backup.success:
                    logger.warning(f"Could not create emergency backup before restore")

            # Restore from backup
            self._restore_from_backup(backup_path, target_db)

            logger.info(f"Profile {profile_name} restored from {backup_path}")

            return {
                "success": True,
                "message": f"Profile {profile_name} restored successfully",
                "profile_name": profile_name,
                "backup_path": str(backup_path),
                "target_path": str(target_db),
            }

        except Exception as e:
            logger.error(f"Restore failed for {profile_name}: {e}")
            return {
                "success": False,
                "message": f"Restore failed: {e}",
                "profile_name": profile_name,
            }

    def get_backup_status(self) -> Dict[str, Any]:
        """Get comprehensive backup status"""
        try:
            profiles = self._discover_profiles()
            backup_summary = {
                "total_profiles": len(profiles),
                "backed_up_profiles": 0,
                "total_backups": len(self._backup_history),
                "backup_size_mb": 0,
                "last_backup": None,
                "profiles_status": {},
            }

            total_size = 0
            latest_backup = None

            for profile in profiles:
                profile_backups = [
                    b for b in self._backup_history if b["profile_name"] == profile and b["success"]
                ]

                if profile_backups:
                    backup_summary["backed_up_profiles"] += 1

                    # Get latest backup
                    latest = max(profile_backups, key=lambda x: x["timestamp"])
                    total_size += latest.get("file_size", 0)

                    if not latest_backup or latest["timestamp"] > latest_backup:
                        latest_backup = latest["timestamp"]

                    backup_summary["profiles_status"][profile] = {
                        "last_backup": latest["timestamp"],
                        "backup_count": len(profile_backups),
                        "latest_size_mb": round(latest.get("file_size", 0) / 1024 / 1024, 2),
                    }
                else:
                    backup_summary["profiles_status"][profile] = {
                        "last_backup": None,
                        "backup_count": 0,
                        "latest_size_mb": 0,
                    }

            backup_summary["backup_size_mb"] = round(total_size / 1024 / 1024, 2)
            backup_summary["last_backup"] = latest_backup

            return backup_summary

        except Exception as e:
            logger.error(f"Error getting backup status: {e}")
            return {"error": str(e), "total_profiles": 0, "backed_up_profiles": 0}

    # ============= PRIVATE METHODS =============

    def _find_profile_database(self, profile_name: str) -> Optional[Path]:
        """Find database file for a profile"""
        # Common database locations
        project_root = Path(__file__).parent.parent.parent.parent

        possible_paths = [
            project_root / "data" / f"{profile_name}.db",
            project_root / "data" / f"{profile_name}_jobs.db",
            project_root / "profiles" / profile_name / "jobs.db",
            project_root / f"{profile_name}.db",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _get_default_database_path(self, profile_name: str) -> Path:
        """Get default database path for a profile"""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / "data" / f"{profile_name}.db"

    def _discover_profiles(self) -> List[str]:
        """Discover available profiles"""
        profiles = set()
        project_root = Path(__file__).parent.parent.parent.parent

        # Check profiles directory
        profiles_dir = project_root / "profiles"
        if profiles_dir.exists():
            for profile_file in profiles_dir.glob("*.json"):
                profiles.add(profile_file.stem)

        # Check data directory for database files
        data_dir = project_root / "data"
        if data_dir.exists():
            for db_file in data_dir.glob("*.db"):
                if not db_file.name.startswith("test_"):
                    profile_name = db_file.stem.replace("_jobs", "")
                    profiles.add(profile_name)

        return list(profiles)

    def _copy_and_verify(self, source: Path, destination: Path) -> tuple[int, str, float]:
        """Copy file with compression and verification"""
        import hashlib

        # Calculate source checksum
        source_hash = hashlib.md5()
        source_size = 0

        with open(source, "rb") as f:
            while chunk := f.read(8192):
                source_hash.update(chunk)
                source_size += len(chunk)

        source_checksum = source_hash.hexdigest()

        # Copy with optional compression
        if self.compress_backups:
            with open(source, "rb") as src, gzip.open(destination, "wb") as dst:
                shutil.copyfileobj(src, dst)
            compression_ratio = source_size / destination.stat().st_size
        else:
            shutil.copy2(source, destination)
            compression_ratio = 1.0

        return source_size, source_checksum, compression_ratio

    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Verify backup file integrity"""
        try:
            if backup_path.suffix == ".gz":
                with gzip.open(backup_path, "rb") as f:
                    # Try to read a small chunk
                    f.read(1024)
            else:
                # For uncompressed files, check if it's a valid SQLite database
                with open(backup_path, "rb") as f:
                    header = f.read(16)
                    if not header.startswith(b"SQLite format 3"):
                        return False

            return True

        except Exception as e:
            logger.error(f"Integrity check failed for {backup_path}: {e}")
            return False

    def _restore_from_backup(self, backup_path: Path, target_path: Path) -> None:
        """Restore database from backup file"""
        if backup_path.suffix == ".gz":
            with gzip.open(backup_path, "rb") as src, open(target_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        else:
            shutil.copy2(backup_path, target_path)

    def _is_recent_backup_available(
        self, profile_name: str, backup_type: str, hours: int = 24
    ) -> bool:
        """Check if recent backup exists"""
        cutoff = datetime.now() - timedelta(hours=hours)

        for backup in self._backup_history:
            if (
                backup["profile_name"] == profile_name
                and backup["backup_type"] == backup_type
                and backup["success"]
            ):

                backup_time = datetime.fromisoformat(backup["timestamp"])
                if backup_time > cutoff:
                    return True

        return False

    def _get_latest_backup_metadata(self, profile_name: str, backup_type: str) -> BackupMetadata:
        """Get metadata for latest backup"""
        matching_backups = [
            b
            for b in self._backup_history
            if (
                b["profile_name"] == profile_name
                and b["backup_type"] == backup_type
                and b["success"]
            )
        ]

        if matching_backups:
            latest = max(matching_backups, key=lambda x: x["timestamp"])
            return BackupMetadata(**latest)

        # Return empty metadata if no backup found
        return BackupMetadata(
            profile_name=profile_name,
            backup_type=backup_type,
            timestamp=datetime.now().isoformat(),
            file_size=0,
            checksum="",
            source_path="",
            backup_path="",
            success=False,
            error_message="No recent backup found",
        )

    def _find_backup_file(
        self, profile_name: str, timestamp: str = None, backup_type: str = "daily"
    ) -> Optional[Path]:
        """Find specific backup file"""
        backup_dir = self.backup_root / backup_type

        if timestamp:
            # Look for specific timestamp
            pattern = f"{profile_name}_{backup_type}_{timestamp}*"
        else:
            # Look for latest backup
            pattern = f"{profile_name}_{backup_type}_*"

        matching_files = list(backup_dir.glob(pattern))

        if matching_files:
            # Return latest if multiple matches
            return max(matching_files, key=lambda x: x.stat().st_mtime)

        return None

    def _cleanup_old_backups(self, backup_type: str) -> None:
        """Remove old backups according to retention policy"""
        backup_dir = self.backup_root / backup_type

        # Get retention limit
        if backup_type == "daily":
            max_backups = self.max_daily_backups
        elif backup_type == "weekly":
            max_backups = self.max_weekly_backups
        elif backup_type == "monthly":
            max_backups = self.max_monthly_backups
        else:
            return  # Don't cleanup emergency backups

        # Group backups by profile
        profile_backups = {}
        for backup_file in backup_dir.glob("*.db*"):
            try:
                profile_name = backup_file.name.split("_")[0]
                if profile_name not in profile_backups:
                    profile_backups[profile_name] = []
                profile_backups[profile_name].append(backup_file)
            except Exception:
                continue

        # Cleanup each profile's old backups
        for profile_name, backups in profile_backups.items():
            if len(backups) > max_backups:
                # Sort by modification time, keep newest
                backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                for old_backup in backups[max_backups:]:
                    try:
                        old_backup.unlink()
                        logger.info(f"Removed old backup: {old_backup}")
                    except Exception as e:
                        logger.error(f"Failed to remove {old_backup}: {e}")

    def _load_backup_history(self) -> List[Dict]:
        """Load backup history from metadata file"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading backup history: {e}")

        return []

    def _save_backup_history(self) -> None:
        """Save backup history to metadata file"""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self._backup_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backup history: {e}")

    def _add_backup_to_history(self, metadata: BackupMetadata) -> None:
        """Add backup metadata to history"""
        self._backup_history.append(asdict(metadata))

        # Keep only last 1000 entries
        if len(self._backup_history) > 1000:
            self._backup_history = self._backup_history[-1000:]

        self._save_backup_history()


# Global backup manager instance
_backup_manager = None


def get_backup_manager() -> DatabaseBackupManager:
    """Get global backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = DatabaseBackupManager()
    return _backup_manager


def schedule_automated_backups():
    """Schedule automated backup tasks (to be called by scheduler)"""
    try:
        backup_manager = get_backup_manager()

        # Daily backup
        results = backup_manager.backup_all_profiles("daily")
        successful = sum(1 for r in results if r.success)

        logger.info(f"Automated daily backup: {successful}/{len(results)} successful")

        # Weekly backup on Sundays
        if datetime.now().weekday() == 6:  # Sunday
            weekly_results = backup_manager.backup_all_profiles("weekly")
            weekly_successful = sum(1 for r in weekly_results if r.success)
            logger.info(f"Weekly backup: {weekly_successful}/{len(weekly_results)} successful")

        # Monthly backup on 1st of month
        if datetime.now().day == 1:
            monthly_results = backup_manager.backup_all_profiles("monthly")
            monthly_successful = sum(1 for r in monthly_results if r.success)
            logger.info(f"Monthly backup: {monthly_successful}/{len(monthly_results)} successful")

    except Exception as e:
        logger.error(f"Automated backup failed: {e}")


def emergency_backup(profile_name: str) -> Dict[str, Any]:
    """Create emergency backup (called before risky operations)"""
    try:
        backup_manager = get_backup_manager()
        result = backup_manager.backup_profile(profile_name, "emergency", force=True)

        return {
            "success": result.success,
            "message": "Emergency backup completed" if result.success else result.error_message,
            "backup_path": result.backup_path,
        }

    except Exception as e:
        logger.error(f"Emergency backup failed for {profile_name}: {e}")
        return {"success": False, "message": f"Emergency backup failed: {e}", "backup_path": ""}
