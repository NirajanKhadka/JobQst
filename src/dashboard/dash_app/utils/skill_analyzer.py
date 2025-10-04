"""
Skill gap analysis utility for dashboard enhancements.
Provides rule-based skill extraction and gap analysis.
"""

from typing import Dict, List, Optional, Set, Tuple
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


# ============================================================================
# Skill Keywords and Patterns
# ============================================================================

# Common skill categories with their keyword patterns
SKILL_PATTERNS = {
    # Programming Languages
    "Python": [r"\bpython\b", r"\bpy\b"],
    "R": [r"\br\b", r"\br programming\b"],
    "SQL": [r"\bsql\b", r"\bt-sql\b", r"\bpl/sql\b", r"\bmysql\b", r"\bpostgresql\b"],
    "Java": [r"\bjava\b", r"\bjava programming\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b", r"\bnode\.?js\b"],
    "C++": [r"\bc\+\+\b", r"\bcpp\b"],
    "C#": [r"\bc#\b", r"\bc sharp\b"],
    "Scala": [r"\bscala\b"],
    "Julia": [r"\bjulia\b"],
    
    # Data Science & ML
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b", r"\bml models\b"],
    "Deep Learning": [r"\bdeep learning\b", r"\bneural networks?\b", r"\bdl\b"],
    "Natural Language Processing": [r"\bnlp\b", r"\bnatural language processing\b", r"\btext analytics\b"],
    "Computer Vision": [r"\bcomputer vision\b", r"\bimage processing\b", r"\bcv\b"],
    "Statistical Analysis": [r"\bstatistical analysis\b", r"\bstatistics\b", r"\bstats\b"],
    "Data Mining": [r"\bdata mining\b", r"\bpattern recognition\b"],
    "Predictive Modeling": [r"\bpredictive modeling\b", r"\bforecasting\b"],
    
    # Data Tools & Frameworks
    "TensorFlow": [r"\btensorflow\b", r"\btf\b"],
    "PyTorch": [r"\bpytorch\b", r"\btorch\b"],
    "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Spark": [r"\bspark\b", r"\bapache spark\b", r"\bpyspark\b"],
    "Hadoop": [r"\bhadoop\b", r"\bhdfs\b"],
    "Kafka": [r"\bkafka\b", r"\bapache kafka\b"],
    
    # Visualization
    "Tableau": [r"\btableau\b"],
    "Power BI": [r"\bpower ?bi\b", r"\bpowerbi\b"],
    "Matplotlib": [r"\bmatplotlib\b"],
    "Seaborn": [r"\bseaborn\b"],
    "D3.js": [r"\bd3\.?js\b", r"\bd3\b"],
    "Plotly": [r"\bplotly\b"],
    
    # Cloud & Big Data
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b", r"\bmicrosoft azure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Docker": [r"\bdocker\b", r"\bcontainerization\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    
    # Databases
    "MongoDB": [r"\bmongodb\b", r"\bmongo\b"],
    "PostgreSQL": [r"\bpostgresql\b", r"\bpostgres\b"],
    "MySQL": [r"\bmysql\b"],
    "Oracle": [r"\boracle\b", r"\boracle db\b"],
    "Redis": [r"\bredis\b"],
    "Cassandra": [r"\bcassandra\b"],
    
    # Business Intelligence
    "ETL": [r"\betl\b", r"\bextract transform load\b"],
    "Data Warehousing": [r"\bdata warehous\w+\b", r"\bdwh\b"],
    "Business Intelligence": [r"\bbusiness intelligence\b", r"\bbi\b"],
    "Data Analytics": [r"\bdata analytics\b", r"\banalytics\b"],
    "Data Visualization": [r"\bdata visualization\b", r"\bdata viz\b"],
    
    # Soft Skills
    "Communication": [r"\bcommunication\b", r"\bverbal\b", r"\bwritten\b"],
    "Problem Solving": [r"\bproblem solving\b", r"\banalytical thinking\b"],
    "Teamwork": [r"\bteamwork\b", r"\bcollaboration\b", r"\bteam player\b"],
    "Leadership": [r"\bleadership\b", r"\bleading teams\b"],
    "Project Management": [r"\bproject management\b", r"\bagile\b", r"\bscrum\b"],
    
    # Other Technical Skills
    "Git": [r"\bgit\b", r"\bgithub\b", r"\bgitlab\b", r"\bversion control\b"],
    "API": [r"\bapi\b", r"\brest\b", r"\brestful\b"],
    "Microservices": [r"\bmicroservices\b"],
    "CI/CD": [r"\bci/cd\b", r"\bcontinuous integration\b"],
}


# ============================================================================
# Skill Extraction Functions
# ============================================================================

def extract_skills_from_text(text: str, skill_patterns: Dict[str, List[str]] = None) -> Set[str]:
    """
    Extract skills from text using pattern matching.
    
    Args:
        text: Text to extract skills from
        skill_patterns: Optional custom skill patterns (uses default if None)
    
    Returns:
        Set of detected skill names
    """
    if not text:
        return set()
    
    if skill_patterns is None:
        skill_patterns = SKILL_PATTERNS
    
    text_lower = text.lower()
    detected_skills = set()
    
    for skill_name, patterns in skill_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                detected_skills.add(skill_name)
                break  # Found this skill, move to next
    
    return detected_skills


def extract_skills_from_jobs(jobs: List[Dict]) -> Dict[str, int]:
    """
    Extract skills from a list of job postings.
    
    Args:
        jobs: List of job dictionaries with 'description' field
    
    Returns:
        Dictionary mapping skill name to count of jobs mentioning it
    """
    skill_counter = Counter()
    
    for job in jobs:
        description = job.get("description", "") or ""
        title = job.get("title", "") or ""
        
        # Combine title and description for better detection
        combined_text = f"{title} {description}"
        
        detected_skills = extract_skills_from_text(combined_text)
        skill_counter.update(detected_skills)
    
    return dict(skill_counter)


def normalize_user_skills(user_skills: List[str]) -> Set[str]:
    """
    Normalize user skills to match skill pattern keys.
    
    Args:
        user_skills: List of user skill strings
    
    Returns:
        Set of normalized skill names
    """
    if not user_skills:
        return set()
    
    normalized = set()
    
    for user_skill in user_skills:
        user_skill_lower = user_skill.lower().strip()
        
        # Try to match against known skill patterns
        for skill_name, patterns in SKILL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_skill_lower, re.IGNORECASE):
                    normalized.add(skill_name)
                    break
        
        # If no match found, add as-is (capitalized)
        if not any(re.search(p, user_skill_lower, re.IGNORECASE) 
                  for patterns in SKILL_PATTERNS.values() 
                  for p in patterns):
            normalized.add(user_skill.strip().title())
    
    return normalized


# ============================================================================
# Skill Gap Analysis Functions
# ============================================================================

def analyze_skill_gaps(
    user_skills: List[str],
    jobs: List[Dict],
    min_frequency: int = 3,
    top_n: int = 10
) -> List[Dict]:
    """
    Analyze skill gaps between user skills and job requirements.
    
    Args:
        user_skills: List of user's current skills
        jobs: List of job dictionaries
        min_frequency: Minimum number of jobs mentioning a skill to include it
        top_n: Maximum number of skill gaps to return
    
    Returns:
        List of skill gap dictionaries with:
            - skill: str (skill name)
            - percentage: float (% of jobs requiring this skill)
            - jobs_count: int (number of jobs)
            - priority: str (high/medium/low)
            - rule_explanation: str (how it was detected)
            - example_keywords: List[str] (keywords that matched)
    """
    try:
        if not jobs:
            logger.warning("No jobs provided for skill gap analysis")
            return []
        
        # Normalize user skills
        user_skills_normalized = normalize_user_skills(user_skills)
        logger.info(f"Normalized user skills: {user_skills_normalized}")
        
        # Extract skills from all jobs
        job_skills = extract_skills_from_jobs(jobs)
        total_jobs = len(jobs)
        
        # Find skill gaps (skills in jobs but not in user profile)
        skill_gaps = []
        
        for skill, count in job_skills.items():
            # Skip if user already has this skill
            if skill in user_skills_normalized:
                continue
            
            # Skip if below minimum frequency
            if count < min_frequency:
                continue
            
            # Calculate percentage
            percentage = (count / total_jobs) * 100
            
            # Determine priority
            if percentage >= 70:
                priority = "high"
            elif percentage >= 40:
                priority = "medium"
            else:
                priority = "low"
            
            # Get example keywords for this skill
            example_keywords = SKILL_PATTERNS.get(skill, [skill.lower()])
            example_keywords = [kw.replace(r"\b", "").replace("\\", "") 
                              for kw in example_keywords[:3]]
            
            # Create rule explanation
            rule_explanation = (
                f"Found in {count} out of {total_jobs} jobs "
                f"({percentage:.0f}%) using keyword matching"
            )
            
            skill_gaps.append({
                "skill": skill,
                "percentage": round(percentage, 1),
                "jobs_count": count,
                "priority": priority,
                "rule_explanation": rule_explanation,
                "example_keywords": example_keywords
            })
        
        # Sort by percentage (descending) and return top N
        skill_gaps.sort(key=lambda x: x["percentage"], reverse=True)
        
        logger.info(f"Found {len(skill_gaps)} skill gaps, returning top {top_n}")
        return skill_gaps[:top_n]
    
    except Exception as e:
        logger.error(f"Error in skill gap analysis: {e}", exc_info=True)
        return []


def get_skill_categories(skills: List[str]) -> Dict[str, List[str]]:
    """
    Categorize skills into groups.
    
    Args:
        skills: List of skill names
    
    Returns:
        Dictionary mapping category to list of skills
    """
    categories = {
        "Programming Languages": [],
        "Data Science & ML": [],
        "Data Tools": [],
        "Cloud & Infrastructure": [],
        "Databases": [],
        "Business Intelligence": [],
        "Soft Skills": [],
        "Other": []
    }
    
    # Define category keywords
    category_keywords = {
        "Programming Languages": ["python", "java", "javascript", "c++", "c#", "r", "scala"],
        "Data Science & ML": ["machine learning", "deep learning", "nlp", "computer vision", 
                             "statistical", "predictive"],
        "Data Tools": ["tensorflow", "pytorch", "pandas", "numpy", "spark", "hadoop"],
        "Cloud & Infrastructure": ["aws", "azure", "gcp", "docker", "kubernetes"],
        "Databases": ["sql", "mongodb", "postgresql", "mysql", "oracle", "redis"],
        "Business Intelligence": ["tableau", "power bi", "etl", "data warehousing", 
                                 "business intelligence"],
        "Soft Skills": ["communication", "problem solving", "teamwork", "leadership", 
                       "project management"]
    }
    
    for skill in skills:
        skill_lower = skill.lower()
        categorized = False
        
        for category, keywords in category_keywords.items():
            if any(keyword in skill_lower for keyword in keywords):
                categories[category].append(skill)
                categorized = True
                break
        
        if not categorized:
            categories["Other"].append(skill)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def calculate_skill_coverage(user_skills: List[str], job_skills: List[str]) -> float:
    """
    Calculate what percentage of job skills the user has.
    
    Args:
        user_skills: List of user's skills
        job_skills: List of required job skills
    
    Returns:
        Coverage percentage (0-100)
    """
    if not job_skills:
        return 100.0
    
    user_skills_normalized = normalize_user_skills(user_skills)
    job_skills_normalized = normalize_user_skills(job_skills)
    
    if not job_skills_normalized:
        return 100.0
    
    matched_skills = user_skills_normalized.intersection(job_skills_normalized)
    coverage = (len(matched_skills) / len(job_skills_normalized)) * 100
    
    return round(coverage, 1)


def get_missing_critical_skills(
    user_skills: List[str],
    jobs: List[Dict],
    critical_threshold: float = 50.0
) -> List[str]:
    """
    Get list of critical missing skills (mentioned in >50% of jobs).
    
    Args:
        user_skills: List of user's skills
        jobs: List of job dictionaries
        critical_threshold: Percentage threshold for critical skills
    
    Returns:
        List of critical missing skill names
    """
    skill_gaps = analyze_skill_gaps(user_skills, jobs, min_frequency=1, top_n=100)
    
    critical_skills = [
        gap["skill"] 
        for gap in skill_gaps 
        if gap["percentage"] >= critical_threshold
    ]
    
    return critical_skills


def get_skill_recommendations(
    user_skills: List[str],
    jobs: List[Dict],
    top_n: int = 5
) -> List[Dict]:
    """
    Get skill learning recommendations based on job market demand.
    
    Args:
        user_skills: List of user's skills
        jobs: List of job dictionaries
        top_n: Number of recommendations to return
    
    Returns:
        List of recommendation dictionaries with:
            - skill: str
            - reason: str
            - priority: str
            - learning_resources: List[str]
    """
    skill_gaps = analyze_skill_gaps(user_skills, jobs, min_frequency=2, top_n=top_n)
    
    recommendations = []
    
    for gap in skill_gaps:
        # Generate learning resource suggestions (placeholder)
        learning_resources = [
            f"Online courses for {gap['skill']}",
            f"Practice projects using {gap['skill']}",
            f"Certifications in {gap['skill']}"
        ]
        
        reason = (
            f"High demand skill - mentioned in {gap['percentage']:.0f}% of target jobs. "
            f"Learning this skill could significantly improve your job match scores."
        )
        
        recommendations.append({
            "skill": gap["skill"],
            "reason": reason,
            "priority": gap["priority"],
            "learning_resources": learning_resources,
            "jobs_count": gap["jobs_count"]
        })
    
    return recommendations
