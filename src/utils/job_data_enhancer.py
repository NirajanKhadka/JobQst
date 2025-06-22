#!/usr/bin/env python3
"""
Job Data Enhancer
Extracts missing job information from job links, handles application questions,
and verifies applications via Gmail.
"""

import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright, Page

from job_database import get_job_db
import utils

console = Console()

@dataclass
class JobEnhancement:
    """Enhanced job data extracted from job links."""
    job_id: str
    original_data: Dict[str, Any]
    enhanced_data: Dict[str, Any]
    questions_found: List[Dict[str, str]]
    requirements: List[str]
    benefits: List[str]
    salary_info: Optional[str]
    application_deadline: Optional[str]
    job_type: Optional[str]  # Full-time, Part-time, Contract, etc.
    experience_level: Optional[str]
    skills_required: List[str]
    education_required: Optional[str]

class JobDataEnhancer:
    """
    Enhances job data by extracting detailed information from job links
    and handling application questions.
    """
    
    def __init__(self, profile_name: str):
        """Initialize the job data enhancer."""
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.profile = None
        
        # Question response patterns
        self.question_responses = self._load_question_responses()
        
        # Enhanced data cache
        self.enhanced_cache = {}
    
    async def initialize(self) -> bool:
        """Initialize the enhancer."""
        try:
            self.profile = utils.load_profile(self.profile_name)
            if not self.profile:
                console.print(f"[red]❌ Failed to load profile: {self.profile_name}[/red]")
                return False
            
            console.print(f"[green]✅ Initialized job data enhancer for: {self.profile_name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False
    
    def _load_question_responses(self) -> Dict[str, str]:
        """Load intelligent responses for common application questions."""
        return {
            # Why interested questions
            "why_interested": "I am excited about this opportunity because it aligns perfectly with my career goals and allows me to leverage my technical skills in data analysis and programming to contribute meaningfully to your team's success.",
            
            # Experience questions
            "experience": "I have extensive experience in data analysis, Python programming, SQL databases, and business intelligence tools. My background includes working with large datasets, creating automated reports, and developing data-driven solutions.",
            
            # Strengths questions
            "strengths": "My key strengths include analytical thinking, attention to detail, problem-solving abilities, and strong communication skills. I excel at translating complex data insights into actionable business recommendations.",
            
            # Availability questions
            "availability": "I am available to start immediately or with a standard two-week notice period. I am flexible with scheduling and committed to meeting project deadlines.",
            
            # Salary questions
            "salary": "I am open to discussing compensation based on the role requirements, responsibilities, and market standards. I value opportunities for growth and learning as much as competitive compensation.",
            
            # Relocation questions
            "relocation": "Yes, I am open to relocation for the right opportunity. I am flexible and adaptable to new environments and locations.",
            
            # Remote work questions
            "remote_work": "I am comfortable with remote work, hybrid arrangements, or in-office positions. I have experience working effectively in distributed teams and maintaining productivity in various work environments.",
            
            # Team work questions
            "teamwork": "I work well in collaborative environments and believe in the power of diverse perspectives. I am a good listener, contribute constructively to discussions, and support team goals.",
            
            # Challenges questions
            "challenges": "I approach challenges systematically by breaking them down into manageable components, researching solutions, and collaborating with team members when needed. I view challenges as opportunities to learn and grow.",
            
            # Goals questions
            "goals": "My career goals include continuing to develop my technical expertise, taking on increasing responsibilities in data analysis and business intelligence, and contributing to impactful projects that drive business success."
        }
    
    async def enhance_job_data(self, job: Dict[str, Any]) -> JobEnhancement:
        """
        Enhance job data by extracting detailed information from the job link.
        
        Args:
            job: Job dictionary from database
            
        Returns:
            JobEnhancement object with extracted data
        """
        job_id = job.get('id', job.get('url', 'unknown'))
        url = job.get('url', '')
        
        console.print(f"\n[bold blue]🔍 Enhancing job data for: {job.get('title', 'Unknown')}[/bold blue]")
        
        if not url:
            return JobEnhancement(
                job_id=job_id,
                original_data=job,
                enhanced_data={},
                questions_found=[],
                requirements=[],
                benefits=[],
                salary_info=None,
                application_deadline=None,
                job_type=None,
                experience_level=None,
                skills_required=[],
                education_required=None
            )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            try:
                page = await context.new_page()
                
                # Navigate to job page
                console.print(f"[cyan]🌐 Navigating to: {url[:80]}...[/cyan]")
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Extract enhanced data
                enhanced_data = await self._extract_job_details(page)
                
                # Find application questions
                questions = await self._find_application_questions(page)
                
                # Extract requirements and benefits
                requirements = await self._extract_requirements(page)
                benefits = await self._extract_benefits(page)
                
                # Extract salary information
                salary_info = await self._extract_salary_info(page)
                
                # Extract other details
                job_type = await self._extract_job_type(page)
                experience_level = await self._extract_experience_level(page)
                skills = await self._extract_skills(page)
                education = await self._extract_education_requirements(page)
                deadline = await self._extract_application_deadline(page)
                
                enhancement = JobEnhancement(
                    job_id=job_id,
                    original_data=job,
                    enhanced_data=enhanced_data,
                    questions_found=questions,
                    requirements=requirements,
                    benefits=benefits,
                    salary_info=salary_info,
                    application_deadline=deadline,
                    job_type=job_type,
                    experience_level=experience_level,
                    skills_required=skills,
                    education_required=education
                )
                
                # Cache the enhancement
                self.enhanced_cache[job_id] = enhancement
                
                return enhancement
                
            except Exception as e:
                console.print(f"[red]❌ Enhancement failed: {e}[/red]")
                return JobEnhancement(
                    job_id=job_id,
                    original_data=job,
                    enhanced_data={'error': str(e)},
                    questions_found=[],
                    requirements=[],
                    benefits=[],
                    salary_info=None,
                    application_deadline=None,
                    job_type=None,
                    experience_level=None,
                    skills_required=[],
                    education_required=None
                )
            
            finally:
                await context.close()
                await browser.close()
    
    async def _extract_job_details(self, page: Page) -> Dict[str, Any]:
        """Extract detailed job information from the page."""
        details = {}
        
        try:
            # Get page content
            content = await page.content()
            text_content = await page.evaluate('() => document.body.innerText')
            
            # Extract job description
            description_selectors = [
                '.job-description',
                '.job-details',
                '.description',
                '[class*="description"]',
                '[id*="description"]'
            ]
            
            for selector in description_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        description = await element.inner_text()
                        if len(description) > 100:  # Ensure it's substantial
                            details['full_description'] = description
                            break
                except:
                    continue
            
            # If no specific description found, use page text
            if 'full_description' not in details:
                details['full_description'] = text_content[:2000]  # First 2000 chars
            
            # Extract company information
            company_selectors = [
                '.company-name',
                '.employer',
                '[class*="company"]',
                '[data-testid*="company"]'
            ]
            
            for selector in company_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        company = await element.inner_text()
                        if company.strip():
                            details['company_name'] = company.strip()
                            break
                except:
                    continue
            
            # Extract location information
            location_selectors = [
                '.location',
                '.job-location',
                '[class*="location"]',
                '[data-testid*="location"]'
            ]
            
            for selector in location_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        location = await element.inner_text()
                        if location.strip():
                            details['location'] = location.strip()
                            break
                except:
                    continue
            
            return details
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting job details: {e}[/yellow]")
            return {}
    
    async def _find_application_questions(self, page: Page) -> List[Dict[str, str]]:
        """Find application questions on the page."""
        questions = []
        
        try:
            # Look for common question patterns
            question_selectors = [
                'textarea[name*="question"]',
                'textarea[id*="question"]',
                'input[name*="question"]',
                'select[name*="question"]',
                'textarea[placeholder*="why"]',
                'textarea[placeholder*="experience"]',
                'textarea[placeholder*="tell us"]'
            ]
            
            for selector in question_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        question_text = await self._get_question_text(page, element)
                        if question_text:
                            field_name = await element.get_attribute('name') or await element.get_attribute('id') or 'unknown'
                            
                            questions.append({
                                'question': question_text,
                                'field_name': field_name,
                                'selector': selector,
                                'suggested_response': self._get_intelligent_response(question_text)
                            })
                            
                            console.print(f"[yellow]❓ Found question: {question_text[:100]}...[/yellow]")
                
                except:
                    continue
            
            return questions
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error finding questions: {e}[/yellow]")
            return []

    async def _get_question_text(self, page: Page, element) -> str:
        """Extract question text associated with an input element."""
        try:
            # Try to find associated label
            element_id = await element.get_attribute('id')
            if element_id:
                label = await page.query_selector(f'label[for="{element_id}"]')
                if label:
                    text = await label.inner_text()
                    if text.strip():
                        return text.strip()

            # Try placeholder text
            placeholder = await element.get_attribute('placeholder')
            if placeholder and len(placeholder) > 10:
                return placeholder

            # Try nearby text (parent or sibling elements)
            parent = await element.query_selector('..')
            if parent:
                parent_text = await parent.inner_text()
                # Look for question-like text
                lines = parent_text.split('\n')
                for line in lines:
                    if any(word in line.lower() for word in ['why', 'what', 'how', 'describe', 'tell us', 'explain']):
                        if len(line.strip()) > 10 and len(line.strip()) < 200:
                            return line.strip()

            return ""
        except:
            return ""

    def _get_intelligent_response(self, question_text: str) -> str:
        """Get intelligent response for application question."""
        question_lower = question_text.lower()

        # Match question patterns to responses
        if any(keyword in question_lower for keyword in ['why', 'interest', 'motivated', 'apply']):
            return self.question_responses['why_interested']

        if any(keyword in question_lower for keyword in ['experience', 'background', 'previous']):
            return self.question_responses['experience']

        if any(keyword in question_lower for keyword in ['strength', 'skills', 'abilities']):
            return self.question_responses['strengths']

        if any(keyword in question_lower for keyword in ['available', 'start', 'when']):
            return self.question_responses['availability']

        if any(keyword in question_lower for keyword in ['salary', 'compensation', 'pay']):
            return self.question_responses['salary']

        if any(keyword in question_lower for keyword in ['relocate', 'move', 'location']):
            return self.question_responses['relocation']

        if any(keyword in question_lower for keyword in ['remote', 'work from home', 'hybrid']):
            return self.question_responses['remote_work']

        if any(keyword in question_lower for keyword in ['team', 'collaborate', 'work with others']):
            return self.question_responses['teamwork']

        if any(keyword in question_lower for keyword in ['challenge', 'difficult', 'problem']):
            return self.question_responses['challenges']

        if any(keyword in question_lower for keyword in ['goal', 'future', 'career']):
            return self.question_responses['goals']

        # Default response
        return "I am very interested in this position and believe my skills and experience make me a strong candidate. I am excited about the opportunity to contribute to your team."

    async def _extract_requirements(self, page: Page) -> List[str]:
        """Extract job requirements from the page."""
        requirements = []

        try:
            # Look for requirements sections
            req_selectors = [
                '[class*="requirement"]',
                '[class*="qualification"]',
                '[id*="requirement"]',
                '[id*="qualification"]'
            ]

            text_content = await page.evaluate('() => document.body.innerText')

            # Look for requirement patterns in text
            req_patterns = [
                r'(?:Requirements?|Qualifications?|Must have|Required):?\s*\n((?:.*\n)*?)(?:\n\s*\n|$)',
                r'(?:You will need|We require|Essential):?\s*\n((?:.*\n)*?)(?:\n\s*\n|$)'
            ]

            for pattern in req_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    req_text = match.group(1)
                    # Split into individual requirements
                    lines = [line.strip() for line in req_text.split('\n') if line.strip()]
                    for line in lines:
                        if len(line) > 10 and len(line) < 200:
                            requirements.append(line)

            # Look for bullet points or list items
            list_selectors = ['li', 'ul li', 'ol li']
            for selector in list_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if text and len(text) > 10 and len(text) < 200:
                            # Check if it looks like a requirement
                            if any(keyword in text.lower() for keyword in ['year', 'experience', 'degree', 'skill', 'knowledge', 'ability']):
                                requirements.append(text.strip())
                except:
                    continue

            # Remove duplicates and return first 10
            unique_requirements = list(dict.fromkeys(requirements))[:10]
            return unique_requirements

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting requirements: {e}[/yellow]")
            return []

    async def _extract_benefits(self, page: Page) -> List[str]:
        """Extract job benefits from the page."""
        benefits = []

        try:
            text_content = await page.evaluate('() => document.body.innerText')

            # Look for benefits patterns
            benefit_patterns = [
                r'(?:Benefits?|Perks?|We offer|What we offer):?\s*\n((?:.*\n)*?)(?:\n\s*\n|$)',
                r'(?:Package includes|You will receive):?\s*\n((?:.*\n)*?)(?:\n\s*\n|$)'
            ]

            for pattern in benefit_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    benefit_text = match.group(1)
                    lines = [line.strip() for line in benefit_text.split('\n') if line.strip()]
                    for line in lines:
                        if len(line) > 5 and len(line) < 150:
                            benefits.append(line)

            # Look for common benefit keywords
            benefit_keywords = ['insurance', 'vacation', 'dental', 'health', 'retirement', '401k', 'bonus', 'flexible', 'remote']
            lines = text_content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in benefit_keywords):
                    if len(line.strip()) > 10 and len(line.strip()) < 150:
                        benefits.append(line.strip())

            # Remove duplicates and return first 8
            unique_benefits = list(dict.fromkeys(benefits))[:8]
            return unique_benefits

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting benefits: {e}[/yellow]")
            return []

    async def _extract_salary_info(self, page: Page) -> Optional[str]:
        """Extract salary information from the page."""
        try:
            text_content = await page.evaluate('() => document.body.innerText')

            # Look for salary patterns
            salary_patterns = [
                r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:year|hour|month))?',
                r'[\d,]+k?(?:\s*-\s*[\d,]+k?)?\s*(?:per|/)\s*(?:year|hour|month)',
                r'(?:salary|compensation|pay):\s*\$?[\d,]+(?:\s*-\s*\$?[\d,]+)?'
            ]

            for pattern in salary_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    salary_text = match.group(0)
                    if any(char.isdigit() for char in salary_text):
                        return salary_text.strip()

            return None

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting salary: {e}[/yellow]")
            return None

    async def _extract_job_type(self, page: Page) -> Optional[str]:
        """Extract job type (Full-time, Part-time, Contract, etc.)."""
        try:
            text_content = await page.evaluate('() => document.body.innerText')

            job_types = ['full-time', 'part-time', 'contract', 'temporary', 'internship', 'freelance', 'permanent']

            for job_type in job_types:
                if job_type in text_content.lower():
                    return job_type.title()

            return None

        except Exception as e:
            return None

    async def _extract_experience_level(self, page: Page) -> Optional[str]:
        """Extract required experience level."""
        try:
            text_content = await page.evaluate('() => document.body.innerText')

            # Look for experience patterns
            exp_patterns = [
                r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
                r'(?:entry|junior|senior|mid|lead|principal)\s*level',
                r'(?:entry|junior|senior|mid|lead|principal)\s*(?:position|role)'
            ]

            for pattern in exp_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    return match.group(0).strip()

            return None

        except Exception as e:
            return None

    async def _extract_skills(self, page: Page) -> List[str]:
        """Extract required skills from the page."""
        skills = []

        try:
            text_content = await page.evaluate('() => document.body.innerText')

            # Common technical skills
            skill_keywords = [
                'python', 'sql', 'excel', 'tableau', 'power bi', 'r', 'java', 'javascript',
                'machine learning', 'data analysis', 'statistics', 'pandas', 'numpy',
                'aws', 'azure', 'docker', 'kubernetes', 'git', 'agile', 'scrum'
            ]

            for skill in skill_keywords:
                if skill.lower() in text_content.lower():
                    skills.append(skill.title())

            return skills[:10]  # Return first 10 found

        except Exception as e:
            return []

    async def _extract_education_requirements(self, page: Page) -> Optional[str]:
        """Extract education requirements."""
        try:
            text_content = await page.evaluate('() => document.body.innerText')

            # Look for education patterns
            edu_patterns = [
                r'(?:bachelor|master|phd|doctorate)(?:\'s)?\s*(?:degree)?',
                r'(?:bs|ba|ms|ma|mba|phd)\s*(?:in|degree)',
                r'(?:high school|diploma|certificate)'
            ]

            for pattern in edu_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    return match.group(0).strip()

            return None

        except Exception as e:
            return None

    async def _extract_application_deadline(self, page: Page) -> Optional[str]:
        """Extract application deadline."""
        try:
            text_content = await page.evaluate('() => document.body.innerText')

            # Look for deadline patterns
            deadline_patterns = [
                r'(?:deadline|apply by|closes on):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:deadline|apply by|closes on):\s*([A-Za-z]+ \d{1,2},? \d{4})'
            ]

            for pattern in deadline_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    return match.group(1).strip()

            return None

        except Exception as e:
            return None

    async def enhance_jobs_batch(self, jobs: List[Dict[str, Any]], limit: int = 5) -> List[JobEnhancement]:
        """Enhance multiple jobs in batch."""
        console.print(f"\n[bold blue]🔍 Enhancing {min(len(jobs), limit)} jobs with detailed data extraction[/bold blue]")

        enhancements = []

        with Progress() as progress:
            task = progress.add_task("[green]Enhancing jobs...", total=min(len(jobs), limit))

            for i, job in enumerate(jobs[:limit]):
                enhancement = await self.enhance_job_data(job)
                enhancements.append(enhancement)

                progress.update(task, advance=1)

                # Brief delay between jobs
                if i < min(len(jobs), limit) - 1:
                    await asyncio.sleep(2)

        self._display_enhancement_summary(enhancements)
        return enhancements

    def _display_enhancement_summary(self, enhancements: List[JobEnhancement]):
        """Display summary of job enhancements."""
        console.print("\n" + "="*60)
        console.print(Panel.fit("🔍 JOB ENHANCEMENT SUMMARY", style="bold green"))

        # Summary table
        table = Table(title="Enhancement Results")
        table.add_column("Job", style="cyan", max_width=30)
        table.add_column("Questions Found", style="yellow")
        table.add_column("Requirements", style="green")
        table.add_column("Benefits", style="blue")
        table.add_column("Salary", style="magenta")

        for enhancement in enhancements:
            job_title = enhancement.original_data.get('title', 'Unknown')[:27] + "..."
            questions_count = str(len(enhancement.questions_found))
            req_count = str(len(enhancement.requirements))
            benefits_count = str(len(enhancement.benefits))
            salary = enhancement.salary_info[:20] + "..." if enhancement.salary_info else "Not found"

            table.add_row(job_title, questions_count, req_count, benefits_count, salary)

        console.print(table)

        # Questions summary
        total_questions = sum(len(e.questions_found) for e in enhancements)
        if total_questions > 0:
            console.print(f"\n[yellow]❓ Total application questions found: {total_questions}[/yellow]")

            # Show sample questions
            console.print("\n[bold]Sample Questions Found:[/bold]")
            question_count = 0
            for enhancement in enhancements:
                for question in enhancement.questions_found[:2]:  # Show first 2 per job
                    if question_count < 5:  # Show max 5 total
                        console.print(f"• {question['question'][:80]}...")
                        console.print(f"  [dim]Suggested response: {question['suggested_response'][:60]}...[/dim]")
                        question_count += 1

    def save_enhanced_data(self, enhancements: List[JobEnhancement]) -> bool:
        """Save enhanced job data to database or file."""
        try:
            # For now, save to JSON file
            from pathlib import Path
            import json

            enhanced_file = Path(f"profiles/{self.profile_name}/enhanced_jobs.json")
            enhanced_file.parent.mkdir(exist_ok=True)

            # Convert enhancements to serializable format
            data = []
            for enhancement in enhancements:
                data.append({
                    'job_id': enhancement.job_id,
                    'original_data': enhancement.original_data,
                    'enhanced_data': enhancement.enhanced_data,
                    'questions_found': enhancement.questions_found,
                    'requirements': enhancement.requirements,
                    'benefits': enhancement.benefits,
                    'salary_info': enhancement.salary_info,
                    'application_deadline': enhancement.application_deadline,
                    'job_type': enhancement.job_type,
                    'experience_level': enhancement.experience_level,
                    'skills_required': enhancement.skills_required,
                    'education_required': enhancement.education_required,
                    'enhanced_at': datetime.now().isoformat()
                })

            with open(enhanced_file, 'w') as f:
                json.dump(data, f, indent=2)

            console.print(f"[green]💾 Saved enhanced data for {len(enhancements)} jobs to {enhanced_file}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to save enhanced data: {e}[/red]")
            return False
