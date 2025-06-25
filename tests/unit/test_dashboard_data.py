#!/usr/bin/env python3
"""
Test script to add sample jobs to the database for dashboard testing.
"""

from src.core.job_database import get_job_db
from datetime import datetime, timedelta
import random

def add_sample_jobs():
    """Add sample jobs to test the enhanced dashboard."""
    
    # Initialize database
    db = get_job_db('Nirajan')
    
    # Sample job data with proper company names
    sample_jobs = [
        {
            "title": "Junior Data Analyst",
            "company": "Microsoft Canada",
            "location": "Toronto, ON",
            "url": "https://www.eluta.ca/job/microsoft-junior-data-analyst-toronto",
            "apply_url": "https://www.eluta.ca/job/microsoft-junior-data-analyst-toronto",
            "summary": "Join Microsoft's data team as a Junior Data Analyst. Work with Python, SQL, and Power BI to analyze business data and create insights.",
            "posted_date": "2 days ago",
            "salary": "$65,000 - $75,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Data Analyst",
            "experience_level": "entry",
            "applied": False,
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "Python Developer - Entry Level",
            "company": "Shopify Inc",
            "location": "Ottawa, ON",
            "url": "https://www.eluta.ca/job/shopify-python-developer-ottawa",
            "apply_url": "https://www.eluta.ca/job/shopify-python-developer-ottawa",
            "summary": "Entry-level Python Developer position at Shopify. Work on e-commerce solutions using Python, Django, and modern web technologies.",
            "posted_date": "1 day ago",
            "salary": "$70,000 - $80,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Python Developer",
            "experience_level": "entry",
            "applied": True,
            "scraped_at": (datetime.now() - timedelta(days=1)).isoformat()
        },
        {
            "title": "Business Intelligence Analyst",
            "company": "Royal Bank of Canada",
            "location": "Toronto, ON",
            "url": "https://www.eluta.ca/job/rbc-business-intelligence-analyst-toronto",
            "apply_url": "https://www.eluta.ca/job/rbc-business-intelligence-analyst-toronto",
            "summary": "Join RBC's BI team to create dashboards and reports using Tableau, Power BI, and SQL. Great opportunity for recent graduates.",
            "posted_date": "3 days ago",
            "salary": "$60,000 - $70,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Business Analyst",
            "experience_level": "entry",
            "applied": False,
            "scraped_at": (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            "title": "SQL Developer - Junior",
            "company": "Manulife Financial",
            "location": "Toronto, ON",
            "url": "https://www.eluta.ca/job/manulife-sql-developer-toronto",
            "apply_url": "https://www.eluta.ca/job/manulife-sql-developer-toronto",
            "summary": "Junior SQL Developer role at Manulife. Work with large datasets, create stored procedures, and optimize database performance.",
            "posted_date": "4 days ago",
            "salary": "$55,000 - $65,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "SQL Developer",
            "experience_level": "entry",
            "applied": False,
            "scraped_at": (datetime.now() - timedelta(days=3)).isoformat()
        },
        {
            "title": "Data Visualization Specialist",
            "company": "Deloitte Canada",
            "location": "Toronto, ON",
            "url": "https://www.eluta.ca/job/deloitte-data-visualization-specialist-toronto",
            "apply_url": "https://www.eluta.ca/job/deloitte-data-visualization-specialist-toronto",
            "summary": "Create compelling data visualizations using Tableau, Power BI, and D3.js. Work with clients to transform data into actionable insights.",
            "posted_date": "5 days ago",
            "salary": "$65,000 - $75,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Data Visualization",
            "experience_level": "entry",
            "applied": True,
            "scraped_at": (datetime.now() - timedelta(days=4)).isoformat()
        },
        {
            "title": "Junior Python Analyst",
            "company": "TD Bank Group",
            "location": "Toronto, ON",
            "url": "https://www.eluta.ca/job/td-bank-python-analyst-toronto",
            "apply_url": "https://www.eluta.ca/job/td-bank-python-analyst-toronto",
            "summary": "Python Analyst role in TD's risk management team. Use Python, Pandas, and NumPy for financial data analysis and modeling.",
            "posted_date": "6 days ago",
            "salary": "$58,000 - $68,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Python Analyst",
            "experience_level": "entry",
            "applied": False,
            "scraped_at": (datetime.now() - timedelta(days=5)).isoformat()
        },
        {
            "title": "Excel Data Analyst",
            "company": "KPMG Canada",
            "location": "Toronto, ON",
            "url": "https://www.eluta.ca/job/kpmg-excel-data-analyst-toronto",
            "apply_url": "https://www.eluta.ca/job/kpmg-excel-data-analyst-toronto",
            "summary": "Excel-focused Data Analyst position at KPMG. Create advanced Excel models, pivot tables, and automated reports for client projects.",
            "posted_date": "1 week ago",
            "salary": "$50,000 - $60,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Excel",
            "experience_level": "entry",
            "applied": False,
            "scraped_at": (datetime.now() - timedelta(days=6)).isoformat()
        },
        {
            "title": "Statistical Analyst - Entry Level",
            "company": "Statistics Canada",
            "location": "Ottawa, ON",
            "url": "https://www.eluta.ca/job/statistics-canada-statistical-analyst-ottawa",
            "apply_url": "https://www.eluta.ca/job/statistics-canada-statistical-analyst-ottawa",
            "summary": "Government position for Statistical Analyst. Work with national datasets, perform statistical analysis, and contribute to official statistics.",
            "posted_date": "1 week ago",
            "salary": "$55,000 - $65,000",
            "job_type": "Full-time",
            "site": "eluta_enhanced",
            "search_keyword": "Statistical Analysis",
            "experience_level": "entry",
            "applied": True,
            "scraped_at": (datetime.now() - timedelta(days=7)).isoformat()
        }
    ]
    
    print("Adding sample jobs to database...")
    
    for i, job in enumerate(sample_jobs, 1):
        try:
            db.add_job(job)
            print(f"✅ Added job {i}: {job['title']} at {job['company']}")
        except Exception as e:
            print(f"❌ Error adding job {i}: {e}")
    
    # Get final stats
    stats = db.get_stats()
    print(f"\n📊 Database Stats:")
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   Applied jobs: {stats['applied_jobs']}")
    print(f"   Unapplied jobs: {stats['unapplied_jobs']}")
    print(f"   Unique companies: {stats['unique_companies']}")
    print(f"   Unique sites: {stats['unique_sites']}")
    
    print(f"\n🎉 Sample data added successfully!")
    print(f"🌐 Visit http://localhost:8002 to see the enhanced dashboard")

if __name__ == "__main__":
    add_sample_jobs()
