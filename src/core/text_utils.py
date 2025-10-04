"""
Text processing utilities for job data analysis and manipulation.
"""

import re
import string
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TextAnalysisResult:
    """Result of text analysis operations."""

    word_count: int
    char_count: int
    sentence_count: int
    paragraph_count: int
    keywords: List[str]
    sentiment_score: float


def clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace and special characters."""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Remove special characters but keep basic punctuation
    text = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)]", "", text)

    return text


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """Extract keywords from text based on frequency and relevance."""
    if not text:
        return []

    # Clean text
    text = clean_text(text.lower())

    # Remove common stop words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
    }

    # Split into words and filter
    words = re.findall(r"\b\w+\b", text)
    words = [word for word in words if len(word) >= min_length and word not in stop_words]

    # Count frequency
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def analyze_text(text: str) -> TextAnalysisResult:
    """Perform comprehensive text analysis."""
    if not text:
        return TextAnalysisResult(0, 0, 0, 0, [], 0.0)

    # Basic counts
    word_count = len(text.split())
    char_count = len(text)
    sentence_count = len(re.findall(r"[.!?]+", text))
    paragraph_count = len([p for p in text.split("\n\n") if p.strip()])

    # Extract keywords
    keywords = extract_keywords(text)

    # Simple sentiment analysis (basic implementation)
    positive_words = {
        "good",
        "great",
        "excellent",
        "amazing",
        "wonderful",
        "fantastic",
        "best",
        "love",
        "like",
    }
    negative_words = {"bad", "terrible", "awful", "worst", "hate", "dislike", "poor", "horrible"}

    words = text.lower().split()
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)

    total_words = len(words)
    if total_words > 0:
        sentiment_score = (positive_count - negative_count) / total_words
    else:
        sentiment_score = 0.0

    return TextAnalysisResult(
        word_count=word_count,
        char_count=char_count,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        keywords=keywords,
        sentiment_score=sentiment_score,
    )


def normalize_job_title(title: str) -> str:
    """Normalize job title for consistent comparison."""
    if not title:
        return ""

    # Convert to lowercase
    title = title.lower()

    # Remove common prefixes/suffixes
    title = re.sub(r"^(senior|junior|lead|principal|staff|associate)\s+", "", title)
    title = re.sub(r"\s+(i|ii|iii|iv|v|sr|jr)$", "", title)

    # Remove special characters
    title = re.sub(r"[^\w\s]", "", title)

    # Normalize whitespace
    title = re.sub(r"\s+", " ", title).strip()

    return title


def extract_skills_from_text(text: str) -> List[str]:
    """Extract potential skills from text content."""
    if not text:
        return []

    # Common programming languages and technologies
    skills_patterns = [
        r"\b(python|java|javascript|typescript|react|angular|vue|node\.js|express|django|flask|fastapi)\b",
        r"\b(sql|mysql|postgresql|mongodb|redis|elasticsearch)\b",
        r"\b(aws|azure|gcp|docker|kubernetes|jenkins|git|github|gitlab)\b",
        r"\b(html|css|bootstrap|tailwind|sass|less|webpack|babel)\b",
        r"\b(machine learning|ai|artificial intelligence|data science|analytics)\b",
        r"\b(agile|scrum|kanban|waterfall|devops|ci/cd)\b",
    ]

    skills = set()
    text_lower = text.lower()

    for pattern in skills_patterns:
        matches = re.findall(pattern, text_lower)
        skills.update(matches)

    return list(skills)


def format_text_for_display(text: str, max_length: int = 200) -> str:
    """Format text for display with proper truncation."""
    if not text:
        return ""

    # Clean text
    text = clean_text(text)

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."

    return text


def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from text."""
    contact_info = {}

    # Email pattern
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info["email"] = emails[0]

    # Phone pattern
    phone_pattern = r"(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})"
    phones = re.findall(phone_pattern, text)
    if phones:
        contact_info["phone"] = "".join(phones[0])

    return contact_info
