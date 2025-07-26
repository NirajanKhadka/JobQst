import json
from pathlib import Path
from typing import List, Dict, Optional
from agentic_doc.parse import parse
import re


def extract_keywords_from_text(text: str, top_n: int = 15) -> List[str]:
    # Simple keyword extraction: most frequent nouns/words (improve with NLP if needed)
    words = re.findall(r'\b\w{4,}\b', text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    # Remove common stopwords (expand as needed)
    stopwords = set([
        'with', 'from', 'that', 'this', 'have', 'will', 'your', 'about', 'which', 'their', 'other',
        'more', 'most', 'such', 'when', 'were', 'been', 'also', 'into', 'than', 'some', 'only',
        'over', 'very', 'like', 'just', 'make', 'time', 'work', 'team', 'role', 'able', 'good',
        'well', 'must', 'need', 'used', 'using', 'skills', 'experience', 'years', 'job', 'jobs',
        'cover', 'letter', 'resume', 'summary', 'objective', 'responsible', 'responsibilities',
        'requirements', 'required', 'preferred', 'excellent', 'strong', 'great', 'proven', 'ability',
        'knowledge', 'including', 'etc', 'etc.', 'etcetera', 'etc', 'etc.'
    ])
    filtered = [w for w in words if w not in stopwords]
    sorted_words = sorted(set(filtered), key=lambda w: -freq[w])
    return sorted_words[:top_n]


def get_keywords_for_profile(profile_path: str) -> List[str]:
    """
    Loads keywords from profile JSON. If missing/empty, extracts from resume/cover letter using agentic-doc,
    updates profile, and returns keywords.
    """
    profile_file = Path(profile_path)
    if not profile_file.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    with profile_file.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    keywords = profile.get("keywords", [])
    if keywords:
        return keywords
    # Try to get resume/cover letter text or file path
    resume_path = profile.get("resume_path")
    cover_letter_path = profile.get("cover_letter_path")
    resume_text = profile.get("resume_text")
    cover_letter_text = profile.get("cover_letter_text")
    extracted_texts = []
    # Prefer file paths if available
    for doc_path in [resume_path, cover_letter_path]:
        if doc_path and Path(doc_path).exists():
            results = parse(doc_path)
            if results and hasattr(results[0], 'markdown'):
                extracted_texts.append(results[0].markdown)
    # Fallback to embedded text
    for text in [resume_text, cover_letter_text]:
        if text:
            extracted_texts.append(text)
    if not extracted_texts:
        raise ValueError("No resume or cover letter found in profile for keyword extraction.")
    # Combine all extracted text
    combined_text = "\n".join(extracted_texts)
    keywords = extract_keywords_from_text(combined_text)
    # Save back to profile
    profile["keywords"] = keywords
    with profile_file.open("w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    return keywords
