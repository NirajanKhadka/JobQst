"""
Gemini API Resume & Cover Letter Generator
Generates tailored resumes and cover letters using Google's Gemini API
Outputs to PDF format while preserving custom formatting
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue, gray
from reportlab.lib import colors

from gemini_optimizer import GeminiOptimizer # Import the new optimizer

# Load environment variables
load_dotenv()

class GeminiResumeGenerator:
    """
    Generates resumes and cover letters using Gemini API
    """
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Set up model with optimal settings for document generation
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for factual, consistent output
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 4000,
        }
        
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        # Create output directory
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gemini_resume_generator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_base_document(self, candidate_profile: Dict, doc_type: str, company_name: Optional[str] = None) -> str:
        """Creates a base document string from the candidate profile."""
        if doc_type == "resume":
            return f"""
**{candidate_profile.get('name', 'N/A')}**
{candidate_profile.get('email', 'N/A')} | {candidate_profile.get('phone', 'N/A')} | {candidate_profile.get('location', 'N/A')}

**PROFESSIONAL SUMMARY**
{candidate_profile.get('summary', 'N/A')}

**PROFESSIONAL EXPERIENCE**
{candidate_profile.get('experience', 'N/A')}

**SKILLS**
{candidate_profile.get('skills', 'N/A')}

**EDUCATION**
{candidate_profile.get('education', 'N/A')}

**CERTIFICATIONS**
{candidate_profile.get('certifications', 'N/A')}
"""
        elif doc_type == "cover_letter":
            return f"""
{candidate_profile.get('name', 'N/A')}
{candidate_profile.get('email', 'N/A')}
{candidate_profile.get('phone', 'N/A')}

Date: {datetime.now().strftime("%B %d, %Y")}

Hiring Manager
{company_name}

Dear Hiring Manager,

I am writing to express my interest in the position. My background in {candidate_profile.get('summary', 'N/A')} aligns with the requirements.

Thank you for your time and consideration.

Sincerely,
{candidate_profile.get('name', 'N/A')}
"""
        return ""

    def create_pdf(self, content: str, filename: str, document_type: str = "resume") -> str:
        """
        Create a PDF from the generated content
        
        Args:
            content: The generated resume/cover letter text
            filename: Output filename (without extension)
            document_type: Type of document ("resume" or "cover_letter")
            
        Returns:
            Path to the generated PDF file
        """
        
        pdf_path = self.output_dir / f"{filename}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=1*inch, bottomMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.black,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=12,
            textColor=colors.black,
            alignment=TA_LEFT
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Parse content and create PDF elements
        story = []
        
        # Split content into lines and process
        lines = content.split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            
            # Check if line is a section header (contains common section names)
            if any(header in line.upper() for header in ['PROFESSIONAL SUMMARY', 'EXPERIENCE', 
                                                         'SKILLS', 'EDUCATION', 'CERTIFICATIONS',
                                                         'CONTACT', 'COVER LETTER']):
                story.append(Paragraph(line, heading_style))
            elif '**' in line: # Bolded lines are likely headers or names
                story.append(Paragraph(line.replace('**', ''), title_style if current_section == "" else heading_style))
            elif line.isupper() and len(line) > 3:  # Likely a header
                story.append(Paragraph(line, heading_style))
            else:
                story.append(Paragraph(line, body_style))
        
        # Build PDF
        try:
            doc.build(story)
            self.logger.info(f"PDF created successfully: {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            self.logger.error(f"Error creating PDF: {str(e)}")
            return f"Error creating PDF: {str(e)}"
    
    async def generate_and_save(self, candidate_profile: Dict, job_description: str, 
                         company_name: str, output_filename: str) -> Dict[str, str]:
        """
        Generate both resume and cover letter using the GeminiOptimizer and save as PDFs
        
        Args:
            candidate_profile: Dictionary containing candidate information
            job_description: The job description to tailor documents for
            company_name: Name of the company
            output_filename: Base filename for output files
            
        Returns:
            Dictionary with paths to generated files
        """
        
        results = {}
        optimizer = GeminiOptimizer()

        # Create base documents from the profile
        base_resume = self._create_base_document(candidate_profile, "resume")
        base_cover_letter = self._create_base_document(candidate_profile, "cover_letter", company_name)
        
        try:
            self.logger.info("Optimizing documents with Gemini Optimizer...")
            optimized_data = await optimizer.optimize_documents(
                job_description,
                base_resume,
                base_cover_letter
            )
            self.logger.info("Documents optimized successfully.")

            resume_content = optimized_data.get("optimizedResume", "")
            cover_letter_content = optimized_data.get("optimizedCoverLetter", "")

            if not resume_content or not cover_letter_content:
                raise ValueError("Optimized content is empty in the response.")

            # Create PDFs
            resume_pdf = self.create_pdf(resume_content, f"{output_filename}_resume", "resume")
            results['resume'] = resume_pdf
            
            cover_letter_pdf = self.create_pdf(cover_letter_content, f"{output_filename}_cover_letter", "cover_letter")
            results['cover_letter'] = cover_letter_pdf
            
            # Save raw text and analysis
            with open(self.output_dir / f"{output_filename}_resume.txt", 'w', encoding='utf-8') as f:
                f.write(resume_content)
            
            with open(self.output_dir / f"{output_filename}_cover_letter.txt", 'w', encoding='utf-8') as f:
                f.write(cover_letter_content)

            with open(self.output_dir / f"{output_filename}_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(optimized_data, f, indent=2)
            
            results['analysis'] = str(self.output_dir / f"{output_filename}_analysis.json")

        except (ValueError, RuntimeError) as e:
            self.logger.error(f"An error occurred during optimization: {e}")
            raise

        return results


async def main():
    """Example usage of the Gemini Resume Generator"""
    
    # Sample candidate profile (replace with your actual data)
    candidate_profile = {
        'name': 'Nirajan Khadka',
        'email': 'your.email@example.com',
        'phone': '(555) 123-4567',
        'location': 'Your City, State',
        'summary': 'Experienced Data Analyst with 5+ years in data visualization, statistical analysis, and business intelligence. Proven track record of transforming complex data into actionable insights.',
        'experience': '''
        Data Analyst | ABC Company | 2020-Present
        - Analyzed large datasets using Python, SQL, and Tableau
        - Created automated dashboards that improved decision-making by 40%
        - Collaborated with cross-functional teams to identify key business metrics
        
        Junior Data Analyst | XYZ Corp | 2018-2020
        - Performed statistical analysis on customer behavior data
        - Developed predictive models that increased sales by 15%
        - Maintained and optimized database performance
        ''',
        'skills': 'Python, SQL, Tableau, Power BI, Excel, R, Statistics, Machine Learning, Data Visualization',
        'education': 'Bachelor of Science in Statistics | University Name | 2018',
        'certifications': 'Google Data Analytics Certificate, Tableau Desktop Specialist'
    }
    
    # Sample job description
    job_description = """
    Data Analyst Position at TechCorp
    
    We are seeking a skilled Data Analyst to join our growing team. The ideal candidate will have experience in:
    - Python and SQL for data analysis
    - Creating dashboards and visualizations
    - Statistical analysis and reporting
    - Working with large datasets
    - Business intelligence tools
    
    Requirements:
    - 3+ years of experience in data analysis
    - Proficiency in Python, SQL, and visualization tools
    - Strong analytical and problem-solving skills
    - Bachelor's degree in a quantitative field
    """
    
    try:
        # Initialize generator
        generator = GeminiResumeGenerator()
        
        # Generate documents
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = await generator.generate_and_save(
            candidate_profile=candidate_profile,
            job_description=job_description,
            company_name="TechCorp",
            output_filename=f"nirajan_techcorp_{timestamp}"
        )
        
        print("Documents generated successfully!")
        print(f"Resume: {results.get('resume')}")
        print(f"Cover Letter: {results.get('cover_letter')}")
        print(f"Analysis: {results.get('analysis')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logging.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
