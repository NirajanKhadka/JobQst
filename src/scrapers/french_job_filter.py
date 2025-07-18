#!/usr/bin/env python3
"""
French Job Filter - Specialized filter for removing French jobs and Montreal jobs with penalty scoring.
Provides intelligent job filtering based on language, location, and content analysis.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from rich.console import Console

console = Console()


@dataclass
class FilterResult:
    """Result of job filtering operation."""

    should_keep: bool
    score: float
    reasons: List[str]
    penalties: List[str]
    warnings: List[str]


class FrenchJobFilter:
    """
    Intelligent job filtering system that removes French jobs and Montreal jobs.
    Provides penalty scoring for filtered jobs.
    """

    def __init__(
        self,
        profile_keywords: Optional[List[str]] = None,
        profile_skills: Optional[List[str]] = None,
    ):
        # French language patterns (common French words in job postings)
        self.french_patterns = [
            r"\b(?:analyste|développeur|ingénieur|consultant|gestionnaire|coordonnateur|spécialiste|technicien|assistant|directeur|chef|responsable)\b",
            r"\b(?:expérience|compétences|connaissances|maîtrise|expertise|formation|diplôme|certification)\b",
            r"\b(?:entreprise|société|organisation|équipe|projet|mission|objectif|stratégie)\b",
            r"\b(?:communication|collaboration|travail|réunion|présentation|rapport|documentation)\b",
            r"\b(?:technologie|système|application|logiciel|base de données|interface|plateforme)\b",
            r"\b(?:analyse|développement|conception|implémentation|maintenance|support|formation)\b",
            r"\b(?:préférence|exigence|responsabilité|fonction|rôle|poste|emploi|carrière)\b",
            r"\b(?:opportunité|défi|environnement|culture|valeurs|bénéfices|avantages)\b",
            r"\b(?:présentement|actuellement|régulièrement|fréquemment|occasionnellement)\b",
            r"\b(?:préférablement|idéalement|obligatoirement|nécessairement|essentiellement)\b",
        ]

        # Montreal location patterns
        self.montreal_patterns = [
            r"\b(?:montréal|montreal)\b",
            r"\b(?:mtl|mtl\.)\b",
            r"\b(?:québec|quebec)\b",
            r"\b(?:qc|qc\.)\b",
            r"\b(?:h2[xy]\s*\d[a-z]\s*\d[a-z])\b",  # Montreal postal codes
            r"\b(?:514|438|450|579)\s*\d{3}\s*\d{4}\b",  # Montreal area codes
        ]

        # French company indicators
        self.french_company_indicators = [
            r"\b(?:desjardins|bmo|rbc|td|scotiabank|national bank|banque)\b",
            r"\b(?:air canada|bombardier|saputo|power corporation|couche-tard)\b",
            r"\b(?:québecor|videotron|cogeco|bell québec|rogers québec)\b",
            r"\b(?:hydro-québec|société des alcools|saq|loto-québec)\b",
            r"\b(?:transit montréal|stm|réseau express métropolitain|rem)\b",
        ]

        # Use profile keywords and skills instead of hardcoded tech keywords
        self.profile_keywords = profile_keywords or []
        self.profile_skills = profile_skills or []

        # Combine keywords and skills for matching
        self.user_skills = list(set(self.profile_keywords + self.profile_skills))

        # Compile regex patterns for performance
        self.french_regex = re.compile("|".join(self.french_patterns), re.IGNORECASE)
        self.montreal_regex = re.compile("|".join(self.montreal_patterns), re.IGNORECASE)
        self.french_company_regex = re.compile(
            "|".join(self.french_company_indicators), re.IGNORECASE
        )

        # Scoring weights
        self.scoring_weights = {
            "french_language": -50.0,  # Heavy penalty for French
            "montreal_location": -30.0,  # Penalty for Montreal
            "french_company": -20.0,  # Penalty for French companies
            "skill_match_bonus": 10.0,  # Bonus for matching user skills
            "remote_bonus": 15.0,  # Bonus for remote work
        }

    def filter_job(self, job: Dict) -> FilterResult:
        """
        Filter a job and return whether it should be kept along with scoring.

        Args:
            job: Job dictionary with title, company, location, summary, etc.

        Returns:
            FilterResult with keep decision, score, and reasons
        """
        score = 100.0  # Start with perfect score
        reasons = []
        penalties = []
        warnings = []

        # Combine all text for analysis
        text_to_analyze = " ".join(
            [
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("summary", ""),
                job.get("description", ""),
            ]
        ).lower()

        # Check for French language
        french_matches = self.french_regex.findall(text_to_analyze)
        if french_matches:
            french_penalty = self.scoring_weights["french_language"]
            score += french_penalty
            penalties.append(f"French language detected: {len(french_matches)} matches")
            # Convert matches to strings for display
            french_terms = []
            for match in french_matches:
                if isinstance(match, tuple):
                    french_terms.extend([term for term in match if term])
                else:
                    french_terms.append(str(match))
            reasons.append(f"French content: {', '.join(set(french_terms[:3]))}")

        # Check for Montreal location
        montreal_matches = self.montreal_regex.findall(text_to_analyze)
        if montreal_matches:
            montreal_penalty = self.scoring_weights["montreal_location"]
            score += montreal_penalty
            penalties.append(f"Montreal location detected: {len(montreal_matches)} matches")
            # Convert matches to strings for display
            montreal_terms = []
            for match in montreal_matches:
                if isinstance(match, tuple):
                    montreal_terms.extend([term for term in match if term])
                else:
                    montreal_terms.append(str(match))
            reasons.append(f"Montreal location: {', '.join(set(montreal_terms[:3]))}")

        # Check for French companies
        french_company_matches = self.french_company_regex.findall(text_to_analyze)
        if french_company_matches:
            company_penalty = self.scoring_weights["french_company"]
            score += company_penalty
            penalties.append(f"French company detected: {len(french_company_matches)} matches")
            # Convert matches to strings for display
            company_terms = []
            for match in french_company_matches:
                if isinstance(match, tuple):
                    company_terms.extend([term for term in match if term])
                else:
                    company_terms.append(str(match))
            reasons.append(f"French company: {', '.join(set(company_terms[:3]))}")

        # Check for skill matches using profile keywords and skills
        skill_matches = []
        for skill in self.user_skills:
            if skill.lower() in text_to_analyze:
                skill_matches.append(skill)

        if skill_matches:
            skill_bonus = self.scoring_weights["skill_match_bonus"] * len(skill_matches)
            score += skill_bonus
            reasons.append(f"Skill matches: {', '.join(skill_matches[:5])}")  # Show first 5 matches

        # Check for remote work bonus
        remote_keywords = [
            "remote",
            "work from home",
            "wfh",
            "telecommute",
            "virtual",
            "distributed",
        ]
        remote_matches = sum(1 for keyword in remote_keywords if keyword in text_to_analyze)
        if remote_matches > 0:
            remote_bonus = self.scoring_weights["remote_bonus"]
            score += remote_bonus
            reasons.append(f"Remote work opportunity detected")

        # Determine if job should be kept
        should_keep = score >= 50.0  # Keep jobs with score >= 50

        # Add warnings for borderline cases
        if 50 <= score < 70:
            warnings.append("Borderline score - job kept but with penalties")
        elif score < 30:
            warnings.append("Very low score - job heavily penalized")

        return FilterResult(
            should_keep=should_keep,
            score=round(score, 2),
            reasons=reasons,
            penalties=penalties,
            warnings=warnings,
        )

    def filter_jobs_batch(self, jobs: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Filter a batch of jobs and return kept jobs, filtered jobs, and statistics.

        Args:
            jobs: List of job dictionaries

        Returns:
            Tuple of (kept_jobs, filtered_jobs, stats)
        """
        kept_jobs = []
        filtered_jobs = []
        stats = {
            "total_jobs": len(jobs),
            "kept_jobs": 0,
            "filtered_jobs": 0,
            "avg_score_kept": 0.0,
            "avg_score_filtered": 0.0,
            "french_filtered": 0,
            "montreal_filtered": 0,
            "french_company_filtered": 0,
        }

        total_score_kept = 0.0
        total_score_filtered = 0.0

        for job in jobs:
            result = self.filter_job(job)

            if result.should_keep:
                kept_jobs.append(job)
                stats["kept_jobs"] += 1
                total_score_kept += result.score
            else:
                filtered_jobs.append(job)
                stats["filtered_jobs"] += 1
                total_score_filtered += result.score

        # Calculate averages
        if stats["kept_jobs"] > 0:
            stats["avg_score_kept"] = round(total_score_kept / stats["kept_jobs"], 2)
        if stats["filtered_jobs"] > 0:
            stats["avg_score_filtered"] = round(total_score_filtered / stats["filtered_jobs"], 2)

        return kept_jobs, filtered_jobs, stats


# Convenience functions
def filter_job(
    job: Dict,
    profile_keywords: Optional[List[str]] = None,
    profile_skills: Optional[List[str]] = None,
) -> FilterResult:
    """Convenience function to filter a single job."""
    filter_instance = FrenchJobFilter(profile_keywords, profile_skills)
    return filter_instance.filter_job(job)


def filter_jobs_batch(
    jobs: List[Dict],
    profile_keywords: Optional[List[str]] = None,
    profile_skills: Optional[List[str]] = None,
) -> Tuple[List[Dict], List[Dict], Dict]:
    """Convenience function to filter a batch of jobs."""
    filter_instance = FrenchJobFilter(profile_keywords, profile_skills)
    return filter_instance.filter_jobs_batch(jobs)
