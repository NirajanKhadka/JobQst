#!/usr/bin/env python3
"""
Training Data Generator for AutoJobAgent AI
Creates diverse, realistic profiles and documents for neural network training.

This tool generates:
- Diverse professional profiles across industries
- Multiple resume/cover letter versions per profile
- Realistic job requirements and success patterns
- Training data in proper format for neural networks

Usage:
    python generate_training_data.py --profiles 15 --documents 3
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

class TrainingDataGenerator:
    """Generates realistic training data for AI model training."""
    
    def __init__(self):
        self.profiles = []
        self.documents = []
        
        # Industry templates
        self.industries = {
            "software_engineering": {
                "roles": ["Junior Developer", "Software Engineer", "Senior Developer", "Full Stack Developer", "Backend Developer", "Frontend Developer"],
                "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "Docker", "AWS", "Java", "C++"],
                "companies": ["Microsoft", "Google", "Amazon", "Meta", "Netflix", "Shopify", "Uber", "Airbnb"],
                "keywords": ["agile", "microservices", "API", "database", "cloud", "CI/CD", "testing", "debugging"]
            },
            "data_science": {
                "roles": ["Data Analyst", "Data Scientist", "ML Engineer", "Business Intelligence Analyst", "Data Engineer"],
                "skills": ["Python", "R", "SQL", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "Power BI", "Tableau", "AWS"],
                "companies": ["Google", "Microsoft", "IBM", "Palantir", "Spotify", "Netflix", "Uber", "Tesla"],
                "keywords": ["machine learning", "statistics", "data visualization", "predictive modeling", "ETL", "big data"]
            },
            "product_management": {
                "roles": ["Product Manager", "Senior Product Manager", "Product Owner", "Associate Product Manager"],
                "skills": ["Product Strategy", "User Research", "Agile", "Scrum", "Analytics", "A/B Testing", "Roadmapping"],
                "companies": ["Apple", "Google", "Microsoft", "Amazon", "Meta", "Slack", "Zoom", "Dropbox"],
                "keywords": ["user experience", "product roadmap", "stakeholder management", "market research", "KPIs"]
            },
            "design": {
                "roles": ["UX Designer", "UI Designer", "Product Designer", "Graphic Designer", "Visual Designer"],
                "skills": ["Figma", "Sketch", "Adobe Creative Suite", "Prototyping", "User Research", "HTML/CSS", "Design Systems"],
                "companies": ["Apple", "Google", "Adobe", "Spotify", "Airbnb", "Dribbble", "Behance", "Canva"],
                "keywords": ["user-centered design", "wireframing", "prototyping", "design thinking", "accessibility"]
            },
            "marketing": {
                "roles": ["Marketing Specialist", "Digital Marketing Manager", "Content Marketing Manager", "Social Media Manager"],
                "skills": ["Google Analytics", "SEO", "SEM", "Social Media", "Content Creation", "Email Marketing", "HubSpot"],
                "companies": ["HubSpot", "Salesforce", "Adobe", "Hootsuite", "Buffer", "Mailchimp", "Shopify"],
                "keywords": ["campaign management", "brand awareness", "lead generation", "conversion optimization"]
            }
        }
        
        # Experience levels
        self.experience_levels = {
            "entry": {"years": "0-2", "title_prefix": "Junior", "salary_range": "45k-65k"},
            "mid": {"years": "3-5", "title_prefix": "", "salary_range": "65k-95k"},
            "senior": {"years": "5-8", "title_prefix": "Senior", "salary_range": "95k-130k"},
            "lead": {"years": "8+", "title_prefix": "Lead", "salary_range": "130k-180k"}
        }
        
        # Names and locations
        self.first_names = ["Alex", "Jordan", "Casey", "Morgan", "Taylor", "Riley", "Avery", "Quinn", "Jamie", "Sage", 
                           "Sarah", "Michael", "Jennifer", "David", "Jessica", "Daniel", "Ashley", "Chris", "Amanda", "Matt"]
        self.last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                          "Chen", "Patel", "Kim", "Singh", "Thompson", "Anderson", "Wilson", "Moore", "Taylor", "Jackson"]
        self.locations = ["Toronto, ON", "Vancouver, BC", "Montreal, QC", "Calgary, AB", "Ottawa, ON", "Edmonton, AB",
                         "New York, NY", "San Francisco, CA", "Seattle, WA", "Austin, TX", "Boston, MA", "Chicago, IL"]
    
    def generate_profile(self, industry: str, experience_level: str) -> Dict[str, Any]:
        """Generate a realistic professional profile."""
        
        industry_data = self.industries[industry]
        exp_data = self.experience_levels[experience_level]
        
        # Basic info
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        full_name = f"{first_name} {last_name}"
        
        # Role selection
        base_role = random.choice(industry_data["roles"])
        if experience_level != "entry" and experience_level != "mid":
            role = f"{exp_data['title_prefix']} {base_role}".strip()
        else:
            role = base_role
        
        # Skills (more skills for higher experience)
        skill_count = {"entry": 6, "mid": 8, "senior": 10, "lead": 12}[experience_level]
        skills = random.sample(industry_data["skills"], min(skill_count, len(industry_data["skills"])))
        
        # Add some general skills
        general_skills = ["Communication", "Problem Solving", "Teamwork", "Project Management", "Leadership"]
        skills.extend(random.sample(general_skills, 2))
        
        profile = {
            "id": str(uuid.uuid4()),
            "name": full_name,
            "email": f"{first_name.lower()}.{last_name.lower()}@email.com",
            "phone": f"({random.randint(400,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}",
            "location": random.choice(self.locations),
            "linkedin": f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
            "github": f"https://github.com/{first_name.lower()}{last_name.lower()}",
            "industry": industry,
            "experience_level": experience_level,
            "years_experience": exp_data["years"],
            "current_role": role,
            "skills": skills,
            "target_companies": random.sample(industry_data["companies"], 4),
            "keywords": random.sample(industry_data["keywords"], 4),
            "salary_expectation": exp_data["salary_range"]
        }
        
        return profile
    
    def generate_resume_content(self, profile: Dict[str, Any], job_target: str) -> str:
        """Generate resume content tailored to a specific job."""
        
        industry = profile["industry"]
        exp_level = profile["experience_level"]
        
        # Professional summary
        summary_templates = {
            "entry": f"Motivated {profile['current_role']} with {profile['years_experience']} years of experience in {industry.replace('_', ' ')}. Passionate about {random.choice(profile['keywords'])} and eager to contribute to innovative projects.",
            "mid": f"Experienced {profile['current_role']} with {profile['years_experience']} years of expertise in {industry.replace('_', ' ')}. Proven track record in {random.choice(profile['keywords'])} and {random.choice(profile['keywords'])}.",
            "senior": f"Senior {profile['current_role']} with {profile['years_experience']} years of experience leading {industry.replace('_', ' ')} initiatives. Expert in {random.choice(profile['keywords'])}, {random.choice(profile['keywords'])}, and team leadership.",
            "lead": f"Lead {profile['current_role']} with {profile['years_experience']} years of experience driving {industry.replace('_', ' ')} strategy and innovation. Specialized in {random.choice(profile['keywords'])} and organizational transformation."
        }
        
        summary = summary_templates[exp_level]
        
        # Skills section
        skills_text = ", ".join(profile["skills"][:8])  # Top 8 skills
        
        # Experience section (simplified)
        exp_count = {"entry": 1, "mid": 2, "senior": 3, "lead": 4}[exp_level]
        experience_section = f"PROFESSIONAL EXPERIENCE:\n"
        
        for i in range(exp_count):
            company = random.choice(profile["target_companies"])
            role = profile["current_role"] if i == 0 else f"Junior {profile['current_role']}"
            
            experience_section += f"\n{role} | {company} | 2022-Present\n"
            experience_section += f"• Led {random.choice(profile['keywords'])} initiatives resulting in improved efficiency\n"
            experience_section += f"• Collaborated with cross-functional teams on {random.choice(profile['keywords'])} projects\n"
            experience_section += f"• Utilized {random.choice(profile['skills'])} and {random.choice(profile['skills'])} for project delivery\n"
        
        resume_content = f"""
{profile['name']}
{profile['location']} | {profile['email']} | {profile['phone']}
LinkedIn: {profile['linkedin']} | GitHub: {profile['github']}

PROFESSIONAL SUMMARY:
{summary}

CORE COMPETENCIES:
{skills_text}

{experience_section}

EDUCATION:
Bachelor's Degree in Computer Science | University of Technology | 2020

CERTIFICATIONS:
• Industry-relevant certification in {random.choice(profile['skills'])}
• Professional development in {random.choice(profile['keywords'])}
"""
        
        return resume_content.strip()
    
    def generate_cover_letter_content(self, profile: Dict[str, Any], company: str, position: str) -> str:
        """Generate cover letter tailored to specific company and position."""
        
        opening_templates = [
            f"I am writing to express my strong interest in the {position} position at {company}.",
            f"I am excited to apply for the {position} role at {company}.",
            f"Having followed {company}'s innovative work in the industry, I am thrilled to apply for the {position} position."
        ]
        
        body_templates = [
            f"With {profile['years_experience']} years of experience in {profile['industry'].replace('_', ' ')}, I have developed expertise in {random.choice(profile['skills'])} and {random.choice(profile['skills'])}.",
            f"In my current role as {profile['current_role']}, I have successfully led projects involving {random.choice(profile['keywords'])} and {random.choice(profile['keywords'])}.",
            f"My background in {random.choice(profile['skills'])} and passion for {random.choice(profile['keywords'])} align perfectly with {company}'s mission."
        ]
        
        closing_templates = [
            f"I would welcome the opportunity to discuss how my skills in {random.choice(profile['skills'])} can contribute to {company}'s continued success.",
            f"I am excited about the possibility of bringing my expertise in {random.choice(profile['keywords'])} to the {company} team.",
            f"Thank you for considering my application. I look forward to the opportunity to contribute to {company}'s innovative projects."
        ]
        
        cover_letter = f"""
Dear {company} Hiring Team,

{random.choice(opening_templates)}

{random.choice(body_templates)} {random.choice(body_templates)}

{random.choice(closing_templates)}

Best regards,
{profile['name']}
"""
        
        return cover_letter.strip()
    
    def generate_training_dataset(self, num_profiles: int = 15, documents_per_profile: int = 3) -> Dict[str, Any]:
        """Generate complete training dataset."""
        
        print(f"🚀 Generating {num_profiles} profiles with {documents_per_profile} documents each...")
        
        training_data = []
        
        # Distribute profiles across industries and experience levels
        industries = list(self.industries.keys())
        experience_levels = list(self.experience_levels.keys())
        
        for i in range(num_profiles):
            industry = industries[i % len(industries)]
            exp_level = experience_levels[i % len(experience_levels)]
            
            # Generate profile
            profile = self.generate_profile(industry, exp_level)
            
            # Generate documents for this profile
            for doc_idx in range(documents_per_profile):
                target_company = random.choice(profile["target_companies"])
                target_position = f"{profile['current_role']} - {target_company}"
                
                if doc_idx == 0:
                    # Resume
                    instruction = f"Generate a professional resume for a {profile['current_role']} position"
                    input_text = f"Profile: {profile['current_role']} with {profile['years_experience']} years experience\nSkills: {', '.join(profile['skills'][:5])}\nTarget: {target_position}"
                    output_text = self.generate_resume_content(profile, target_position)
                    document_type = "resume"
                else:
                    # Cover letter
                    instruction = f"Generate a professional cover letter for a {profile['current_role']} position"
                    input_text = f"Company: {target_company}\nPosition: {profile['current_role']}\nCandidate: {profile['name']} with {profile['years_experience']} years experience\nKey Skills: {', '.join(profile['skills'][:3])}"
                    output_text = self.generate_cover_letter_content(profile, target_company, profile['current_role'])
                    document_type = "cover_letter"
                
                training_example = {
                    "id": f"{profile['id']}_{doc_idx}",
                    "instruction": instruction,
                    "input": input_text,
                    "output": output_text,
                    "domain": industry,
                    "document_type": document_type,
                    "experience_level": profile["experience_level"],
                    "profile_id": profile["id"],
                    "metadata": {
                        "target_company": target_company,
                        "skills_mentioned": profile["skills"][:5],
                        "keywords_used": profile["keywords"][:3]
                    }
                }
                
                training_data.append(training_example)
        
        dataset = {
            "metadata": {
                "generated_date": datetime.now().isoformat(),
                "num_profiles": num_profiles,
                "documents_per_profile": documents_per_profile,
                "total_examples": len(training_data),
                "industries": list(self.industries.keys()),
                "experience_levels": list(self.experience_levels.keys())
            },
            "training_data": training_data
        }
        
        print(f"✅ Generated {len(training_data)} training examples")
        return dataset
    
    def save_dataset(self, dataset: Dict[str, Any], output_path: str = "data/ai_training_data.json"):
        """Save the generated dataset to file."""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dataset saved to {output_path}")
        print(f"📊 Total training examples: {len(dataset['training_data'])}")
        
        # Generate summary
        summary_path = output_file.parent / "training_data_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(f"AI Training Data Summary\n")
            f.write(f"Generated: {dataset['metadata']['generated_date']}\n\n")
            f.write(f"Dataset Statistics:\n")
            f.write(f"- Profiles: {dataset['metadata']['num_profiles']}\n")
            f.write(f"- Documents per profile: {dataset['metadata']['documents_per_profile']}\n")
            f.write(f"- Total examples: {dataset['metadata']['total_examples']}\n\n")
            f.write(f"Industries covered: {', '.join(dataset['metadata']['industries'])}\n")
            f.write(f"Experience levels: {', '.join(dataset['metadata']['experience_levels'])}\n")
        
        return output_path


def main():
    """Generate training data for AutoJobAgent AI."""
    
    generator = TrainingDataGenerator()
    
    # Generate dataset
    print("🎯 AutoJobAgent AI Training Data Generator")
    print("=" * 50)
    
    # Start with a good baseline
    num_profiles = 15
    documents_per_profile = 3
    
    dataset = generator.generate_training_dataset(num_profiles, documents_per_profile)
    
    # Save dataset
    output_path = generator.save_dataset(dataset)
    
    print("\n✨ Training data generation complete!")
    print(f"📁 Files created:")
    print(f"  - {output_path}")
    print(f"  - data/training_data_summary.txt")
    print(f"\n🚀 Ready for AI training!")
    print(f"   Next step: python simple_tensorflow_generator.py --data {output_path}")


if __name__ == "__main__":
    main()
