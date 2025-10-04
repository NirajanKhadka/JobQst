#!/usr/bin/env python3
"""
Language Detection Utility for AutoJobAgent
Detects and filters out non-English job postings before processing.
"""

import logging
from typing import Dict, List, Optional, Tuple
import re
from langdetect import detect, detect_langs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobLanguageDetector:
    """Detects and filters job postings by language."""

    def __init__(self, english_threshold: float = 0.6, french_threshold: float = 0.4):
        """
        Initialize language detector.

        Args:
            english_threshold: Minimum confidence for English detection
            french_threshold: Maximum allowable French confidence before filtering
        """
        self.english_threshold = english_threshold
        self.french_threshold = french_threshold

        # Common French job posting indicators
        self.french_indicators = [
            "emploi",
            "travail",
            "poste",
            "carrière",
            "candidature",
            "expérience",
            "compétences",
            "formation",
            "diplôme",
            "salaire",
            "horaire",
            "temps partiel",
            "temps plein",
            "entreprise",
            "société",
            "équipe",
            "département",
            "responsabilités",
            "qualifications",
            "exigences",
            "bilingue",
            "français",
            "anglais",
            "québec",
            "montreal",
            "toronto",
            "vancouver",
            "ottawa",
            "calgary",
        ]

        # Common English job posting indicators
        self.english_indicators = [
            "job",
            "position",
            "role",
            "career",
            "opportunity",
            "experience",
            "skills",
            "requirements",
            "qualifications",
            "responsibilities",
            "salary",
            "benefits",
            "full-time",
            "part-time",
            "remote",
            "hybrid",
            "on-site",
            "company",
            "team",
            "department",
            "apply",
            "application",
            "resume",
        ]

    def detect_job_language(self, job_data: Dict) -> Dict:
        """
        Detect language of a job posting.

        Args:
            job_data: Dictionary containing job information

        Returns:
            Dictionary with language detection results
        """
        try:
            # Combine relevant text fields
            text_fields = []

            for field in ["title", "summary", "job_description", "requirements", "company"]:
                if field in job_data and job_data[field]:
                    text_fields.append(str(job_data[field]))

            combined_text = " ".join(text_fields)

            if not combined_text.strip():
                return {
                    "detected_language": "unknown",
                    "confidence": 0.0,
                    "languages": [],
                    "should_process": False,
                    "reason": "No text content to analyze",
                }

            # Clean text for better detection
            cleaned_text = self._clean_text(combined_text)

            # Perform language detection
            detection_result = self._detect_with_fallback(cleaned_text)

            if not detection_result:
                return {
                    "detected_language": "unknown",
                    "confidence": 0.0,
                    "languages": [],
                    "should_process": False,
                    "reason": "Language detection failed",
                }

            primary_lang = detection_result[0]
            confidence = detection_result[1]

            # Get detailed language probabilities
            lang_probs = self._get_language_probabilities(cleaned_text)

            # Calculate keyword-based indicators
            french_score = self._calculate_french_indicators(combined_text.lower())
            english_score = self._calculate_english_indicators(combined_text.lower())

            # Make processing decision
            should_process, reason = self._should_process_job(
                primary_lang, confidence, lang_probs, french_score, english_score
            )

            return {
                "detected_language": primary_lang,
                "confidence": confidence,
                "languages": lang_probs,
                "french_indicator_score": french_score,
                "english_indicator_score": english_score,
                "should_process": should_process,
                "reason": reason,
                "text_length": len(cleaned_text),
            }

        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return {
                "detected_language": "error",
                "confidence": 0.0,
                "languages": [],
                "should_process": False,
                "reason": f"Detection error: {str(e)}",
            }

    def _clean_text(self, text: str) -> str:
        """Clean text for better language detection."""
        # Remove URLs, emails, and special characters
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _detect_with_fallback(self, text: str) -> Optional[Tuple[str, float]]:
        """Detect language with fallback mechanisms."""
        try:
            # Primary detection
            detected_lang = detect(text)

            # Get confidence from detailed detection
            lang_list = detect_langs(text)
            confidence = 0.0

            for lang_obj in lang_list:
                if lang_obj.lang == detected_lang:
                    confidence = lang_obj.prob
                    break

            return detected_lang, confidence

        except Exception:
            # Fallback to keyword-based detection
            french_score = self._calculate_french_indicators(text.lower())
            english_score = self._calculate_english_indicators(text.lower())

            if french_score > english_score and french_score > 0.3:
                return "fr", french_score
            elif english_score > 0.3:
                return "en", english_score

            return None
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None

    def _get_language_probabilities(self, text: str) -> List[Dict]:
        """Get detailed language probabilities."""
        try:
            lang_list = detect_langs(text)
            return [{"language": lang.lang, "probability": lang.prob} for lang in lang_list]
        except Exception as e:
            logger.debug("Language detection failed: %s", str(e))
            return []

    def _calculate_french_indicators(self, text: str) -> float:
        """Calculate French language indicator score."""
        if not text:
            return 0.0

        french_count = sum(1 for indicator in self.french_indicators if indicator in text)
        return min(french_count / len(self.french_indicators), 1.0)

    def _calculate_english_indicators(self, text: str) -> float:
        """Calculate English language indicator score."""
        if not text:
            return 0.0

        english_count = sum(1 for indicator in self.english_indicators if indicator in text)
        return min(english_count / len(self.english_indicators), 1.0)

    def _should_process_job(
        self,
        primary_lang: str,
        confidence: float,
        lang_probs: List[Dict],
        french_score: float,
        english_score: float,
    ) -> Tuple[bool, str]:
        """
        Determine if job should be processed based on language detection.

        Returns:
            Tuple of (should_process, reason)
        """
        # Get French probability from detailed detection
        french_prob = 0.0
        english_prob = 0.0

        for lang_data in lang_probs:
            if lang_data["language"] == "fr":
                french_prob = lang_data["probability"]
            elif lang_data["language"] == "en":
                english_prob = lang_data["probability"]

        # Rule 1: If French probability > threshold, don't process
        if french_prob >= self.french_threshold:
            return (
                False,
                f"French probability too high: {french_prob:.2f} >= {self.french_threshold}",
            )

        # Rule 2: If primary language is French with high confidence, don't process
        if primary_lang == "fr" and confidence >= 0.7:
            return False, f"Detected as French with high confidence: {confidence:.2f}"

        # Rule 3: If French indicators are too strong, don't process
        if french_score >= 0.5:
            return False, f"High French keyword indicators: {french_score:.2f}"

        # Rule 4: If English probability is good or English indicators are strong, process
        if english_prob >= self.english_threshold or english_score >= 0.3:
            return True, f"English probability: {english_prob:.2f}, indicators: {english_score:.2f}"

        # Rule 5: If primary language is English, process
        if primary_lang == "en":
            return True, f"Detected as English with confidence: {confidence:.2f}"

        # Rule 6: Unknown or other languages - don't process for safety
        return False, f"Language {primary_lang} not suitable for processing"

    def filter_jobs_by_language(self, jobs: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a list of jobs by language.

        Args:
            jobs: List of job dictionaries

        Returns:
            Tuple of (processable_jobs, filtered_jobs)
        """
        processable_jobs = []
        filtered_jobs = []

        for job in jobs:
            detection_result = self.detect_job_language(job)

            # Add language detection metadata to job
            job["language_detection"] = detection_result

            if detection_result["should_process"]:
                processable_jobs.append(job)
            else:
                filtered_jobs.append(job)

        logger.info(
            f"Language filtering: {len(processable_jobs)} processable, {len(filtered_jobs)} filtered"
        )

        return processable_jobs, filtered_jobs

    def get_language_stats(self, jobs: List[Dict]) -> Dict:
        """Get language distribution statistics for a list of jobs."""
        stats = {
            "total_jobs": len(jobs),
            "languages": {},
            "processable": 0,
            "filtered": 0,
            "filter_reasons": {},
        }

        for job in jobs:
            if "language_detection" in job:
                detection = job["language_detection"]

                # Count by detected language
                lang = detection["detected_language"]
                if lang not in stats["languages"]:
                    stats["languages"][lang] = 0
                stats["languages"][lang] += 1

                # Count processable vs filtered
                if detection["should_process"]:
                    stats["processable"] += 1
                else:
                    stats["filtered"] += 1

                    # Count filter reasons
                    reason = detection["reason"]
                    if reason not in stats["filter_reasons"]:
                        stats["filter_reasons"][reason] = 0
                    stats["filter_reasons"][reason] += 1

        return stats


# Example usage and testing
def test_language_detector():
    """Test the language detector with sample job data."""
    detector = JobLanguageDetector()

    # Test cases
    test_jobs = [
        {
            "title": "Software Engineer - Python Developer",
            "summary": "We are looking for a skilled Python developer to join our team.",
            "company": "TechCorp Inc.",
            "job_description": "Develop and maintain Python applications, work with databases, and collaborate with cross-functional teams.",
        },
        {
            "title": "Développeur Python - Poste à Montréal",
            "summary": "Nous recherchons un développeur Python expérimenté pour rejoindre notre équipe.",
            "company": "TechFrance SARL",
            "job_description": "Développer des applications Python, travailler avec des bases de données, et collaborer avec des équipes multidisciplinaires.",
        },
        {
            "title": "Data Analyst - Toronto",
            "summary": "Analyze data trends and create reports for business insights.",
            "company": "DataCorp",
            "job_description": "Use SQL, Python, and visualization tools to analyze business data and present findings to stakeholders.",
        },
    ]

    print("🔍 Language Detection Test Results:")
    print("=" * 50)

    for i, job in enumerate(test_jobs, 1):
        result = detector.detect_job_language(job)
        print(f"\nJob {i}: {job['title']}")
        print(f"  Language: {result['detected_language']} (confidence: {result['confidence']:.2f})")
        print(f"  Should Process: {result['should_process']}")
        print(f"  Reason: {result['reason']}")
        if result["languages"]:
            lang_list = [
                f"{lang['language']}: {lang['probability']:.2f}" for lang in result["languages"]
            ]
            print(f"  All Languages: {lang_list}")


# Main functionality moved to CLI module or tests
# Import and use the functions directly
