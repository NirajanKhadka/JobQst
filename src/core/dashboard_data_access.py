"""Dashboard data access layer for JobQst.

This module centralizes DuckDB access and normalization routines used by the
Dash dashboard and related services.  It exposes a single, cache-aware API so
that downstream consumers no longer need to duplicate query logic, schema
shaping, or cache coordination.

Key responsibilities:
- Execute profile-scoped DuckDB queries safely via ``DuckDBConnectionManager``.
- Normalize raw database rows into a consistent schema that includes RCIP
  indicators, ranking breakdowns, and cache metadata required by the dashboard.
- Leverage ``UnifiedCacheService`` to provide TTL-based caching with
  instrumentation hooks for monitoring.
- Surface a structured response contract that callers can rely on for both
  records and pandas DataFrame access plus diagnostic metadata.

The implementation follows the JobQst development standards and Python
instructions for documentation, type hints, and maintainability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .duckdb_connection_manager import DuckDBConnectionManager
from .unified_cache_service import CacheConfig, UnifiedCacheService

logger = logging.getLogger(__name__)

# Canonical dashboard columns. Downstream consumers should rely on this list
# when creating DataFrame views to avoid schema drift.
DEFAULT_COLUMNS: Tuple[str, ...] = (
    "id",
    "title",
    "company",
    "location",
    "status",
    "salary",
    "match_score",
    "fit_score",
    "stage1_score",
    "final_score",
    "posted_date",
    "created_at",
    "url",
    "job_url",
    "summary",
    "description",
    "site",
    "job_type",
    "skills",
    "keywords",
    "application_status",
    "priority_level",
    "city_tags",
    "province_code",
    "location_type",
    "location_category",
    "tags",
    "has_rcip",
    "rcip_indicator",
    "immigration_priority",
    "ranking",
    "cache_metadata",
)

# Ranking keys exposed to the dashboard UI. Values are normalized to floats so
# chart and badge logic can consume them without extra casting.
RANKING_KEYS: Tuple[str, ...] = (
    "match_score",
    "fit_score",
    "stage1_score",
    "final_score",
    "relevance_score",
)


class DashboardDataAccessError(Exception):
    """Raised when the dashboard data access layer encounters an unrecoverable error."""


@dataclass(slots=True)
class CacheMetadata:
    """Metadata describing cache behaviour for a result payload."""

    cache_key: str
    cached_at: datetime
    ttl_seconds: int
    hit: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metadata object to a JSON-serialisable dictionary."""
        return {
            "cache_key": self.cache_key,
            "cached_at": self.cached_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "hit": self.hit,
        }


@dataclass(slots=True)
class DashboardDataResponse:
    """Structured response returned by ``DashboardDataAccess`` calls."""

    records: List[Dict[str, Any]]
    dataframe: pd.DataFrame
    cache_metadata: CacheMetadata
    schema: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_COLUMNS)
    error: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        """Produce a serialisable payload for REST or Dash callbacks."""
        return {
            "data": self.records,
            "schema": list(self.schema),
            "cache": self.cache_metadata.to_dict(),
            "error": self.error,
        }


class DashboardDataAccess:
    """Unified entry point for profile-scoped dashboard data retrieval."""

    def __init__(
        self,
        cache_service: Optional[UnifiedCacheService] = None,
        cache_config: Optional[CacheConfig] = None,
    ) -> None:
        """Initialise the access layer with optional cache dependencies.

        Args:
            cache_service: Injected cache instance (useful for tests). When
                omitted, a new ``UnifiedCacheService`` is created with the
                provided ``cache_config``.
            cache_config: Optional cache configuration when the access layer
                owns the cache instance.
        """
        if cache_service is not None:
            self._cache = cache_service
        else:
            self._cache = UnifiedCacheService(
                cache_config
                or CacheConfig(
                    max_size=500,
                    default_ttl_seconds=300,
                    enable_statistics=True,
                    thread_safe=True,
                )
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_jobs(
        self,
        profile_name: str,
        *,
        force_refresh: bool = False,
        limit: Optional[int] = None,
    ) -> DashboardDataResponse:
        """Return normalised job records for the given profile.

        Args:
            profile_name: Profile whose jobs we need to fetch.
            force_refresh: Skip cache and refresh from DuckDB when ``True``.
            limit: Optional limit applied to the SQL query (useful for previews).

        Returns:
            ``DashboardDataResponse`` containing records, DataFrame, and cache
            diagnostics.

        Raises:
            DashboardDataAccessError: When the underlying DuckDB query fails.
        """
        cache_key = self._build_cache_key(profile_name, limit)
        cache_hit = False

        if not force_refresh:
            cached_payload = self._cache.get(cache_key)
            if cached_payload is not None:
                cache_hit = True
                logger.debug(
                    "Dashboard data cache hit for profile=%s limit=%s",
                    profile_name,
                    limit,
                )
                return self._build_response(
                    cached_payload,
                    cache_key=cache_key,
                    cache_hit=True,
                )

        try:
            rows, columns = self._fetch_jobs(profile_name, limit=limit)
        except Exception as error:  # pragma: no cover - defensive logging branch
            logger.exception(
                "Failed to fetch dashboard jobs for profile %s: %s",
                profile_name,
                error,
            )
            raise DashboardDataAccessError(str(error)) from error

        records = [self._normalise_record(dict(zip(columns, row))) for row in rows]
        dataframe = self._create_dataframe(records)
        payload = {
            "records": records,
            "dataframe": dataframe,
        }
        self._cache.set(cache_key, payload)

        return self._build_response(
            payload,
            cache_key=cache_key,
            cache_hit=cache_hit,
        )

    def clear_profile_cache(self, profile_name: Optional[str]) -> int:
        """Invalidate cached job data for a specific profile or entire cache."""
        if not profile_name:
            return self._cache.invalidate()
        pattern = re.escape(profile_name)
        return self._cache.invalidate(pattern)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Expose cache statistics for monitoring dashboards."""
        return self._cache.get_statistics()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_cache_key(self, profile_name: str, limit: Optional[int]) -> str:
        """Create a deterministic cache key."""
        limit_part = f"limit={limit}" if limit is not None else "all"
        return self._cache.generate_cache_key(
            self.__class__.__name__,
            profile_name,
            limit_part,
        )

    def _fetch_jobs(
        self,
        profile_name: str,
        *,
        limit: Optional[int] = None,
    ) -> Tuple[List[Tuple[Any, ...]], List[str]]:
        """Execute the DuckDB query and return raw rows and columns."""
        query = "SELECT * FROM jobs WHERE profile_name = ? " "ORDER BY created_at DESC"
        params: List[Any] = [profile_name]

        if limit is not None and limit > 0:
            query += " LIMIT ?"
            params.append(limit)

        rows = DuckDBConnectionManager.execute_query(
            query,
            params,
            profile_name,
            read_only=True,
        )
        columns = DuckDBConnectionManager.get_columns(
            query,
            params,
            profile_name,
        )
        return rows, columns

    def _normalise_record(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a raw database row into the dashboard schema."""
        match_score = self._compute_match_score(raw)
        tags = self._build_tags(raw)
        ranking = self._build_ranking(raw, match_score)

        normalised = {
            "id": raw.get("id", ""),
            "title": raw.get("title", "Unknown Title"),
            "company": raw.get("company", "Unknown Company"),
            "location": raw.get("location", "Unknown Location"),
            "status": self._resolve_status(raw),
            "salary": self._format_salary(raw.get("salary_range")),
            "match_score": match_score,
            "fit_score": self._safe_float(raw.get("fit_score")),
            "stage1_score": self._safe_float(raw.get("stage1_score")),
            "final_score": self._safe_float(raw.get("final_score")),
            "posted_date": self._format_date(raw.get("date_posted")),
            "created_at": self._format_date(raw.get("created_at")),
            "url": raw.get("url", ""),
            "job_url": raw.get("url", ""),
            "summary": raw.get("summary", ""),
            "description": raw.get("description", ""),
            "site": raw.get("source", raw.get("site", "")),
            "job_type": raw.get("job_type", ""),
            "skills": raw.get("skills", ""),
            "keywords": self._extract_keywords(raw),
            "application_status": raw.get("application_status", "discovered"),
            "priority_level": raw.get("priority_level", 3),
            "city_tags": raw.get("city_tags", ""),
            "province_code": raw.get("province_code", ""),
            "location_type": raw.get("location_type", "onsite"),
            "location_category": raw.get("location_category", "unknown"),
            "tags": tags,
            "has_rcip": "RCIP" in tags,
            "rcip_indicator": "🇨🇦 RCIP" if "RCIP" in tags else "",
            "immigration_priority": "⭐ Priority" if "IMMIGRATION_PRIORITY" in tags else "",
            "ranking": ranking,
            "cache_metadata": {},  # Filled post-normalisation
        }

        # Ensure all default columns exist (some may have been missing in raw data).
        for column in DEFAULT_COLUMNS:
            normalised.setdefault(column, None)

        return normalised

    def _build_response(
        self,
        payload: Dict[str, Any],
        *,
        cache_key: str,
        cache_hit: bool,
    ) -> DashboardDataResponse:
        """Construct response object with cache metadata injected."""
        cache_metadata = CacheMetadata(
            cache_key=cache_key,
            cached_at=datetime.utcnow(),
            ttl_seconds=self._cache.config.default_ttl_seconds,
            hit=cache_hit,
        )

        records: List[Dict[str, Any]] = payload["records"]
        dataframe: pd.DataFrame = payload["dataframe"]

        # Inject metadata into each record for downstream UI features.
        cache_meta_dict = cache_metadata.to_dict()
        for record in records:
            record["cache_metadata"] = cache_meta_dict

        return DashboardDataResponse(
            records=records,
            dataframe=dataframe,
            cache_metadata=cache_metadata,
        )

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------
    def _compute_match_score(self, raw: Dict[str, Any]) -> float:
        """Coerce match score values into the expected 0-100 range."""
        score_sources: Iterable[Any] = (
            raw.get("match_score"),
            raw.get("fit_score"),
        )
        for score in score_sources:
            value = self._safe_float(score)
            if value is None:
                continue
            # Values stored as 0-1 need upscaling, assume <= 1.0 implies percentages.
            return float(value * 100 if value <= 1 else value)
        return 0.0

    def _build_ranking(self, raw: Dict[str, Any], match_score: float) -> Dict[str, float]:
        """Compose ranking breakdown dictionary for the dashboard."""
        ranking: Dict[str, float] = {"match_score": float(match_score)}
        for key in RANKING_KEYS:
            value = raw.get(key)
            safe_value = self._safe_float(value)
            if safe_value is not None:
                ranking[key] = float(safe_value)
        return ranking

    def _build_tags(self, raw: Dict[str, Any]) -> List[str]:
        """Create a set of tags that power dashboard filtering."""
        tags: List[str] = []
        if raw.get("is_rcip_city"):
            tags.append("RCIP")
        if raw.get("is_immigration_priority"):
            tags.append("IMMIGRATION_PRIORITY")
        location = (raw.get("location") or "").lower()
        if "remote" in location:
            tags.append("REMOTE")
        if raw.get("application_status") not in (None, "discovered"):
            tags.append(raw.get("application_status", "").upper())
        if raw.get("keywords"):
            tags.append("KEYWORDED")
        return tags

    def _resolve_status(self, raw: Dict[str, Any]) -> str:
        """Determine dashboard status from stored job fields."""
        application_status = raw.get("application_status")
        if application_status and application_status != "discovered":
            return application_status

        status_mapping = {
            "new": "new",
            "scraped": "new",
            "processed": "ready_to_apply",
            "ready_to_apply": "ready_to_apply",
            "applied": "applied",
            "reviewing": "needs_review",
            "interview": "interview",
        }
        return status_mapping.get(raw.get("status", "new"), "new")

    def _format_salary(self, salary: Any) -> str:
        """Format salary information for display."""
        if salary in (None, "", "None", "null", "not specified"):
            return "Not specified"
        if isinstance(salary, (int, float)):
            return f"${salary:,.0f}"
        return str(salary)

    def _format_date(self, value: Any) -> str:
        """Normalise date values to YYYY-MM-DD strings."""
        if not value:
            return datetime.utcnow().strftime("%Y-%m-%d")
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        try:
            text = str(value)
            if "T" in text:
                text = text.split("T")[0]
            return text[:10]
        except Exception:  # pragma: no cover - defensive fallback
            return datetime.utcnow().strftime("%Y-%m-%d")

    def _extract_keywords(self, raw: Dict[str, Any]) -> str:
        """Derive display-ready keywords from job metadata."""
        keywords_field = raw.get("keywords") or raw.get("skills")
        if isinstance(keywords_field, str) and keywords_field.strip():
            parts = [
                part.strip().title()
                for part in keywords_field.replace(
                    ",",
                    ";",
                ).split(";")
                if part.strip()
            ]
            return ", ".join(dict.fromkeys(parts))[:250]
        return "No keywords"

    def _safe_float(self, value: Any) -> Optional[float]:
        """Convert values to float when possible."""
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _create_dataframe(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create a DataFrame with the canonical column ordering."""
        if not records:
            return pd.DataFrame(columns=list(DEFAULT_COLUMNS))
        dataframe = pd.DataFrame.from_records(records)
        # Ensure all expected columns exist.
        for column in DEFAULT_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = None
        return dataframe[list(DEFAULT_COLUMNS)]


def get_dashboard_data_access() -> DashboardDataAccess:
    """Convenience factory mirroring other JobQst service accessors."""
    return DashboardDataAccess()
