#!/usr/bin/env python3
"""
Multi-Site JobSpy Workers - Temporary Implementation for Phase 1 Consolidation

This is a simplified implementation to support the unified pipeline architecture.
It provides basic JobSpy integration functionality while the full implementation
is being developed.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
from rich.console import Console

from src.core.unified_deduplication import deduplicate_jobs_unified

console = Console()


@dataclass
class JobSpyWorkerConfig:
    """Configuration for JobSpy workers."""

    sites: List[str] = None
    locations: List[str] = None
    search_terms: List[str] = None
    max_jobs_per_site: int = 50
    concurrency: int = 4


class MultiSiteJobSpyWorkers:
    """
    Simplified JobSpy workers implementation for Phase 1 consolidation.

    This provides basic functionality to support the unified pipeline
    while maintaining compatibility with the existing architecture.
    """

    def __init__(
        self,
        profile_name: str = "Nirajan",
        max_jobs_per_site: int = 50,
        concurrency: int = 4,
    ):
        self.profile_name = profile_name
        self.max_jobs_per_site = max_jobs_per_site
        self.concurrency = concurrency
        self.console = Console()

        # Initialize default config
        self.config = JobSpyWorkerConfig(
            sites=["indeed", "linkedin"],
            locations=["Toronto, ON", "Vancouver, BC", "Calgary, AB"],
            search_terms=["Software Developer", "Python Developer", "Data Analyst"],
            max_jobs_per_site=max_jobs_per_site,
            concurrency=concurrency,
        )

    def _filter_relevant_jobs(
        self, jobs_df: pd.DataFrame, search_term: str
    ) -> pd.DataFrame:
        """
        Filter jobs to ensure relevance to the search term.

        Removes jobs that don't match the actual search intent (e.g., Java Developer
        when searching for Python Developer).
        """
        if jobs_df.empty:
            return jobs_df

        # Extract key terms from search query
        search_lower = search_term.lower()
        search_keywords = set(search_lower.split())

        # Technology-specific filters
        tech_conflicts = {
            "python": [
                "java developer",
                "java engineer",
                ".net developer",
                "c# developer",
                "data developer",
                "etl developer",
                "sql developer",
            ],
            "java": [
                "python developer",
                ".net developer",
                "c# developer",
                "ruby developer",
            ],
            ".net": ["java developer", "python developer", "ruby developer"],
            "javascript": ["java developer", "python developer", ".net developer"],
            "data analyst": ["software engineer", "java developer", "python developer"],
            "data scientist": ["software engineer", "java developer"],
        }

        def is_relevant(row):
            """Check if a job is relevant to the search term"""
            title = str(row.get("title", "")).lower()
            description = str(row.get("description", "")).lower()
            combined = f"{title} {description}"

            # Check for conflicting technologies in title (strict check)
            for tech, conflicts in tech_conflicts.items():
                if tech in search_lower:
                    # If searching for this tech, exclude jobs with conflicting tech in title
                    if any(conflict in title for conflict in conflicts):
                        return False

            # Specific rules for Python searches
            if "python" in search_lower:
                # Title must explicitly mention Python OR be very generic
                if "developer" in title or "engineer" in title:
                    # Require Python mention unless it's a very generic title
                    if "python" not in combined:
                        # Exclude if it has any other specific technology
                        if any(
                            x in title
                            for x in [
                                "java",
                                "c#",
                                ".net",
                                "c++",
                                "data",
                                "sql",
                                "etl",
                                "bi ",
                            ]
                        ):
                            return False
                    # Even if Python is in description, exclude if title has conflicting tech
                    if any(
                        x in title
                        for x in [
                            "java ",
                            "c#",
                            ".net",
                            "c++",
                            "data analyst",
                            "sql developer",
                        ]
                    ):
                        return False

            # Specific rules for data analyst searches
            if "data analyst" in search_lower:
                # Exclude pure software engineering roles
                if any(
                    x in title
                    for x in [
                        "software engineer",
                        "full stack",
                        "backend engineer",
                        "frontend engineer",
                        "python developer",
                        "java developer",
                    ]
                ):
                    if "data" not in title and "analyst" not in title:
                        return False

            # Must contain at least one key search keyword in title or description
            if not any(
                keyword in combined for keyword in search_keywords if len(keyword) > 2
            ):
                return False

            return True

        # Apply filter
        filtered_df = jobs_df[jobs_df.apply(is_relevant, axis=1)].copy()
        return filtered_df

    async def run_discovery(
        self,
        sites: List[str] = None,
        locations: List[str] = None,
        search_terms: List[str] = None,
        max_jobs_per_site: int = 50,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Run JobSpy discovery across multiple sites.

        Returns a pandas DataFrame with job data in JobSpy format.
        """
        try:
            # Use provided parameters or fall back to config
            sites = sites or self.config.sites or ["indeed", "linkedin"]
            locations = locations or self.config.locations or ["Toronto, ON"]
            search_terms = (
                search_terms or self.config.search_terms or ["Software Developer"]
            )

            console.print(
                f"[cyan]🔍 JobSpy Discovery: {len(sites)} sites × {len(locations)} locations × {len(search_terms)} terms[/cyan]"
            )

            # Try to import and use JobSpy
            try:
                from jobspy import scrape_jobs

                all_jobs = []

                for site in sites:
                    for location in locations:
                        for search_term in search_terms:
                            try:
                                console.print(
                                    f"[yellow]  Searching {site}: {search_term} in {location}[/yellow]"
                                )

                                # Run JobSpy scraping
                                console.print(
                                    f"[dim]    JobSpy params: site={site}, term='{search_term}', location='{location}', results={min(max_jobs_per_site, 20)}[/dim]"
                                )
                                # Determine country for site-specific parameters
                                is_canada = any(
                                    x in location.upper()
                                    for x in [
                                        "CA",
                                        "ON",
                                        "BC",
                                        "AB",
                                        "QC",
                                        "NS",
                                        "NB",
                                        "MB",
                                        "SK",
                                        "PE",
                                        "NL",
                                        "YT",
                                        "NT",
                                        "NU",
                                    ]
                                )
                                country = "Canada" if is_canada else "USA"

                                # Prepare site-specific parameters
                                scrape_params = {
                                    "site_name": site,
                                    "search_term": search_term,
                                    "location": location,
                                    "results_wanted": min(max_jobs_per_site, 20),
                                    "hours_old": 168,  # 7 days
                                    "country_indeed": country,  # Used by Indeed and Glassdoor
                                }

                                # Site-specific location formatting
                                if site == "glassdoor":
                                    # Glassdoor works better with city name only for Canadian locations
                                    # Extract just the city name if format is "City, Province"
                                    if "," in location:
                                        city_only = location.split(",")[0].strip()
                                        scrape_params["location"] = city_only
                                        console.print(
                                            f"[dim]    Glassdoor: using simplified location '{city_only}' (was '{location}')[/dim]"
                                        )
                                    console.print(
                                        f"[dim]    Glassdoor country: {country}[/dim]"
                                    )
                                elif site == "indeed":
                                    console.print(
                                        f"[dim]    Indeed country: {country}[/dim]"
                                    )

                                jobs_df = scrape_jobs(**scrape_params)

                                if jobs_df is not None and not jobs_df.empty:
                                    # Add metadata
                                    jobs_df["search_term"] = search_term
                                    jobs_df["search_location"] = location
                                    jobs_df["source_site"] = site

                                    # Apply relevance filtering
                                    original_count = len(jobs_df)
                                    jobs_df = self._filter_relevant_jobs(
                                        jobs_df, search_term
                                    )
                                    filtered_count = len(jobs_df)

                                    if not jobs_df.empty:
                                        all_jobs.append(jobs_df)
                                        console.print(
                                            f"[green]    Found {filtered_count} jobs[/green]"
                                        )
                                        if filtered_count < original_count:
                                            console.print(
                                                f"[dim]    (filtered {original_count - filtered_count} irrelevant jobs)[/dim]"
                                            )
                                    else:
                                        console.print(
                                            f"[yellow]    No relevant jobs found (filtered all {original_count})[/yellow]"
                                        )
                                else:
                                    console.print(f"[yellow]    No jobs found[/yellow]")

                                # Small delay to be respectful
                                await asyncio.sleep(1)

                            except Exception as e:
                                error_msg = str(e)
                                console.print(
                                    f"[red]    ❌ Error with {site}/{search_term}:[/red]"
                                )
                                console.print(f"[red]       {error_msg}[/red]")

                                # Site-specific troubleshooting hints
                                if site == "glassdoor":
                                    console.print(
                                        f"[yellow]    💡 Glassdoor tip: Ensure location format is correct (e.g., 'Toronto, ON')[/yellow]"
                                    )
                                elif site == "linkedin":
                                    console.print(
                                        f"[yellow]    💡 LinkedIn tip: May require specific location codes or authentication[/yellow]"
                                    )

                                continue

                # Combine all results
                if all_jobs:
                    combined_df = pd.concat(all_jobs, ignore_index=True)
                    console.print(
                        f"[green]✅ JobSpy Discovery completed: {len(combined_df)} total jobs[/green]"
                    )
                    return combined_df
                else:
                    console.print(
                        "[yellow]⚠️ No jobs found across all searches[/yellow]"
                    )
                    return pd.DataFrame()

            except ImportError:
                console.print(
                    "[red]❌ JobSpy not installed. Install with: pip install python-jobspy[/red]"
                )
                # Return empty DataFrame with expected columns
                return pd.DataFrame(
                    columns=[
                        "title",
                        "company",
                        "location",
                        "job_url",
                        "description",
                        "date_posted",
                        "search_term",
                        "search_location",
                        "source_site",
                    ]
                )

        except Exception as e:
            console.print(f"[red]❌ JobSpy discovery failed: {e}[/red]")
            return pd.DataFrame()

    async def enrich_descriptions(
        self, jobs_df: pd.DataFrame, concurrency: int = 4
    ) -> pd.DataFrame:
        """
        Enrich job descriptions (placeholder implementation).

        In the full implementation, this would fetch missing descriptions
        from job URLs asynchronously.
        """
        console.print(f"[cyan]📝 Description enrichment: {len(jobs_df)} jobs[/cyan]")

        # For now, just return the DataFrame as-is
        # In the full implementation, this would:
        # 1. Identify jobs with missing/short descriptions
        # 2. Fetch full descriptions from job URLs
        # 3. Update the DataFrame with enriched content

        return jobs_df

    async def run_comprehensive_search(
        self,
        location_set: str = "canada_comprehensive",
        query_preset: str = "comprehensive",
        sites: Optional[List[str]] = None,
        per_site_concurrency: int = 4,
        max_total_jobs: Optional[int] = None,
        **kwargs,
    ) -> "MultiSiteResult":
        """
        Run comprehensive JobSpy search across multiple sites and locations.

        Returns a MultiSiteResult object with combined_data DataFrame.
        """
        from src.config.jobspy_integration_config import (
            JOBSPY_LOCATION_SETS,
            JOBSPY_QUERY_PRESETS,
        )

        # Get locations from predefined sets
        if location_set in JOBSPY_LOCATION_SETS:
            locations = JOBSPY_LOCATION_SETS[location_set][:10]  # Limit for testing
        else:
            locations = ["Toronto, ON", "Vancouver, BC", "Montreal, QC"]

        # Get search terms from presets
        if query_preset in JOBSPY_QUERY_PRESETS:
            search_terms = JOBSPY_QUERY_PRESETS[query_preset][:5]  # Limit for testing
        else:
            search_terms = ["Software Developer", "Python Developer"]

        # Use provided sites or defaults
        sites = sites or ["indeed", "linkedin"]

        console.print(
            f"[cyan]🔍 Comprehensive search: {len(sites)} sites × {len(locations)} locations × {len(search_terms)} terms[/cyan]"
        )

        # Run discovery
        jobs_df = await self.run_discovery(
            sites=sites,
            locations=locations,
            search_terms=search_terms,
            max_jobs_per_site=self.max_jobs_per_site,
        )

        # Return result in expected format
        return MultiSiteResult(combined_data=jobs_df)

    async def run_optimized_description_fetching(
        self, jobs_df: pd.DataFrame, max_concurrency: int = 24
    ) -> pd.DataFrame:
        """
        Fetch and enrich job descriptions.

        This is a placeholder implementation for Phase 1.
        """
        console.print(
            f"[cyan]📝 Description fetching: {len(jobs_df)} jobs (max_concurrency={max_concurrency})[/cyan]"
        )

        # For Phase 1, just return the DataFrame as-is
        # In the full implementation, this would fetch missing descriptions
        return jobs_df

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return {
            "profile_name": self.profile_name,
            "max_jobs_per_site": self.max_jobs_per_site,
            "concurrency": self.concurrency,
        }


@dataclass
class MultiSiteResult:
    """Result object for multi-site JobSpy searches."""

    combined_data: pd.DataFrame
    stats: Dict[str, Any] = None

    def __post_init__(self):
        if self.stats is None:
            self.stats = {
                "total_jobs": (
                    len(self.combined_data) if self.combined_data is not None else 0
                ),
                "sites_searched": 0,
                "locations_searched": 0,
            }


# Convenience function for backward compatibility
async def run_multi_site_jobspy_discovery(
    sites: List[str] = None,
    locations: List[str] = None,
    search_terms: List[str] = None,
    max_jobs_per_site: int = 50,
    concurrency: int = 4,
) -> pd.DataFrame:
    """
    Convenience function to run JobSpy discovery.

    This provides a simple interface for the unified pipeline.
    """
    workers = MultiSiteJobSpyWorkers(
        profile_name="default",
        max_jobs_per_site=max_jobs_per_site,
        concurrency=concurrency,
    )
    return await workers.run_discovery(
        sites=sites,
        locations=locations,
        search_terms=search_terms,
        max_jobs_per_site=max_jobs_per_site,
    )


if __name__ == "__main__":
    # Test the implementation
    async def test_jobspy_workers():
        console.print("[bold blue]🧪 Testing JobSpy Workers Implementation[/bold blue]")

        result = await run_multi_site_jobspy_discovery(
            sites=["indeed"],
            locations=["Toronto, ON"],
            search_terms=["Python Developer"],
            max_jobs_per_site=5,
        )

        console.print(f"[green]Test completed: {len(result)} jobs found[/green]")
        if not result.empty:
            console.print(f"[cyan]Sample columns: {list(result.columns)}[/cyan]")

    asyncio.run(test_jobspy_workers())
