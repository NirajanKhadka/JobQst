from __future__ import annotations

"""Shared aggregation helpers for dashboard analytics.

This module centralizes company, location, and job metrics computations so that
services, cache adapters, and chart utilities reuse the exact same business
logic. All helpers accept either a pandas ``DataFrame`` or an iterable of job
records. The functions are intentionally side-effect free to make them easy to
cache and test.
"""

from collections.abc import Mapping as MappingABC, Sequence as SequenceABC
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple
import hashlib
import json

import pandas as pd

__all__ = [
    "CompanyStats",
    "LocationStats",
    "ScoreDistribution",
    "JobMetrics",
    "ensure_dataframe",
    "dataframe_fingerprint",
    "compute_company_stats",
    "compute_location_stats",
    "compute_job_metrics",
]


@dataclass(frozen=True)
class CompanyStats:
    """Aggregated company statistics for dashboard visuals."""

    companies: List[str]
    counts: List[int]
    total_companies: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "companies": self.companies,
            "counts": self.counts,
            "total_companies": self.total_companies,
        }


@dataclass(frozen=True)
class LocationStats:
    """Aggregated location statistics for dashboard visuals."""

    locations: List[str]
    counts: List[int]
    total_locations: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "locations": self.locations,
            "counts": self.counts,
            "total_locations": self.total_locations,
        }


@dataclass(frozen=True)
class ScoreDistribution:
    """Distribution of match scores grouped by configured ranges."""

    ranges: List[str]
    counts: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return {"ranges": self.ranges, "counts": self.counts}


@dataclass(frozen=True)
class JobMetrics:
    """High-level job metrics surfaced across dashboard panels."""

    total_jobs: int
    avg_match_score: float
    status_counts: Dict[str, int]
    score_distribution: ScoreDistribution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_jobs": self.total_jobs,
            "avg_match_score": self.avg_match_score,
            "status_counts": self.status_counts,
            "score_distribution": self.score_distribution.to_dict(),
        }


def ensure_dataframe(data: Any) -> pd.DataFrame:
    """Return a defensive copy of job records as a DataFrame.

    Parameters
    ----------
    data:
        Either a pandas ``DataFrame`` or an iterable of mapping objects.

    Returns
    -------
    pd.DataFrame
        DataFrame representation of *data*. Empty when the input cannot be
        represented (e.g., ``None`` or an empty iterable).
    """

    if data is None:
        return pd.DataFrame()

    if isinstance(data, pd.DataFrame):
        return data.copy()

    if isinstance(data, Iterable):
        materialized = list(data)
        if not materialized:
            return pd.DataFrame()
        return pd.DataFrame(materialized)

    return pd.DataFrame()


def _canonicalize_for_hash(value: Any) -> Any:
    """Return a hash-friendly representation for complex objects.

    The hashing utilities in pandas expect hashable values. Job records may
    contain dictionaries or nested collections (e.g., metadata blobs) that are
    unhashable by default. This helper converts such structures into stable JSON
    strings so that two logically equivalent values produce the same
    fingerprint.
    """

    if value is None:
        return "<NULL>"

    if isinstance(value, (str, bytes, bytearray)):
        return value

    if isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return value.isoformat()

    if isinstance(value, MappingABC):
        canonical_items = {str(key): _canonicalize_for_hash(val) for key, val in value.items()}
        return json.dumps(canonical_items, sort_keys=True, separators=(",", ":"))

    if isinstance(value, SequenceABC) and not isinstance(value, (str, bytes, bytearray)):
        canonical_sequence = [_canonicalize_for_hash(item) for item in value]
        return json.dumps(canonical_sequence, sort_keys=True, separators=(",", ":"))

    if isinstance(value, (set, frozenset)):
        canonical_sequence = sorted(_canonicalize_for_hash(item) for item in value)
        return json.dumps(canonical_sequence, sort_keys=True, separators=(",", ":"))

    if isinstance(value, (int, float, bool)):
        return value

    return str(value)


def dataframe_fingerprint(df: pd.DataFrame) -> str:
    """Return a stable fingerprint for caching operations."""

    if df is None or df.empty:
        return "empty"

    # Normalise the frame by sorting columns and filling NaNs with sentinels.
    normalized = df.sort_index(axis=1).copy()
    normalized = normalized.fillna("<NA>")

    for column in normalized.columns:
        if pd.api.types.is_object_dtype(normalized[column]):
            normalized[column] = normalized[column].map(_canonicalize_for_hash)

    # Hash a subset of rows to avoid quadratic hashing for very large frames.
    sample = normalized.head(100)
    hashed = pd.util.hash_pandas_object(sample, index=True).values.tobytes()
    digest = hashlib.sha256(hashed).hexdigest()
    return f"{len(df)}:{digest[:16]}"


def compute_company_stats(data: Any, top_n: int = 15) -> CompanyStats:
    """Compute company distribution statistics."""

    df = ensure_dataframe(data)
    if df.empty or "company" not in df.columns:
        return CompanyStats([], [], 0)

    series = df["company"].fillna("Unknown Company").astype(str)
    company_counts = series.value_counts().head(top_n)

    return CompanyStats(
        companies=company_counts.index.tolist(),
        counts=[int(v) for v in company_counts.values.tolist()],
        total_companies=int(series.nunique()),
    )


def compute_location_stats(data: Any, top_n: int = 10) -> LocationStats:
    """Compute location distribution statistics."""

    df = ensure_dataframe(data)
    if df.empty or "location" not in df.columns:
        return LocationStats([], [], 0)

    series = df["location"].fillna("Unknown Location").astype(str).str.strip()
    location_counts = series.value_counts().head(top_n)

    return LocationStats(
        locations=location_counts.index.tolist(),
        counts=[int(v) for v in location_counts.values.tolist()],
        total_locations=int(series.nunique()),
    )


_SCORE_BINS: Tuple[int, ...] = (20, 40, 60, 80, 100)
_SCORE_LABELS: Tuple[str, ...] = ("0-20", "21-40", "41-60", "61-80", "81-100")


def _build_score_distribution(series: pd.Series) -> ScoreDistribution:
    if series.empty:
        return ScoreDistribution(list(_SCORE_LABELS), [0] * len(_SCORE_LABELS))

    binned = pd.cut(
        series.clip(lower=0, upper=100),
        bins=[-0.1, *_SCORE_BINS],
        labels=_SCORE_LABELS,
    )
    counts = binned.value_counts(sort=False).reindex(_SCORE_LABELS, fill_value=0).tolist()
    return ScoreDistribution(list(_SCORE_LABELS), [int(v) for v in counts])


def compute_job_metrics(data: Any) -> JobMetrics:
    """Compute aggregate job metrics including status counts and score ranges."""

    df = ensure_dataframe(data)
    if df.empty:
        return JobMetrics(
            0, 0.0, {}, ScoreDistribution(list(_SCORE_LABELS), [0] * len(_SCORE_LABELS))
        )

    total_jobs = int(len(df))

    score_series = (
        df["match_score"].astype(float).fillna(0)
        if "match_score" in df.columns
        else pd.Series(dtype=float)
    )
    avg_score = float(score_series.mean()) if not score_series.empty else 0.0

    if "status" in df.columns:
        status_counts = {
            str(status): int(count) for status, count in df["status"].value_counts().items()
        }
    else:
        status_counts = {}

    score_distribution = _build_score_distribution(score_series)

    return JobMetrics(total_jobs, avg_score, status_counts, score_distribution)
