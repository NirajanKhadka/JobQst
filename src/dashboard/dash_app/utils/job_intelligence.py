"""
Job Intelligence Extractor
Extract top keywords, generate AI summaries, and analyze skill gaps from job descriptions
"""

import re
from collections import Counter
from typing import List, Dict, Tuple
import pandas as pd


class JobIntelligenceExtractor:
    """Extract actionable intelligence from job descriptions for job seekers"""
    
    # Common words to filter out
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'job',
        'work', 'position', 'role', 'opportunity', 'team', 'company', 'looking'
    }
    
    # Tech/Business keywords to prioritize
    PRIORITY_KEYWORDS = {
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
        'sql', 'nosql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
        'django', 'flask', 'fastapi', 'spring', 'express', 'laravel',
        'agile', 'scrum', 'ci/cd', 'devops', 'microservices', 'api', 'rest',
        'git', 'github', 'gitlab', 'jira', 'confluence', 'linux', 'bash',
        'leadership', 'management', 'communication', 'problem solving',
        'bachelor', 'master', 'phd', 'certification', 'degree'
    }
    
    def extract_top_keywords(
        self, 
        description: str, 
        title: str = "",
        top_n: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Extract top N keywords from job description
        
        Args:
            description: Full job description text
            title: Job title (optional, gets extra weight)
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, frequency) tuples
        """
        if not description:
            return []
        
        # Combine title and description (title words get extra weight)
        text = f"{title} {title} {title} {description}".lower()
        
        # Extract words (including multi-word tech terms)
        words = re.findall(r'\b[a-z][a-z+#\.]{1,}\b', text)
        
        # Filter stop words and short words
        words = [
            w for w in words 
            if w not in self.STOP_WORDS and len(w) > 2
        ]
        
        # Count frequencies
        word_counts = Counter(words)
        
        # Boost priority keywords
        for word, count in word_counts.items():
            if word in self.PRIORITY_KEYWORDS:
                word_counts[word] = count * 2
        
        # Get top N
        return word_counts.most_common(top_n)
    
    def generate_ai_summary(
        self, 
        description: str, 
        title: str = "",
        company: str = ""
    ) -> str:
        """
        Generate a quick "What They're Looking For" summary
        
        Args:
            description: Full job description
            title: Job title
            company: Company name
            
        Returns:
            2-3 sentence summary of key requirements
        """
        if not description:
            return "No description available"
        
        # This is a simple rule-based summary
        # In production, you'd use an LLM or fine-tuned model
        
        summary_parts = []
        desc_lower = description.lower()
        
        # Extract experience level
        exp_match = re.search(r'(\d+)\+?\s*years?', desc_lower)
        if exp_match:
            years = exp_match.group(1)
            summary_parts.append(f"Seeking {years}+ years experience")
        else:
            if any(word in desc_lower for word in ['junior', 'entry', 'graduate']):
                summary_parts.append("Entry-level position")
            elif any(word in desc_lower for word in ['senior', 'lead', 'principal']):
                summary_parts.append("Senior-level position")
            else:
                summary_parts.append("Mid-level position")
        
        # Extract key skills (top 3)
        keywords = self.extract_top_keywords(description, title, top_n=5)
        if keywords:
            top_skills = [kw[0] for kw in keywords[:3]]
            if any(skill in self.PRIORITY_KEYWORDS for skill, _ in keywords[:5]):
                tech_skills = [
                    kw[0] for kw in keywords[:5] 
                    if kw[0] in self.PRIORITY_KEYWORDS
                ][:3]
                if tech_skills:
                    summary_parts.append(
                        f"Must have: {', '.join(tech_skills)}"
                    )
        
        # Extract work arrangement
        if 'remote' in desc_lower:
            summary_parts.append("Remote work available")
        elif 'hybrid' in desc_lower:
            summary_parts.append("Hybrid work model")
        else:
            summary_parts.append("On-site position")
        
        # Combine into summary
        if summary_parts:
            return ". ".join(summary_parts) + "."
        
        return f"{title} role at {company}"
    
    def analyze_skill_gap(
        self,
        job_skills: List[str],
        user_skills: List[str]
    ) -> Dict[str, any]:
        """
        Analyze skill gap between job requirements and user skills
        
        Args:
            job_skills: List of skills required by job
            user_skills: List of skills user has
            
        Returns:
            Dict with match analysis:
            - matched_skills: List of matching skills
            - missing_skills: List of missing skills
            - match_percentage: Percentage of skills matched
            - match_level: 'Excellent', 'Good', 'Fair', or 'Poor'
        """
        if not job_skills:
            return {
                "matched_skills": [],
                "missing_skills": [],
                "match_percentage": 0,
                "match_level": "Unknown"
            }
        
        # Normalize skills to lowercase
        job_skills_set = {skill.lower().strip() for skill in job_skills if skill}
        user_skills_set = {skill.lower().strip() for skill in user_skills if skill}
        
        # Find matches and gaps
        matched = job_skills_set & user_skills_set
        missing = job_skills_set - user_skills_set
        
        # Calculate percentage
        match_pct = (len(matched) / len(job_skills_set)) * 100 if job_skills_set else 0
        
        # Determine match level
        if match_pct >= 80:
            level = "Excellent"
        elif match_pct >= 60:
            level = "Good"
        elif match_pct >= 40:
            level = "Fair"
        else:
            level = "Poor"
        
        return {
            "matched_skills": sorted(list(matched)),
            "missing_skills": sorted(list(missing)),
            "match_percentage": round(match_pct, 1),
            "match_level": level,
            "total_required": len(job_skills_set),
            "total_matched": len(matched)
        }
    
    def extract_salary_intelligence(
        self,
        salary_str: str,
        location: str = ""
    ) -> Dict[str, any]:
        """
        Extract and analyze salary information
        
        Args:
            salary_str: Salary range string (e.g., "$80k-$120k")
            location: Job location for market comparison
            
        Returns:
            Dict with salary analysis
        """
        if not salary_str:
            return {
                "min": None,
                "max": None,
                "midpoint": None,
                "market_comparison": "Unknown"
            }
        
        # Extract numbers from salary string
        numbers = re.findall(r'[\d,]+', salary_str)
        if not numbers:
            return {
                "min": None,
                "max": None,
                "midpoint": None,
                "market_comparison": "Unknown"
            }
        
        # Parse salary values
        salaries = [int(n.replace(',', '')) for n in numbers]
        
        # Handle single value or range
        if len(salaries) == 1:
            midpoint = salaries[0]
            salary_min = salary_max = salaries[0]
        else:
            salary_min = min(salaries)
            salary_max = max(salaries)
            midpoint = (salary_min + salary_max) / 2
        
        # Simple market comparison (could be enhanced with real data)
        market_comparison = "Average"
        if midpoint > 100000:
            market_comparison = "Above Average"
        elif midpoint < 50000:
            market_comparison = "Below Average"
        
        return {
            "min": salary_min,
            "max": salary_max,
            "midpoint": midpoint,
            "market_comparison": market_comparison
        }


def find_similar_jobs(
    current_job: Dict,
    all_jobs: List[Dict],
    top_n: int = 3
) -> List[Dict]:
    """
    Find similar jobs based on keywords, location, and salary
    
    Args:
        current_job: The current job being viewed
        all_jobs: List of all available jobs
        top_n: Number of similar jobs to return
        
    Returns:
        List of similar job dictionaries
    """
    if not all_jobs:
        return []
    
    current_id = current_job.get("id")
    current_keywords = set(current_job.get("top_keywords", []))
    current_location = current_job.get("location", "").lower()
    current_salary_mid = current_job.get("salary_intelligence", {}).get("midpoint", 0)
    
    # Score each job for similarity
    scored_jobs = []
    for job in all_jobs:
        # Skip the current job
        if job.get("id") == current_id:
            continue
        
        score = 0
        
        # Keyword overlap (most important)
        job_keywords = set(job.get("top_keywords", []))
        keyword_overlap = len(current_keywords & job_keywords)
        score += keyword_overlap * 10
        
        # Same location/city
        if current_location and current_location in job.get("location", "").lower():
            score += 15
        
        # Similar salary range (within 20%)
        job_salary_mid = job.get("salary_intelligence", {}).get("midpoint", 0)
        if current_salary_mid and job_salary_mid:
            salary_diff = abs(current_salary_mid - job_salary_mid) / current_salary_mid
            if salary_diff < 0.2:  # Within 20%
                score += 10
            elif salary_diff < 0.4:  # Within 40%
                score += 5
        
        # Higher match score bonus
        if job.get("fit_score", 0) > current_job.get("fit_score", 0):
            score += 8
        
        # RCIP cities bonus
        if job.get("is_rcip_city"):
            score += 5
        
        scored_jobs.append((score, job))
    
    # Sort by score and return top N
    scored_jobs.sort(reverse=True, key=lambda x: x[0])
    return [job for score, job in scored_jobs[:top_n]]


def enhance_job_with_intelligence(job: Dict, user_profile: Dict = None) -> Dict:
    """
    Enhance a job dictionary with intelligence features
    
    Args:
        job: Job dictionary from database
        user_profile: Optional user profile for skill matching
        
    Returns:
        Enhanced job dictionary with AI summary, keywords, skill gaps
    """
    extractor = JobIntelligenceExtractor()
    
    # Extract keywords
    keywords = extractor.extract_top_keywords(
        job.get("description", ""),
        job.get("title", ""),
        top_n=8
    )
    job["top_keywords"] = [kw[0] for kw in keywords]
    job["keyword_frequencies"] = dict(keywords)
    
    # Generate AI summary
    job["ai_summary"] = extractor.generate_ai_summary(
        job.get("description", ""),
        job.get("title", ""),
        job.get("company", "")
    )
    
    # Skill gap analysis (if user profile provided)
    if user_profile and user_profile.get("skills"):
        job_skills = job.get("skills", "").split(",") if job.get("skills") else []
        skill_analysis = extractor.analyze_skill_gap(
            job_skills,
            user_profile.get("skills", [])
        )
        job["skill_gap_analysis"] = skill_analysis
    
    # Salary intelligence
    if job.get("salary_range"):
        salary_info = extractor.extract_salary_intelligence(
            job.get("salary_range", ""),
            job.get("location", "")
        )
        job["salary_intelligence"] = salary_info
    
    return job
