from typing import List, Dict


def get_Automated_keywords(profile: Dict) -> List[str]:
    """Generates Automated keywords based on a user's profile."""
    keywords = profile.get("keywords", [])
    skills = profile.get("skills", [])

    Automated_keywords = keywords.copy()
    skill_lower = [s.lower() for s in skills]

    if "python" in skill_lower:
        Automated_keywords.extend(["Python Developer", "Python Data Analyst"])
    if "sql" in skill_lower:
        Automated_keywords.extend(["SQL Analyst", "SQL Developer"])

    data_skills = ["pandas", "numpy", "excel", "tableau", "power bi"]
    if any(skill.lower() in skill_lower for skill in data_skills):
        Automated_keywords.extend(["Junior Data Analyst", "Business Intelligence Analyst"])

    seen = set()
    unique_keywords = []
    for keyword in Automated_keywords:
        if keyword.lower() not in seen:
            seen.add(keyword.lower())
            unique_keywords.append(keyword)

    return unique_keywords[:12]

