#!/usr/bin/env python3
"""
Llama3-Based Job Similarity Analyzer
Advanced AI-powered job matching using Llama3 with sophisticated prompting
"""

import json
import re
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class JobAnalysisResult:
    """Structured result from Llama3 job analysis"""
    compatibility_score: float  # 0.0 to 1.0
    skill_matches: List[str]
    skill_gaps: List[str]
    experience_match: str  # "perfect", "close", "mismatch"
    location_match: str    # "perfect", "nearby", "remote_ok", "mismatch"
    salary_assessment: str # "below", "fair", "above", "unknown"
    cultural_fit: float   # 0.0 to 1.0
    growth_potential: float # 0.0 to 1.0
    recommendation: str   # "highly_recommend", "recommend", "consider", "skip"
    reasoning: str        # Detailed explanation
    confidence: float     # 0.0 to 1.0 - how confident the AI is

class LlamaJobAnalyzer:
    """Advanced job analysis using Llama3 with sophisticated prompting"""
    
    def __init__(self, llama_endpoint: str = "http://localhost:11434", model: str = "llama3:latest"):
        """
        Initialize Llama3 analyzer
        
        Args:
            llama_endpoint: Ollama endpoint URL
            model: Model name (llama3, llama3:70b, etc.)
        """
        self.endpoint = llama_endpoint
        self.model = model
        self.session = requests.Session()
        
    def _create_analysis_prompt(self, profile: Dict, job: Dict) -> str:
        """Create sophisticated analysis prompt for Llama3"""
        
        prompt = f"""You are an expert career counselor and AI recruiter with 20+ years of experience in job matching and career development. Analyze how well this job matches the candidate's profile.

**CANDIDATE PROFILE:**
Name: {profile.get('name', 'Unknown')}
Location: {profile.get('location', 'Unknown')}
Experience Level: {profile.get('experience_level', 'Unknown')}

Skills: {', '.join(profile.get('skills', []))}
Keywords: {', '.join(profile.get('keywords', []))}
Preferred Industries: {', '.join(profile.get('industries', ['Any']))}
Work Preferences: {profile.get('work_preferences', {})}

**JOB POSTING:**
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Experience Level: {job.get('experience_level', 'Unknown')}

Summary: {job.get('summary', 'No summary provided')}
Description: {job.get('description', job.get('summary', 'No description provided'))}

Requirements: {job.get('requirements', 'See description')}
Salary Range: {job.get('salary_range', 'Not specified')}

**ANALYSIS INSTRUCTIONS:**
Provide a comprehensive analysis as a JSON object with these exact fields:

1. **compatibility_score** (0.0-1.0): Overall match score
   - 0.9-1.0: Perfect match, should definitely apply
   - 0.7-0.8: Strong match, high chance of success
   - 0.5-0.6: Good match, worth applying
   - 0.3-0.4: Weak match, consider carefully
   - 0.0-0.2: Poor match, probably skip

2. **skill_matches** (array): List of candidate skills that match job requirements

3. **skill_gaps** (array): Important job requirements the candidate lacks

4. **experience_match** (string): "perfect", "close", "stretch", "mismatch"

5. **location_match** (string): "perfect", "nearby", "remote_ok", "relocate_needed", "mismatch"

6. **salary_assessment** (string): "below", "fair", "above", "unknown"

7. **cultural_fit** (0.0-1.0): How well the candidate would fit the company culture

8. **growth_potential** (0.0-1.0): Career growth opportunities this job offers

9. **recommendation** (string): "highly_recommend", "recommend", "consider", "skip"

10. **reasoning** (string): 2-3 sentence explanation of the analysis

11. **confidence** (0.0-1.0): How confident you are in this analysis

**SCORING CRITERIA:**
- Skill alignment: 40% weight
- Experience level match: 25% weight  
- Location compatibility: 15% weight
- Cultural/industry fit: 10% weight
- Growth potential: 10% weight

**IMPORTANT CONSIDERATIONS:**
- Consider synonyms and related skills (e.g., "Power BI" = "Business Intelligence", "Python" includes "pandas", "numpy")
- Entry level candidates can grow into roles requiring slightly more experience
- Remote work options increase location compatibility
- Company reputation and growth opportunities matter
- Industry transitions are possible with transferable skills

Respond ONLY with valid JSON, no additional text:"""

        return prompt
    
    def _call_llama(self, prompt: str) -> Optional[str]:
        """Call Llama3 API with the analysis prompt"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1000,  # Allow longer responses
                }
            }
            
            response = self.session.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Llama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Llama API: {e}")
            return None
    
    def _parse_llama_response(self, response: str) -> Optional[JobAnalysisResult]:
        """Parse Llama3 JSON response into structured result"""
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in Llama response")
                return None
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                'compatibility_score', 'skill_matches', 'skill_gaps',
                'experience_match', 'location_match', 'salary_assessment',
                'cultural_fit', 'growth_potential', 'recommendation',
                'reasoning', 'confidence'
            ]
            
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            return JobAnalysisResult(
                compatibility_score=float(data['compatibility_score']),
                skill_matches=data['skill_matches'],
                skill_gaps=data['skill_gaps'],
                experience_match=data['experience_match'],
                location_match=data['location_match'],
                salary_assessment=data['salary_assessment'],
                cultural_fit=float(data['cultural_fit']),
                growth_potential=float(data['growth_potential']),
                recommendation=data['recommendation'],
                reasoning=data['reasoning'],
                confidence=float(data['confidence'])
            )
            
        except Exception as e:
            logger.error(f"Error parsing Llama response: {e}")
            logger.error(f"Response: {response}")
            return None
    
    def analyze_job(self, profile: Dict, job: Dict) -> Optional[JobAnalysisResult]:
        """
        Analyze job compatibility using Llama3
        
        Args:
            profile: User profile dict
            job: Job posting dict
            
        Returns:
            JobAnalysisResult or None if analysis failed
        """
        try:
            # Create sophisticated prompt
            prompt = self._create_analysis_prompt(profile, job)
            
            # Call Llama3
            response = self._call_llama(prompt)
            if not response:
                return None
            
            # Parse response
            result = self._parse_llama_response(response)
            return result
            
        except Exception as e:
            logger.error(f"Error in job analysis: {e}")
            return None
    
    def batch_analyze_jobs(self, profile: Dict, jobs: List[Dict]) -> List[Tuple[Dict, Optional[JobAnalysisResult]]]:
        """
        Analyze multiple jobs in batch
        
        Args:
            profile: User profile dict
            jobs: List of job dicts
            
        Returns:
            List of (job, analysis_result) tuples
        """
        results = []
        
        for job in jobs:
            logger.info(f"Analyzing job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            analysis = self.analyze_job(profile, job)
            results.append((job, analysis))
        
        return results
    
    def get_top_matches(self, profile: Dict, jobs: List[Dict], top_n: int = 10) -> List[Tuple[Dict, JobAnalysisResult]]:
        """
        Get top N job matches sorted by compatibility score
        
        Args:
            profile: User profile dict
            jobs: List of job dicts
            top_n: Number of top matches to return
            
        Returns:
            List of (job, analysis_result) tuples sorted by score
        """
        # Analyze all jobs
        results = self.batch_analyze_jobs(profile, jobs)
        
        # Filter successful analyses and sort by score
        valid_results = [(job, analysis) for job, analysis in results if analysis is not None]
        sorted_results = sorted(valid_results, key=lambda x: x[1].compatibility_score, reverse=True)
        
        return sorted_results[:top_n]
    
    def create_match_report(self, profile: Dict, job: Dict, analysis: JobAnalysisResult) -> str:
        """Create a detailed match report for a job"""
        
        score_emoji = "🎯" if analysis.compatibility_score >= 0.8 else "✅" if analysis.compatibility_score >= 0.6 else "⚠️" if analysis.compatibility_score >= 0.4 else "❌"
        
        report = f"""
{score_emoji} **JOB MATCH ANALYSIS**

**Job:** {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}
**Overall Compatibility:** {analysis.compatibility_score:.1%} ({analysis.recommendation.replace('_', ' ').title()})
**AI Confidence:** {analysis.confidence:.1%}

**✅ Matching Skills:**
{', '.join(analysis.skill_matches) if analysis.skill_matches else 'None identified'}

**📈 Skill Gaps:**
{', '.join(analysis.skill_gaps) if analysis.skill_gaps else 'None identified'}

**📍 Location:** {analysis.location_match.replace('_', ' ').title()}
**🎯 Experience:** {analysis.experience_match.title()} match
**💰 Salary:** {analysis.salary_assessment.title()} range
**🏢 Cultural Fit:** {analysis.cultural_fit:.1%}
**📈 Growth Potential:** {analysis.growth_potential:.1%}

**💡 AI Reasoning:**
{analysis.reasoning}
"""
        return report

def test_llama_analyzer():
    """Test the Llama3 job analyzer"""
    
    # Test profile
    profile = {
        'name': 'Nirajan Khadka',
        'location': 'Mississauga, ON',
        'experience_level': 'Entry Level',
        'skills': ['Python', 'Pandas', 'NumPy', 'Scikit-learn', 'Power BI', 'SQL', 'Machine Learning'],
        'keywords': ['Data Analyst', 'Power BI', 'SQL', 'Python', 'Data Science', 'Machine Learning'],
        'industries': ['Technology', 'Finance', 'Healthcare'],
        'work_preferences': {'remote': True, 'hybrid': True}
    }
    
    # Test job
    job = {
        'title': 'Data Analyst',
        'company': 'Microsoft',
        'location': 'Toronto, ON',
        'experience_level': 'Entry Level',
        'summary': 'Looking for a Data Analyst with Python, SQL, Power BI, and machine learning experience.',
        'description': 'We need someone with Python, Pandas, SQL, Power BI, machine learning, and data analysis skills.',
        'salary_range': '$60,000 - $75,000 CAD'
    }
    
    # Test analyzer
    analyzer = LlamaJobAnalyzer()
    result = analyzer.analyze_job(profile, job)
    
    if result:
        print("✅ Llama3 Analysis Successful!")
        print(f"Compatibility Score: {result.compatibility_score:.1%}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Reasoning: {result.reasoning}")
        
        # Generate report
        report = analyzer.create_match_report(profile, job, result)
        print("\n" + "="*50)
        print(report)
    else:
        print("❌ Llama3 Analysis Failed")

if __name__ == "__main__":
    test_llama_analyzer()
