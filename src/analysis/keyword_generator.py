from typing import List, Dict

def get_intelligent_keywords(profile: Dict) -> List[str]:
    """Generates intelligent keywords based on a user's profile."""
    keywords = profile.get('keywords', [])
    skills = profile.get('skills', [])
    
    intelligent_keywords = keywords.copy()
    skill_lower = [s.lower() for s in skills]

    if 'python' in skill_lower:
        intelligent_keywords.extend(['Python Developer', 'Python Data Analyst'])
    if 'sql' in skill_lower:
        intelligent_keywords.extend(['SQL Analyst', 'SQL Developer'])
    
    data_skills = ['pandas', 'numpy', 'excel', 'tableau', 'power bi']
    if any(skill.lower() in skill_lower for skill in data_skills):
        intelligent_keywords.extend(['Junior Data Analyst', 'Business Intelligence Analyst'])
        
    seen = set()
    unique_keywords = []
    for keyword in intelligent_keywords:
        if keyword.lower() not in seen:
            seen.add(keyword.lower())
            unique_keywords.append(keyword)
            
    return unique_keywords[:12]