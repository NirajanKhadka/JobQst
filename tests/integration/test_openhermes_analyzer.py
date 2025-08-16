#!/usr/bin/env python3
"""
Test script to verify OpenHermes 2.5 job analyzer is working properly
"""

import asyncio
import json
import pytest

try:
    from src.ai.Improved_job_analyzer import ImprovedJobAnalyzer  # type: ignore
    ANALYZER_AVAILABLE = True
except Exception:
    ANALYZER_AVAILABLE = False

from src.utils.profile_helpers import load_profile

@pytest.mark.skipif(not ANALYZER_AVAILABLE, reason="OpenHermes analyzer not available in v4")
def test_openhermes_analyzer():
    """Test OpenHermes 2.5 analyzer with a sample job."""
    
    # Load profile
    profile = load_profile("Nirajan")
    if not profile:
        print("❌ Could not load profile")
        return
    
    print(f"✅ Loaded profile for: {profile.get('name', 'Unknown')}")
    
    # Sample job for testing
    sample_job = {
        "title": "Junior Data Analyst",
        "company": "Tech Solutions Inc",
        "location": "Toronto, ON",
        "description": """
        We are looking for a Junior Data Analyst to join our growing team. 
        
        Requirements:
        - Bachelor's degree in Data Science, Statistics, or related field
        - 0-2 years of experience in data analysis
        - Proficiency in Python, SQL, and Excel
        - Experience with data visualization tools like Tableau or Power BI
        - Knowledge of statistical analysis and machine learning basics
        - Strong analytical and problem-solving skills
        
        Responsibilities:
        - Analyze large datasets to identify trends and patterns
        - Create dashboards and reports using Power BI
        - Collaborate with cross-functional teams
        - Support data-driven decision making
        
        Nice to have:
        - AWS experience
        - Experience with pandas, numpy, scikit-learn
        - Knowledge of machine learning algorithms
        """,
        "salary": "$55,000 - $70,000",
        "experience_level": "Entry Level",
        "url": "https://example.com/job/123"
    }
    
    print("\n📋 Sample Job:")
    print(f"   Title: {sample_job['title']}")
    print(f"   Company: {sample_job['company']}")
    print(f"   Location: {sample_job['location']}")
    
    # Initialize analyzer
    print("\n🤖 Initializing Enhanced Job Analyzer with OpenHermes 2.5...")
    try:
        analyzer = ImprovedJobAnalyzer(
            profile=profile,
            use_openhermes=True,
            fallback_to_llama=True,
            fallback_to_rule_based=True
        )
        print("✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return
    
    # Test analysis
    print("\n🔍 Running job analysis...")
    try:
        analysis_result = analyzer.analyze_job(sample_job)
        
        if analysis_result:
            print("✅ Analysis completed successfully!")
            print(f"\n📊 Analysis Results:")
            print(f"   Method: {analysis_result.get('analysis_method', 'Unknown')}")
            print(f"   Compatibility Score: {analysis_result.get('compatibility_score', 0):.2f}")
            print(f"   Confidence: {analysis_result.get('confidence', 0):.2f}")
            print(f"   Recommendation: {analysis_result.get('recommendation', 'Unknown')}")
            print(f"   Experience Match: {analysis_result.get('experience_match', 'Unknown')}")
            print(f"   Location Match: {analysis_result.get('location_match', 'Unknown')}")
            
            skill_matches = analysis_result.get('skill_matches', [])
            if skill_matches:
                print(f"   Skill Matches: {', '.join(skill_matches[:5])}")
            
            skill_gaps = analysis_result.get('skill_gaps', [])
            if skill_gaps:
                print(f"   Skill Gaps: {', '.join(skill_gaps[:5])}")
            
            reasoning = analysis_result.get('reasoning', '')
            if reasoning:
                print(f"   Reasoning: {reasoning[:200]}...")
            
            # Check if OpenHermes was used
            if analysis_result.get('analysis_method') == 'openhermes_2_5':
                print("\n🎉 OpenHermes 2.5 analysis successful!")
                
                # Show detailed OpenHermes analysis if available
                openhermes_analysis = analysis_result.get('openhermes_analysis')
                if openhermes_analysis:
                    print("\n📈 Detailed OpenHermes Analysis:")
                    match_score = openhermes_analysis.get('match_score', {})
                    if match_score:
                        print(f"   Overall Match: {match_score.get('overall', 0):.2f}")
                        print(f"   Skill Match: {match_score.get('skill_match', 0):.2f}")
                        print(f"   Experience Match: {match_score.get('experience_match', 0):.2f}")
                        print(f"   Location Match: {match_score.get('location_match', 0):.2f}")
                        print(f"   Cultural Fit: {match_score.get('cultural_fit', 0):.2f}")
                        print(f"   Growth Potential: {match_score.get('growth_potential', 0):.2f}")
            else:
                print(f"\n⚠️ Used fallback method: {analysis_result.get('analysis_method')}")
                
        else:
            print("❌ Analysis returned None")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing OpenHermes 2.5 Job Analyzer")
    print("=" * 50)
    test_openhermes_analyzer()
    print("\n" + "=" * 50)
    print("✅ Test completed")