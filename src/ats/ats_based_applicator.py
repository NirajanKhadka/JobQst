#!/usr/bin/env python3
"""
ATS-Based Job Applicator
Advanced job application system with specific strategies for each ATS,
dynamic field processing, and on-the-fly code modification capabilities.
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from playwright.async_api import async_playwright, Page, BrowserContext

from job_database import get_job_db
import utils

console = Console()

@dataclass
class FieldMapping:
    """Field mapping for ATS systems."""
    field_name: str
    selectors: List[str]
    field_type: str  # 'text', 'email', 'tel', 'file', 'select', 'textarea'
    required: bool = False
    validation: Optional[str] = None

@dataclass
class ATSStrategy:
    """ATS-specific application strategy."""
    name: str
    url_patterns: List[str]
    dom_indicators: List[str]
    field_mappings: Dict[str, FieldMapping]
    special_handlers: Dict[str, str]  # Special handling functions
    success_indicators: List[str]
    failure_indicators: List[str]

class ATSBasedApplicator:
    """
    Advanced ATS-based job applicator with dynamic field processing
    and on-the-fly code modification capabilities.
    """
    
    def __init__(self, profile_name: str):
        """Initialize the ATS-based applicator."""
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.profile = None
        
        # Load ATS strategies
        self.ats_strategies = self._load_ats_strategies()
        
        # Dynamic field registry for new fields discovered during applications
        self.dynamic_fields = {}
        
        # Application statistics
        self.stats = {
            "total_processed": 0,
            "successful_applications": 0,
            "failed_applications": 0,
            "manual_reviews": 0,
            "fields_discovered": 0,
            "ats_detected": {}
        }
    
    def _load_ats_strategies(self) -> Dict[str, ATSStrategy]:
        """Load ATS-specific strategies and field mappings."""
        strategies = {}
        
        # Workday Strategy
        strategies["workday"] = ATSStrategy(
            name="Workday",
            url_patterns=["workday.com", "myworkday", "wd1.myworkdayjobs", "wd3.myworkdayjobs"],
            dom_indicators=['[data-automation-id]', '.workday', 'workday-form'],
            field_mappings={
                "first_name": FieldMapping(
                    field_name="first_name",
                    selectors=[
                        'input[data-automation-id*="firstName"]',
                        'input[data-automation-id*="first"]',
                        'input[name*="firstName"]',
                        '#firstName'
                    ],
                    field_type="text",
                    required=True
                ),
                "last_name": FieldMapping(
                    field_name="last_name",
                    selectors=[
                        'input[data-automation-id*="lastName"]',
                        'input[data-automation-id*="last"]',
                        'input[name*="lastName"]',
                        '#lastName'
                    ],
                    field_type="text",
                    required=True
                ),
                "email": FieldMapping(
                    field_name="email",
                    selectors=[
                        'input[data-automation-id*="email"]',
                        'input[type="email"]',
                        'input[name*="email"]',
                        '#email'
                    ],
                    field_type="email",
                    required=True
                ),
                "phone": FieldMapping(
                    field_name="phone",
                    selectors=[
                        'input[data-automation-id*="phone"]',
                        'input[type="tel"]',
                        'input[name*="phone"]',
                        '#phone'
                    ],
                    field_type="tel",
                    required=True
                ),
                "resume": FieldMapping(
                    field_name="resume",
                    selectors=[
                        'input[data-automation-id*="resume"]',
                        'input[data-automation-id*="cv"]',
                        'input[type="file"]',
                        'input[name*="resume"]'
                    ],
                    field_type="file",
                    required=True
                ),
                "cover_letter": FieldMapping(
                    field_name="cover_letter",
                    selectors=[
                        'input[data-automation-id*="coverLetter"]',
                        'input[data-automation-id*="cover"]',
                        'input[name*="cover"]'
                    ],
                    field_type="file",
                    required=False
                )
            },
            special_handlers={
                "multi_step": "handle_workday_multi_step",
                "dropdown": "handle_workday_dropdown",
                "date_picker": "handle_workday_date_picker"
            },
            success_indicators=[
                "application submitted",
                "thank you for applying",
                "application received",
                "successfully submitted"
            ],
            failure_indicators=[
                "error occurred",
                "required field",
                "please complete"
            ]
        )
        
        # Greenhouse Strategy
        strategies["greenhouse"] = ATSStrategy(
            name="Greenhouse",
            url_patterns=["greenhouse.io", "boards.greenhouse"],
            dom_indicators=['.application-form', '.greenhouse', 'greenhouse-form'],
            field_mappings={
                "first_name": FieldMapping(
                    field_name="first_name",
                    selectors=[
                        'input[name*="first_name"]',
                        '#first_name',
                        'input[id*="first"]'
                    ],
                    field_type="text",
                    required=True
                ),
                "last_name": FieldMapping(
                    field_name="last_name",
                    selectors=[
                        'input[name*="last_name"]',
                        '#last_name',
                        'input[id*="last"]'
                    ],
                    field_type="text",
                    required=True
                ),
                "email": FieldMapping(
                    field_name="email",
                    selectors=[
                        'input[name*="email"]',
                        '#email',
                        'input[type="email"]'
                    ],
                    field_type="email",
                    required=True
                ),
                "phone": FieldMapping(
                    field_name="phone",
                    selectors=[
                        'input[name*="phone"]',
                        '#phone',
                        'input[type="tel"]'
                    ],
                    field_type="tel",
                    required=True
                ),
                "resume": FieldMapping(
                    field_name="resume",
                    selectors=[
                        'input[name*="resume"]',
                        'input[type="file"]',
                        '#resume'
                    ],
                    field_type="file",
                    required=True
                )
            },
            special_handlers={
                "questions": "handle_greenhouse_questions",
                "attachments": "handle_greenhouse_attachments"
            },
            success_indicators=[
                "application submitted",
                "thank you for your application",
                "application complete"
            ],
            failure_indicators=[
                "error",
                "required",
                "invalid"
            ]
        )
        
        # Lever Strategy
        strategies["lever"] = ATSStrategy(
            name="Lever",
            url_patterns=["lever.co", "jobs.lever"],
            dom_indicators=['.application-form', '.lever', 'lever-form'],
            field_mappings={
                "name": FieldMapping(
                    field_name="name",
                    selectors=[
                        'input[name*="name"]',
                        '#name',
                        'input[placeholder*="name"]'
                    ],
                    field_type="text",
                    required=True
                ),
                "email": FieldMapping(
                    field_name="email",
                    selectors=[
                        'input[name*="email"]',
                        '#email',
                        'input[type="email"]'
                    ],
                    field_type="email",
                    required=True
                ),
                "phone": FieldMapping(
                    field_name="phone",
                    selectors=[
                        'input[name*="phone"]',
                        '#phone',
                        'input[type="tel"]'
                    ],
                    field_type="tel",
                    required=False
                ),
                "resume": FieldMapping(
                    field_name="resume",
                    selectors=[
                        'input[type="file"]',
                        'input[name*="resume"]'
                    ],
                    field_type="file",
                    required=True
                )
            },
            special_handlers={
                "questions": "handle_lever_questions"
            },
            success_indicators=[
                "application sent",
                "thank you",
                "submitted"
            ],
            failure_indicators=[
                "error",
                "required"
            ]
        )
        
        # Generic/Other Strategy
        strategies["other"] = ATSStrategy(
            name="Other",
            url_patterns=[],
            dom_indicators=[],
            field_mappings={
                "first_name": FieldMapping(
                    field_name="first_name",
                    selectors=[
                        'input[name*="first"]',
                        '#firstName',
                        '#first_name',
                        'input[placeholder*="first"]'
                    ],
                    field_type="text",
                    required=True
                ),
                "last_name": FieldMapping(
                    field_name="last_name",
                    selectors=[
                        'input[name*="last"]',
                        '#lastName',
                        '#last_name',
                        'input[placeholder*="last"]'
                    ],
                    field_type="text",
                    required=True
                ),
                "email": FieldMapping(
                    field_name="email",
                    selectors=[
                        'input[type="email"]',
                        'input[name*="email"]',
                        '#email'
                    ],
                    field_type="email",
                    required=True
                ),
                "phone": FieldMapping(
                    field_name="phone",
                    selectors=[
                        'input[type="tel"]',
                        'input[name*="phone"]',
                        '#phone'
                    ],
                    field_type="tel",
                    required=False
                ),
                "resume": FieldMapping(
                    field_name="resume",
                    selectors=[
                        'input[type="file"]',
                        'input[name*="resume"]',
                        'input[name*="cv"]'
                    ],
                    field_type="file",
                    required=True
                )
            },
            special_handlers={},
            success_indicators=[
                "submitted",
                "thank you",
                "received",
                "success"
            ],
            failure_indicators=[
                "error",
                "required",
                "failed"
            ]
        )
        
        return strategies

    async def initialize(self) -> bool:
        """Initialize the applicator."""
        try:
            self.profile = utils.load_profile(self.profile_name)
            if not self.profile:
                console.print(f"[red]❌ Failed to load profile: {self.profile_name}[/red]")
                return False

            console.print(f"[green]✅ Initialized ATS-based applicator for: {self.profile_name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False

    async def detect_ats(self, page: Page, url: str) -> Tuple[str, float]:
        """
        Detect ATS system with improved accuracy.

        Returns:
            Tuple of (ats_name, confidence_score)
        """
        console.print("[cyan]🔍 Detecting ATS system...[/cyan]")

        # URL-based detection (highest confidence)
        for ats_name, strategy in self.ats_strategies.items():
            if ats_name == "other":
                continue

            for pattern in strategy.url_patterns:
                if pattern.lower() in url.lower():
                    console.print(f"[green]🎯 ATS detected by URL: {ats_name} (confidence: 0.95)[/green]")
                    return ats_name, 0.95

        # DOM-based detection
        try:
            page_content = await page.content()

            for ats_name, strategy in self.ats_strategies.items():
                if ats_name == "other":
                    continue

                confidence = 0.0

                # Check DOM indicators
                for indicator in strategy.dom_indicators:
                    try:
                        elements = await page.query_selector_all(indicator)
                        if elements:
                            confidence += 0.3
                    except:
                        continue

                # Check page content for ATS-specific text
                ats_name_lower = ats_name.lower()
                if ats_name_lower in page_content.lower():
                    confidence += 0.4

                if confidence >= 0.6:
                    console.print(f"[green]🎯 ATS detected by DOM: {ats_name} (confidence: {confidence:.2f})[/green]")
                    return ats_name, confidence

            # Fallback to "other"
            console.print("[yellow]⚠️ No specific ATS detected, using 'other' strategy[/yellow]")
            return "other", 0.3

        except Exception as e:
            console.print(f"[red]❌ ATS detection failed: {e}[/red]")
            return "other", 0.1

    async def discover_fields(self, page: Page, ats_strategy: ATSStrategy) -> Dict[str, Any]:
        """
        Discover all form fields on the page and categorize them.

        Returns:
            Dictionary of discovered fields with metadata
        """
        console.print("[cyan]🔍 Discovering form fields...[/cyan]")

        discovered_fields = {}

        # Find all input elements
        try:
            inputs = await page.query_selector_all('input, select, textarea')

            for input_elem in inputs:
                try:
                    # Get element attributes
                    tag_name = await input_elem.evaluate('el => el.tagName.toLowerCase()')
                    input_type = await input_elem.get_attribute('type') or 'text'
                    name = await input_elem.get_attribute('name') or ''
                    id_attr = await input_elem.get_attribute('id') or ''
                    placeholder = await input_elem.get_attribute('placeholder') or ''
                    required = await input_elem.get_attribute('required') is not None

                    # Create field info
                    field_info = {
                        'tag': tag_name,
                        'type': input_type,
                        'name': name,
                        'id': id_attr,
                        'placeholder': placeholder,
                        'required': required,
                        'selector': f'{tag_name}[name="{name}"]' if name else f'#{id_attr}' if id_attr else None
                    }

                    # Categorize field based on attributes
                    field_category = self._categorize_field(field_info)

                    if field_category:
                        discovered_fields[field_category] = field_info
                        console.print(f"[green]📝 Discovered {field_category}: {field_info['selector']}[/green]")

                except Exception as e:
                    continue

            # Update dynamic fields registry
            self.dynamic_fields.update(discovered_fields)
            self.stats["fields_discovered"] += len(discovered_fields)

            return discovered_fields

        except Exception as e:
            console.print(f"[red]❌ Field discovery failed: {e}[/red]")
            return {}

    def _categorize_field(self, field_info: Dict[str, Any]) -> Optional[str]:
        """Categorize a field based on its attributes."""
        name = field_info.get('name', '').lower()
        id_attr = field_info.get('id', '').lower()
        placeholder = field_info.get('placeholder', '').lower()
        input_type = field_info.get('type', '').lower()

        # Combine all text for analysis
        all_text = f"{name} {id_attr} {placeholder}".lower()

        # Email field
        if input_type == 'email' or any(keyword in all_text for keyword in ['email', 'mail']):
            return 'email'

        # Phone field
        if input_type == 'tel' or any(keyword in all_text for keyword in ['phone', 'tel', 'mobile']):
            return 'phone'

        # File upload (resume/CV)
        if input_type == 'file':
            if any(keyword in all_text for keyword in ['resume', 'cv', 'curriculum']):
                return 'resume'
            elif any(keyword in all_text for keyword in ['cover', 'letter']):
                return 'cover_letter'
            else:
                return 'file_upload'

        # Name fields
        if any(keyword in all_text for keyword in ['firstname', 'first_name', 'first name']):
            return 'first_name'
        if any(keyword in all_text for keyword in ['lastname', 'last_name', 'last name']):
            return 'last_name'
        if 'name' in all_text and 'first' not in all_text and 'last' not in all_text:
            return 'full_name'

        # Address fields
        if any(keyword in all_text for keyword in ['address', 'street']):
            return 'address'
        if any(keyword in all_text for keyword in ['city']):
            return 'city'
        if any(keyword in all_text for keyword in ['state', 'province']):
            return 'state'
        if any(keyword in all_text for keyword in ['zip', 'postal']):
            return 'zip_code'

        # Other common fields
        if any(keyword in all_text for keyword in ['linkedin']):
            return 'linkedin'
        if any(keyword in all_text for keyword in ['website', 'portfolio']):
            return 'website'

        return None

    async def fill_form_fields(self, page: Page, ats_strategy: ATSStrategy, discovered_fields: Dict[str, Any]) -> Dict[str, bool]:
        """
        Fill form fields using ATS strategy and discovered fields.

        Returns:
            Dictionary of field_name -> success_status
        """
        console.print("[cyan]📝 Filling form fields...[/cyan]")

        filled_fields = {}
        profile_data = self._get_profile_data()

        # Combine strategy fields with discovered fields
        all_fields = {**ats_strategy.field_mappings, **self._convert_discovered_to_mappings(discovered_fields)}

        for field_name, field_mapping in all_fields.items():
            if field_name in profile_data:
                value = profile_data[field_name]
                if value:
                    success = await self._try_fill_field(page, field_mapping, value)
                    filled_fields[field_name] = success

                    if success:
                        console.print(f"[green]✅ Filled {field_name}: {value}[/green]")
                    else:
                        console.print(f"[yellow]⚠️ Could not fill {field_name}[/yellow]")

        return filled_fields

    def _get_profile_data(self) -> Dict[str, str]:
        """Get profile data for form filling."""
        # Check if profile is loaded
        if not self.profile:
            console.print("[yellow]⚠️ Profile not loaded, using fallback data[/yellow]")
            return {
                'first_name': 'Test',
                'last_name': 'User',
                'full_name': 'Test User',
                'email': 'test@example.com',
                'phone': '123-456-7890',
                'address': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'zip_code': '12345',
                'linkedin': 'https://linkedin.com/in/testuser',
                'website': 'https://testuser.com'
            }
        
        return {
            'first_name': self.profile.get('first_name', ''),
            'last_name': self.profile.get('last_name', ''),
            'full_name': f"{self.profile.get('first_name', '')} {self.profile.get('last_name', '')}".strip(),
            'email': self.profile.get('email', 'Nirajan.tech@gmail.com'),
            'phone': self.profile.get('phone', ''),
            'address': self.profile.get('address', ''),
            'city': self.profile.get('city', ''),
            'state': self.profile.get('state', ''),
            'zip_code': self.profile.get('zip_code', ''),
            'linkedin': self.profile.get('linkedin', ''),
            'website': self.profile.get('website', '')
        }

    def _convert_discovered_to_mappings(self, discovered_fields: Dict[str, Any]) -> Dict[str, FieldMapping]:
        """Convert discovered fields to FieldMapping objects."""
        mappings = {}

        for field_name, field_info in discovered_fields.items():
            if field_info.get('selector'):
                mappings[field_name] = FieldMapping(
                    field_name=field_name,
                    selectors=[field_info['selector']],
                    field_type=field_info.get('type', 'text'),
                    required=field_info.get('required', False)
                )

        return mappings

    async def _try_fill_field(self, page: Page, field_mapping: FieldMapping, value: str) -> bool:
        """Try to fill a field using multiple selectors."""
        for selector in field_mapping.selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Check if field is visible and enabled
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()

                    if is_visible and is_enabled:
                        # Handle different field types
                        if field_mapping.field_type == 'file':
                            # Handle file upload
                            await element.set_input_files(value)
                        elif field_mapping.field_type == 'select':
                            # Handle dropdown
                            await element.select_option(value)
                        else:
                            # Handle text input - clear first, then fill
                            await element.fill("")  # Clear the field
                            await element.fill(value)

                        return True
            except Exception as e:
                console.print(f"[yellow]⚠️ Error filling field with selector {selector}: {e}[/yellow]")
                continue

        return False

    async def apply_to_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply to a single job using ATS-based strategy.

        Returns:
            Application result dictionary
        """
        start_time = time.time()
        job_title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        url = job.get('url', '')

        console.print(f"\n[bold blue]🎯 Applying to: {job_title} at {company}[/bold blue]")

        if not url:
            return {
                'status': 'failed',
                'error': 'No URL provided',
                'duration': time.time() - start_time
            }

        # Skip Eluta URLs completely
        if any(eluta_pattern in url.lower() for eluta_pattern in [
            'eluta.ca', 'sandbox', 'destination=', 'eluta.com'
        ]):
            console.print(f"[yellow]⚠️ Skipping Eluta URL: {url[:80]}...[/yellow]")
            return {
                'status': 'failed',
                'error': 'Eluta URL skipped - not a real job link',
                'duration': time.time() - start_time
            }

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

                # Detect ATS
                ats_name, confidence = await self.detect_ats(page, url)
                ats_strategy = self.ats_strategies[ats_name]

                # Update stats
                self.stats["ats_detected"][ats_name] = self.stats["ats_detected"].get(ats_name, 0) + 1

                # Discover fields
                discovered_fields = await self.discover_fields(page, ats_strategy)

                # Fill form fields
                filled_fields = await self.fill_form_fields(page, ats_strategy, discovered_fields)

                # Handle special ATS-specific logic
                await self._handle_special_ats_logic(page, ats_strategy)

                # Check for success/failure indicators
                result_status = await self._check_application_status(page, ats_strategy)

                # Pause for user review if needed
                if result_status == 'manual_review':
                    console.print("[yellow]⚠️ Manual review required. Please complete the application manually.[/yellow]")
                    input("Press Enter when application is complete...")
                    result_status = 'applied'

                return {
                    'status': result_status,
                    'ats_detected': ats_name,
                    'ats_confidence': confidence,
                    'fields_filled': filled_fields,
                    'fields_discovered': len(discovered_fields),
                    'duration': time.time() - start_time
                }

            except Exception as e:
                console.print(f"[red]❌ Application failed: {e}[/red]")
                return {
                    'status': 'failed',
                    'error': str(e),
                    'duration': time.time() - start_time
                }

            finally:
                await context.close()
                await browser.close()

    async def _handle_special_ats_logic(self, page: Page, ats_strategy: ATSStrategy):
        """Handle ATS-specific special logic."""
        for handler_name, handler_func in ats_strategy.special_handlers.items():
            try:
                if handler_name == "multi_step" and ats_strategy.name == "Workday":
                    await self._handle_workday_multi_step(page)
                elif handler_name == "questions":
                    await self._handle_application_questions(page)
                # Add more handlers as needed
            except Exception as e:
                console.print(f"[yellow]⚠️ Special handler {handler_name} failed: {e}[/yellow]")

    async def _handle_workday_multi_step(self, page: Page):
        """Handle Workday's multi-step application process."""
        console.print("[cyan]🔄 Handling Workday multi-step process...[/cyan]")

        # Look for Next/Continue buttons
        next_selectors = [
            'button[data-automation-id*="next"]',
            'button[data-automation-id*="continue"]',
            'button:has-text("Next")',
            'button:has-text("Continue")'
        ]

        for selector in next_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    console.print("[cyan]🔄 Clicking Next/Continue button[/cyan]")
                    await button.click()
                    await page.wait_for_timeout(2000)
                    break
            except:
                continue

    async def _handle_application_questions(self, page: Page):
        """Handle application questions dynamically."""
        console.print("[cyan]❓ Checking for application questions...[/cyan]")

        # Look for common question patterns
        question_selectors = [
            'textarea[name*="question"]',
            'textarea[id*="question"]',
            'input[name*="question"]',
            'select[name*="question"]'
        ]

        for selector in question_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    # Get question text from label or nearby text
                    question_text = await self._get_question_text(page, element)
                    if question_text:
                        console.print(f"[yellow]❓ Found question: {question_text[:100]}...[/yellow]")

                        # Ask user for response or use default
                        response = self._get_question_response(question_text)
                        if response:
                            await element.fill(response)
                            console.print(f"[green]✅ Answered question[/green]")
            except:
                continue

    async def _get_question_text(self, page: Page, element) -> str:
        """Extract question text associated with an input element."""
        try:
            # Try to find associated label
            element_id = await element.get_attribute('id')
            if element_id:
                label = await page.query_selector(f'label[for="{element_id}"]')
                if label:
                    return await label.inner_text()

            # Try to find nearby text
            parent = await element.query_selector('..')
            if parent:
                return await parent.inner_text()

            return ""
        except:
            return ""

    def _get_question_response(self, question_text: str) -> str:
        """Get response for application question."""
        question_lower = question_text.lower()

        # Common question responses
        if any(keyword in question_lower for keyword in ['why', 'interest', 'motivated']):
            return "I am excited about this opportunity because it aligns with my career goals and allows me to contribute my skills to your team."

        if any(keyword in question_lower for keyword in ['experience', 'background']):
            return "I have relevant experience in data analysis, programming, and problem-solving that makes me a strong candidate for this position."

        if any(keyword in question_lower for keyword in ['salary', 'compensation']):
            return "I am open to discussing compensation based on the role requirements and market standards."

        if any(keyword in question_lower for keyword in ['start', 'available']):
            return "I am available to start immediately or with standard notice period."

        # Default response
        return "Yes, I am interested in this position and believe I would be a great fit."

    async def _check_application_status(self, page: Page, ats_strategy: ATSStrategy) -> str:
        """Check if application was successful based on page content."""
        try:
            page_content = await page.content()
            page_text = page_content.lower()

            # Check for success indicators
            for indicator in ats_strategy.success_indicators:
                if indicator.lower() in page_text:
                    console.print(f"[green]✅ Success indicator found: {indicator}[/green]")
                    return 'applied'

            # Check for failure indicators
            for indicator in ats_strategy.failure_indicators:
                if indicator.lower() in page_text:
                    console.print(f"[red]❌ Failure indicator found: {indicator}[/red]")
                    return 'failed'

            # Check for manual review indicators
            manual_indicators = ['captcha', 'verify', 'human', 'security', 'additional information']
            for indicator in manual_indicators:
                if indicator in page_text:
                    console.print(f"[yellow]⚠️ Manual review required: {indicator}[/yellow]")
                    return 'manual_review'

            # Default to manual review if unclear
            return 'manual_review'

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not determine application status: {e}[/yellow]")
            return 'manual_review'

    async def apply_to_jobs_batch(self, jobs: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
        """Apply to multiple jobs in batches."""
        console.print(f"\n[bold blue]🚀 Starting ATS-based application process for {len(jobs)} jobs[/bold blue]")

        results = []

        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            console.print(f"\n[cyan]📦 Processing batch {i//batch_size + 1} ({len(batch)} jobs)[/cyan]")

            for job in batch:
                result = await self.apply_to_job(job)
                results.append(result)

                # Update stats
                self.stats["total_processed"] += 1
                if result['status'] == 'applied':
                    self.stats["successful_applications"] += 1
                elif result['status'] == 'failed':
                    self.stats["failed_applications"] += 1
                elif result['status'] == 'manual_review':
                    self.stats["manual_reviews"] += 1

                # Delay between applications
                if i + len(batch) < len(jobs):
                    console.print("[yellow]⏳ Waiting 30 seconds before next application...[/yellow]")
                    await asyncio.sleep(30)

        self._display_final_results(results)
        return results

    def _display_final_results(self, results: List[Dict[str, Any]]):
        """Display final application results."""
        console.print("\n" + "="*60)
        console.print(Panel.fit("🎯 ATS-BASED APPLICATION RESULTS", style="bold green"))

        # Results table
        table = Table(title="Application Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")

        total = len(results)
        if total > 0:
            table.add_row("Total Applications", str(total), "100.0%")
            table.add_row("Successful", str(self.stats["successful_applications"]),
                         f"{(self.stats['successful_applications']/total)*100:.1f}%")
            table.add_row("Failed", str(self.stats["failed_applications"]),
                         f"{(self.stats['failed_applications']/total)*100:.1f}%")
            table.add_row("Manual Reviews", str(self.stats["manual_reviews"]),
                         f"{(self.stats['manual_reviews']/total)*100:.1f}%")

        console.print(table)

        # ATS detection summary
        if self.stats["ats_detected"]:
            ats_table = Table(title="ATS Systems Detected")
            ats_table.add_column("ATS System", style="cyan")
            ats_table.add_column("Count", style="green")

            for ats_name, count in self.stats["ats_detected"].items():
                ats_table.add_row(ats_name.title(), str(count))

            console.print(ats_table)

        # Fields discovered
        console.print(f"\n[cyan]📝 Total fields discovered: {self.stats['fields_discovered']}[/cyan]")

        # Save dynamic fields for future use
        self._save_dynamic_fields()

    def _save_dynamic_fields(self):
        """Save discovered fields for future applications."""
        if self.dynamic_fields:
            try:
                fields_file = Path(f"profiles/{self.profile_name}/discovered_fields.json")
                fields_file.parent.mkdir(exist_ok=True)

                with open(fields_file, 'w') as f:
                    json.dump(self.dynamic_fields, f, indent=2)

                console.print(f"[green]💾 Saved {len(self.dynamic_fields)} discovered fields to {fields_file}[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not save discovered fields: {e}[/yellow]")

    def add_custom_field_mapping(self, ats_name: str, field_name: str, selectors: List[str], field_type: str = "text"):
        """Add custom field mapping on the fly."""
        if ats_name in self.ats_strategies:
            new_mapping = FieldMapping(
                field_name=field_name,
                selectors=selectors,
                field_type=field_type,
                required=False
            )
            self.ats_strategies[ats_name].field_mappings[field_name] = new_mapping
            console.print(f"[green]✅ Added custom field mapping: {field_name} for {ats_name}[/green]")
        else:
            console.print(f"[red]❌ ATS strategy not found: {ats_name}[/red]")

    def get_stats(self) -> Dict[str, Any]:
        """Get application statistics."""
        return self.stats.copy()


# Convenience functions
async def apply_with_ats_detection(profile_name: str, jobs: List[Dict[str, Any]], batch_size: int = 3) -> List[Dict[str, Any]]:
    """
    Convenience function to apply to jobs with ATS detection.

    Args:
        profile_name: Name of the user profile
        jobs: List of job dictionaries
        batch_size: Number of jobs to process in parallel

    Returns:
        List of application results
    """
    applicator = ATSBasedApplicator(profile_name)

    if not await applicator.initialize():
        return []

    return await applicator.apply_to_jobs_batch(jobs, batch_size)


async def test_ats_detection(profile_name: str = "Nirajan", num_jobs: int = 3) -> None:
    """Test ATS detection with a few jobs."""
    console.print(Panel.fit("🧪 TESTING ATS DETECTION SYSTEM", style="bold magenta"))

    applicator = ATSBasedApplicator(profile_name)
    if not await applicator.initialize():
        return

    # Get jobs from database
    jobs = applicator.db.get_unapplied_jobs(limit=num_jobs)
    if not jobs:
        console.print("[yellow]No jobs available for testing[/yellow]")
        return

    console.print(f"[cyan]🔍 Testing ATS detection with {len(jobs)} jobs...[/cyan]")

    results = await applicator.apply_to_jobs_batch(jobs, batch_size=1)

    console.print(f"[green]✅ ATS detection test completed! Processed {len(results)} jobs[/green]")


if __name__ == "__main__":
    import asyncio

    # Run test when script is executed directly
    asyncio.run(test_ats_detection())
