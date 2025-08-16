#!/usr/bin/env python3
"""Create sample jobs for testing the Improved 2-worker system."""

from src.core.job_database import get_job_db
import time

def create_sample_jobs():
    db = get_job_db('default')
    
    sample_jobs = [
        {
            'job_id': 'sample_001',
            'title': 'Senior Python Developer',
            'company': 'TechCorp Inc',
            'location': 'Toronto, ON',
            'summary': 'Looking for an experienced Python developer to join our team.',
            'url': 'https://example.com/jobs/python-dev-001',
            'search_keyword': 'python developer',
            'site': 'sample',
            'scraped_at': str(time.time()),
            'status': 'scraped',
            'job_description': '''
            We are seeking a Senior Python Developer to join our growing engineering team.
            
            Requirements:
            • 5+ years of Python development experience
            • Experience with Django, Flask, or FastAPI
            • Knowledge of PostgreSQL and Redis
            • Familiarity with AWS cloud services
            • Strong problem-solving skills
            
            Responsibilities:
            • Design and develop scalable web applications
            • Collaborate with cross-functional teams
            • Write clean, maintainable code
            • Participate in code reviews
            
            Benefits:
            • Competitive salary ($90,000 - $130,000)
            • Health and dental insurance
            • Remote work options
            • Professional development budget
            
            Employment Type: Full-time
            '''
        },
        {
            'job_id': 'sample_002',
            'title': 'Data Scientist',
            'company': 'DataCorp Analytics',
            'location': 'Vancouver, BC',
            'summary': 'Data scientist role focusing on machine learning and analytics.',
            'url': 'https://example.com/jobs/data-scientist-002',
            'search_keyword': 'data scientist',
            'site': 'sample',
            'scraped_at': str(time.time()),
            'status': 'scraped',
            'job_description': '''
            Join our data science team to build predictive models and analytics solutions.
            
            Requirements:
            • Master's degree in Data Science, Statistics, or related field
            • 3+ years of experience in data science
            • Proficiency in Python, R, and SQL
            • Experience with machine learning frameworks (scikit-learn, TensorFlow, PyTorch)
            • Knowledge of statistical analysis and data visualization
            
            Responsibilities:
            • Develop machine learning models
            • Analyze large datasets to extract insights
            • Create data visualizations and reports
            • Collaborate with business stakeholders
            
            Benefits:
            • Salary range: $80,000 - $120,000
            • Stock options
            • Flexible working hours
            • Learning and development opportunities
            
            Employment Type: Full-time
            '''
        },
        {
            'job_id': 'sample_003',
            'title': 'Full Stack Developer',
            'company': 'StartupXYZ',
            'location': 'Remote',
            'summary': 'Full stack developer for a fast-growing startup.',
            'url': 'https://example.com/jobs/fullstack-003',
            'search_keyword': 'full stack developer',
            'site': 'sample',
            'scraped_at': str(time.time()),
            'status': 'scraped',
            'job_description': '''
            We're looking for a talented Full Stack Developer to help build our Updated platform.
            
            Requirements:
            • 4+ years of full stack development experience
            • Frontend: React, TypeScript, HTML5, CSS3
            • Backend: Node.js, Express, Python
            • Database: MongoDB, PostgreSQL
            • Experience with cloud platforms (AWS, GCP)
            
            Responsibilities:
            • Build responsive web applications
            • Develop RESTful APIs
            • Optimize application performance
            • Work in an agile development environment
            
            Benefits:
            • Competitive salary ($75,000 - $110,000)
            • Equity participation
            • 100% remote work
            • Unlimited PTO
            • Health benefits
            
            Employment Type: Full-time, Remote
            '''
        },
        {
            'job_id': 'sample_004',
            'title': 'DevOps Engineer',
            'company': 'CloudTech Solutions',
            'location': 'Calgary, AB',
            'summary': 'DevOps engineer to manage cloud infrastructure and CI/CD pipelines.',
            'url': 'https://example.com/jobs/devops-004',
            'search_keyword': 'devops engineer',
            'site': 'sample',
            'scraped_at': str(time.time()),
            'status': 'scraped',
            'job_description': '''
            Join our DevOps team to build and maintain scalable cloud infrastructure.
            
            Requirements:
            • 3+ years of DevOps/SRE experience
            • Strong knowledge of AWS, Azure, or GCP
            • Experience with Docker and Kubernetes
            • Proficiency in Infrastructure as Code (Terraform, CloudFormation)
            • CI/CD pipeline experience (Jenkins, GitLab CI, GitHub Actions)
            
            Responsibilities:
            • Design and implement cloud infrastructure
            • Automate deployment processes
            • Monitor system performance and reliability
            • Implement security best practices
            
            Benefits:
            • Salary: $85,000 - $125,000
            • Performance bonuses
            • Professional certifications covered
            • Flexible work arrangements
            
            Employment Type: Full-time
            '''
        },
        {
            'job_id': 'sample_005',
            'title': 'Machine Learning Engineer',
            'company': 'AI Innovations Ltd',
            'location': 'Montreal, QC',
            'summary': 'ML engineer to deploy and scale machine learning models.',
            'url': 'https://example.com/jobs/ml-engineer-005',
            'search_keyword': 'machine learning engineer',
            'site': 'sample',
            'scraped_at': str(time.time()),
            'status': 'scraped',
            'job_description': '''
            We're seeking a Machine Learning Engineer to productionize ML models at scale.
            
            Requirements:
            • Bachelor's/Master's in Computer Science or related field
            • 4+ years of ML engineering experience
            • Strong Python programming skills
            • Experience with MLOps tools and practices
            • Knowledge of deep learning frameworks
            • Cloud platform experience (AWS, GCP, Azure)
            
            Responsibilities:
            • Deploy ML models to production
            • Build ML pipelines and infrastructure
            • Optimize model performance and scalability
            • Collaborate with data scientists and engineers
            
            Benefits:
            • Competitive salary ($95,000 - $140,000)
            • Research and development time
            • Conference attendance budget
            • Comprehensive health benefits
            • Stock options
            
            Employment Type: Full-time
            '''
        }
    ]
    
    print("Creating sample jobs for Improved 2-worker system demonstration...")
    
    for job in sample_jobs:
        success = db.add_job(job)
        if success:
            print(f"✅ Added job: {job['title']} at {job['company']}")
        else:
            print(f"❌ Failed to add job: {job['title']}")
    
    # Check final stats
    stats = db.get_job_stats()
    print(f"\n📊 Database now has {stats['total_jobs']} total jobs")
    
    # Check jobs ready for processing
    scraped_jobs = [job for job in db.get_all_jobs() if job.get('status') == 'scraped']
    print(f"🔄 Jobs ready for processing: {len(scraped_jobs)}")

if __name__ == "__main__":
    create_sample_jobs()