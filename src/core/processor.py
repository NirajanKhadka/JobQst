"""Simple adapter exposing JobProcessor interface expected by dashboard.

Provides get_status() used in DataLoader without pulling in heavy
processing pipeline synchronously. Wraps TwoStageJobProcessor lazily if
needed for future expansion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import logging

try:  # lightweight import of profile manager & db
    from .job_database import get_job_db  # type: ignore
except Exception:  # pragma: no cover - dashboard fallback
    get_job_db = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ProcessorStatus:
    queue_size: int = 0
    is_processing: bool = False
    completed_today: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "queue_size": self.queue_size,
            "is_processing": self.is_processing,
            "completed_today": self.completed_today,
            "error_count": self.error_count,
        }


class JobProcessor:
    """Minimal facade expected by dashboard code.

    Real heavy processing lives elsewhere (e.g. TwoStageJobProcessor).
    We supply status info derived from DB so the dashboard does not break
    if full processor hasn't been started.
    """

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self._status = ProcessorStatus()
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        logger.debug(
            "JobProcessor initialized for profile %s",
            self.profile_name
        )

    def refresh_status(self) -> None:
        if get_job_db is None:
            return
        try:
            db = get_job_db(self.profile_name)
            pending = db.get_job_count(
                status_filter=["scraped", "new"]
            )  # type: ignore
            processed = db.get_job_count(
                status_filter=["processed", "ready_to_apply", "applied"]
            )  # type: ignore
            self._status.queue_size = pending
            self._status.completed_today = processed  # naive placeholder
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to refresh processor status: %s", e)

    def get_status(self) -> Dict[str, Any]:  # noqa: D401
        self.refresh_status()
        return self._status.to_dict()

    def start_background_processing(self) -> None:  # pragma: no cover
        self._status.is_processing = True
        logger.info("Background processing start requested (stub)")

    def stop(self) -> None:  # pragma: no cover
        self._status.is_processing = False
        logger.info("Processing stop requested (stub)")


__all__ = ["JobProcessor", "ProcessorStatus"]

