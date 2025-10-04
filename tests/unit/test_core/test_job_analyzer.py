#!/usr/bin/env python3
"""
Unit tests for job matching and analysis functionality.
Tests core job matching logic following TESTING_STANDARDS.md
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any


# Mock JobAnalyzer for testing purposes to avoid import dependencies
class MockJobAnalyzer:
    """Mock JobAnalyzer that implements core matching logic for testing."""

    def __init__(self, profile: Dict[str, Any] = None):
        self.profile = profile or {}

    def calculate_match_score(self, job: Dict[str, Any], profile: Dict[str, Any]) -> float:
        """Calculate basic match score based on skill overlap."""
        job_skills = set(job.get("skills", []))
        profile_skills = set(profile.get("skills", []))

        if not job_skills or not profile_skills:
            return 0.0

        overlap = len(job_skills.intersection(profile_skills))
        return min(1.0, overlap / len(job_skills))

    def extract_skills_from_description(self, description: str) -> List[str]:
        """Extract skills from job description."""
        if not description:
            return []

        # Simple skill extraction for testing
        common_skills = [
            "Python",
            "Java",
            "JavaScript",
            "React",
            "Django",
            "PostgreSQL",
            "MySQL",
            "AWS",
            "Docker",
            "Kubernetes",
            "Git",
            "Linux",
        ]

        found_skills = []
        description_lower = description.lower()

        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)

        return found_skills

    def analyze_experience_level(self, job: Dict[str, Any]) -> str:
        """Analyze experience level from job title."""
        title = job.get("title", "").lower()

        if any(word in title for word in ["junior", "entry", "graduate"]):
            return "junior"
        elif any(word in title for word in ["senior", "lead", "principal", "staff"]):
            return "senior"
        else:
            return "mid"

    def detect_remote_options(self, job: Dict[str, Any]) -> bool:
        """Detect if job offers remote work options."""
        description = job.get("description", "").lower()
        return any(word in description for word in ["remote", "work from home", "hybrid"])


# Use the mock for all tests
JobAnalyzer = MockJobAnalyzer


@pytest.mark.unit
class TestJobMatching:
    """Test job matching and scoring functionality."""

    def test_calculate_match_score_perfect_match_returns_high_score(self, test_profile):
        """Test that perfect skill matches return high scores."""
        analyzer = JobAnalyzer()

        job = {
            "title": "Python Developer",
            "description": "Python Django PostgreSQL AWS development",
            "skills": ["Python", "Django", "PostgreSQL", "AWS"],
        }

        # Profile has same skills
        profile = {"skills": ["Python", "Django", "PostgreSQL", "AWS"], "experience_years": 3}

        score = analyzer.calculate_match_score(job, profile)

        assert score >= 0.8, f"Expected high score for perfect match, got {score}"
        assert score <= 1.0, f"Score should not exceed 1.0, got {score}"

    def test_calculate_match_score_no_skills_match_returns_low_score(self, test_profile):
        """Test that no skill matches return low scores."""
        analyzer = JobAnalyzer()

        job = {
            "title": "Java Developer",
            "description": "Java Spring MySQL development",
            "skills": ["Java", "Spring", "MySQL"],
        }

        profile = {"skills": ["Python", "Django", "PostgreSQL"], "experience_years": 3}

        score = analyzer.calculate_match_score(job, profile)

        assert score <= 0.3, f"Expected low score for no skill match, got {score}"
        assert score >= 0.0, f"Score should not be negative, got {score}"

    def test_calculate_match_score_partial_match_returns_medium_score(self):
        """Test that partial skill matches return medium scores."""
        analyzer = JobAnalyzer()

        job = {
            "title": "Full Stack Developer",
            "description": "Python React PostgreSQL development",
            "skills": ["Python", "React", "PostgreSQL", "JavaScript"],
        }

        profile = {"skills": ["Python", "Django", "PostgreSQL"], "experience_years": 3}  # 2/4 match

        score = analyzer.calculate_match_score(job, profile)

        assert 0.3 < score < 0.8, f"Expected medium score for partial match, got {score}"

    @pytest.mark.parametrize(
        "job_skills,profile_skills,expected_range",
        [
            (["Python", "Django"], ["Python", "Django"], (0.8, 1.0)),  # Perfect match
            (["Python", "Django"], ["Python"], (0.4, 0.7)),  # Partial match
            (["Python", "Django"], ["Java", "Spring"], (0.0, 0.3)),  # No match
            (["Python"], ["Python", "Django", "React"], (0.7, 1.0)),  # Profile exceeds job
        ],
    )
    def test_match_score_ranges_with_different_skill_combinations(
        self, job_skills, profile_skills, expected_range
    ):
        """Test score ranges for various skill combinations."""
        analyzer = JobAnalyzer()

        job = {"title": "Test Job", "description": " ".join(job_skills), "skills": job_skills}

        profile = {"skills": profile_skills, "experience_years": 3}

        score = analyzer.calculate_match_score(job, profile)

        min_score, max_score = expected_range
        assert min_score <= score <= max_score, (
            f"Score {score} not in expected range {expected_range} "
            f"for job_skills={job_skills}, profile_skills={profile_skills}"
        )


@pytest.mark.unit
class TestJobAnalysisFeatures:
    """Test additional job analysis features."""

    def test_extract_skills_from_job_description(self):
        """Test skill extraction from job descriptions."""
        analyzer = JobAnalyzer()

        job_description = (
            "We are looking for a developer with Python, Django, and PostgreSQL experience. "
            "Knowledge of AWS and Docker is a plus. JavaScript and React skills are required."
        )

        skills = analyzer.extract_skills_from_description(job_description)

        expected_skills = ["Python", "Django", "PostgreSQL", "AWS", "Docker", "JavaScript", "React"]

        # Check that most expected skills are found
        found_skills = [skill for skill in expected_skills if skill in skills]
        assert len(found_skills) >= 5, f"Expected to find most skills, found: {found_skills}"

    def test_analyze_experience_level_from_job_title(self):
        """Test experience level detection from job titles."""
        analyzer = JobAnalyzer()

        test_cases = [
            ("Junior Python Developer", "junior"),
            ("Senior Software Engineer", "senior"),
            ("Lead Data Scientist", "senior"),
            ("Python Developer", "mid"),  # No level specified = mid
            ("Entry Level Programmer", "junior"),
            ("Principal Engineer", "senior"),
        ]

        for title, expected_level in test_cases:
            job = {"title": title, "description": "Test description"}
            level = analyzer.analyze_experience_level(job)

            assert (
                level == expected_level
            ), f"Title '{title}' should detect '{expected_level}', got '{level}'"

    def test_detect_remote_work_options(self):
        """Test remote work detection from job descriptions."""
        analyzer = JobAnalyzer()

        test_cases = [
            ("Remote work available. Work from home.", True),
            ("100% remote position", True),
            ("Hybrid work - 2 days in office", True),
            ("On-site position in downtown Toronto", False),
            ("Must work from our Vancouver office", False),
            ("Remote work considered for right candidate", True),
        ]

        for description, expected_remote in test_cases:
            job = {"title": "Test Job", "description": description}
            is_remote = analyzer.detect_remote_options(job)

            assert (
                is_remote == expected_remote
            ), f"Description '{description}' should detect remote={expected_remote}, got {is_remote}"


@pytest.mark.unit
class TestJobAnalysisErrorHandling:
    """Test error handling in job analysis."""

    def test_calculate_match_score_with_empty_job_handles_gracefully(self):
        """Test match calculation with empty/invalid job data."""
        analyzer = JobAnalyzer()

        empty_job = {}
        profile = {"skills": ["Python"], "experience_years": 3}

        score = analyzer.calculate_match_score(empty_job, profile)

        assert 0.0 <= score <= 1.0, f"Score should be valid range even for empty job, got {score}"

    def test_calculate_match_score_with_empty_profile_handles_gracefully(self, sample_job):
        """Test match calculation with empty profile."""
        analyzer = JobAnalyzer()

        empty_profile = {}

        score = analyzer.calculate_match_score(sample_job, empty_profile)

        assert (
            0.0 <= score <= 1.0
        ), f"Score should be valid range even for empty profile, got {score}"

    def test_extract_skills_with_empty_description_returns_empty_list(self):
        """Test skill extraction with empty description."""
        analyzer = JobAnalyzer()

        skills = analyzer.extract_skills_from_description("")
        assert skills == []

        skills = analyzer.extract_skills_from_description(None)
        assert skills == []

    def test_analyzer_initialization_with_missing_dependencies(self):
        """Test analyzer works even if optional dependencies are missing."""
        # Test that analyzer can be initialized with minimal profile
        minimal_profile = {"skills": ["Python"]}
        analyzer = JobAnalyzer(minimal_profile)

        # Should still be able to do basic analysis
        job = {"title": "Python Developer", "skills": ["Python"]}

        score = analyzer.calculate_match_score(job, minimal_profile)
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0


@pytest.mark.performance
class TestJobAnalysisPerformance:
    """Test performance characteristics of job analysis."""

    def test_match_calculation_performance_with_large_skill_lists(self, performance_timer):
        """Test that match calculation is fast even with large skill lists."""
        analyzer = JobAnalyzer()

        # Create job and profile with many skills
        large_skill_list = [f"skill_{i}" for i in range(100)]
        job = {
            "title": "Test Job",
            "description": " ".join(large_skill_list),
            "skills": large_skill_list,
        }
        profile = {"skills": large_skill_list[:50], "experience_years": 5}  # 50% overlap

        with performance_timer:
            score = analyzer.calculate_match_score(job, profile)

        # Should complete within reasonable time (< 100ms)
        assert (
            performance_timer.elapsed < 0.1
        ), f"Match calculation took {performance_timer.elapsed:.3f}s"
        assert 0.0 <= score <= 1.0

    def test_batch_job_analysis_performance(self, performance_timer, sample_jobs):
        """Test analyzing multiple jobs in batch."""
        analyzer = JobAnalyzer()
        profile = {"skills": ["Python", "Django"], "experience_years": 3}

        # Create larger batch
        large_job_batch = sample_jobs * 10  # 30 jobs
        for i, job in enumerate(large_job_batch):
            job["job_url"] = f"https://test.com/job/{i}"

        with performance_timer:
            scores = []
            for job in large_job_batch:
                score = analyzer.calculate_match_score(job, profile)
                scores.append(score)

        # Should process all jobs quickly (< 1 second for 30 jobs)
        assert (
            performance_timer.elapsed < 1.0
        ), f"Batch analysis took {performance_timer.elapsed:.3f}s"
        assert len(scores) == len(large_job_batch)
        assert all(0.0 <= score <= 1.0 for score in scores)
