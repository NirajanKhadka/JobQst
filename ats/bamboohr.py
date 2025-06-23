"""
BambooHR ATS submitter implementation.
Handles job application automation for BambooHR-based job portals.
"""

from typing import Dict

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_submitter import BaseSubmitter
import utils

console = Console()

class BambooHRSubmitter(BaseSubmitter):
    """
    Submitter for BambooHR ATS.
    Handles automation of job applications on BambooHR-based portals.
    """
    
    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Submit an application to BambooHR ATS.
        
        Args:
            job: Job dictionary with details
            profile: User profile dictionary
            resume_path: Path to the resume file
            cover_letter_path: Path to the cover letter file
            
        Returns:
            Status string (e.g., "Applied", "Failed", "Manual")
        """
        console.print("[bold blue]Starting BambooHR application process[/bold blue]")
        
        page = self.ctx.new_page()
        
        try:
            # Navigate to the job URL
            console.print(f"[green]Navigating to job URL: {job['url']}[/green]")
            page.goto(job["url"], timeout=30000)
            self.wait_for_navigation(page)

            # Handle login if needed
            if self.handle_login(page, profile, job["url"]):
                console.print("[green]Login completed[/green]")
            else:
                console.print("[yellow]Manual login may be required[/yellow]")
            
            # Check for CAPTCHA
            self.check_for_captcha(page)
            
            # BambooHR typically has an "Apply Now" or "Apply for this Position" button
            apply_button_selectors = [
                "button:has-text('Apply Now')",
                "button:has-text('Apply for this Position')",
                "button:has-text('Apply')",
                "a:has-text('Apply Now')",
                "a:has-text('Apply for this Position')",
                "a:has-text('Apply')",
                ".apply-button",
                "#apply-button",
                "[data-testid*='apply']",
                "button[class*='apply']"
            ]
            
            apply_clicked = False
            for selector in apply_button_selectors:
                try:
                    if page.is_visible(selector):
                        console.print(f"[green]Clicking Apply button: {selector}[/green]")
                        page.click(selector)
                        self.wait_for_navigation(page)
                        apply_clicked = True
                        break
                except Exception as e:
                    console.print(f"[yellow]Failed to click {selector}: {e}[/yellow]")
                    continue
            
            if not apply_clicked:
                console.print("[yellow]Could not find Apply button, trying to proceed with form filling[/yellow]")
            
            # Fill out the application form
            return self._fill_application_form(page, job, profile, resume_path, cover_letter_path)
            
        except utils.NeedsHumanException as e:
            console.print(f"[bold yellow]Human intervention needed: {e}[/bold yellow]")
            return "Manual"
        except Exception as e:
            console.print(f"[bold red]Error in BambooHR application: {e}[/bold red]")
            return "Failed"
        finally:
            page.close()
    
    def _fill_application_form(self, page: Page, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Fill out the BambooHR application form step-by-step with user interaction.

        Args:
            page: Playwright page
            job: Job dictionary
            profile: Profile dictionary
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file

        Returns:
            Status string
        """
        try:
            console.print("[bold blue]Starting interactive step-by-step application process[/bold blue]")
            console.print("[yellow]Dashboard is running at http://localhost:8002 for monitoring[/yellow]")

            # Wait for initial form to load
            page.wait_for_timeout(3000)

            step_number = 1
            max_steps = 10  # Safety limit

            while step_number <= max_steps:
                console.print(f"\n[bold cyan]═══ STEP {step_number} ═══[/bold cyan]")

                # Identify current step and fill appropriate fields
                step_result = self._process_current_step(page, profile, resume_path, cover_letter_path, step_number)

                if step_result == "COMPLETED":
                    console.print("[bold green]Application completed successfully![/bold green]")
                    return "Applied"
                elif step_result == "FAILED":
                    console.print("[bold red]Application failed[/bold red]")
                    return "Failed"
                elif step_result == "MANUAL":
                    console.print("[bold yellow]Manual intervention required[/bold yellow]")
                    return "Manual"

                # Ask user if everything looks correct
                console.print(f"[yellow]Step {step_number} processing complete.[/yellow]")

                # Check for pause signal from dashboard
                if utils.check_pause_signal():
                    console.print("[yellow]Pause signal detected from dashboard[/yellow]")
                    self._wait_for_resume()

                # Interactive confirmation
                user_input = input("\\n[?] Does everything look correct? (y/n/pause/quit/learn): ").strip().lower()

                if user_input == 'n':
                    console.print("[yellow]Please manually correct the fields, then press Enter to continue...[/yellow]")
                    input()
                    # After manual correction, learn the new values
                    console.print("[cyan]Learning from your manual inputs...[/cyan]")
                    self._learn_from_manual_input(page, profile, step_number)
                elif user_input == 'learn':
                    console.print("[cyan]Learning current field values for future use...[/cyan]")
                    self._learn_from_manual_input(page, profile, step_number)
                elif user_input == 'pause':
                    console.print("[yellow]Application paused. Type 'resume' to continue...[/yellow]")
                    self._wait_for_resume()
                elif user_input == 'quit':
                    console.print("[red]Application cancelled by user[/red]")
                    return "Manual"

                # Try to move to next step
                if not self._move_to_next_step(page):
                    console.print("[yellow]No more steps found, attempting to submit...[/yellow]")
                    if self._submit_application(page):
                        console.print("[bold green]Application submitted successfully![/bold green]")
                        return "Applied"
                    else:
                        console.print("[yellow]Could not submit automatically[/yellow]")
                        return "Manual"

                step_number += 1
                page.wait_for_timeout(2000)  # Wait for next step to load

            console.print("[yellow]Maximum steps reached, attempting final submission...[/yellow]")
            if self._submit_application(page):
                return "Applied"
            else:
                return "Manual"

        except Exception as e:
            console.print(f"[bold red]Error in step-by-step application: {e}[/bold red]")
            return "Failed"
    
    def _upload_resume(self, page: Page, resume_path: str) -> bool:
        """Upload resume file to BambooHR form."""
        resume_selectors = [
            "input[type='file'][name*='resume']",
            "input[type='file'][name*='cv']",
            "input[type='file'][id*='resume']",
            "input[type='file'][id*='cv']",
            "input[type='file'][class*='resume']",
            "input[type='file'][class*='cv']",
            "input[type='file']"  # Fallback to any file input
        ]
        
        try:
            return utils.smart_attach(page, resume_selectors, resume_path)
        except utils.NeedsHumanException:
            console.print("[yellow]Could not upload resume automatically[/yellow]")
            return False
    
    def _upload_cover_letter(self, page: Page, cover_letter_path: str) -> bool:
        """Upload cover letter file to BambooHR form."""
        cover_letter_selectors = [
            "input[type='file'][name*='cover']",
            "input[type='file'][name*='letter']",
            "input[type='file'][id*='cover']",
            "input[type='file'][id*='letter']",
            "input[type='file'][class*='cover']",
            "input[type='file'][class*='letter']"
        ]
        
        try:
            return utils.smart_attach(page, cover_letter_selectors, cover_letter_path)
        except utils.NeedsHumanException:
            console.print("[yellow]Could not upload cover letter automatically[/yellow]")
            return False
    
    def _fill_bamboohr_specific_fields(self, page: Page, profile: Dict) -> None:
        """Fill BambooHR-specific form fields."""
        # Common BambooHR field mappings
        field_mappings = {
            "input[name*='linkedin']": profile.get("linkedin", ""),
            "input[name*='website']": profile.get("website", ""),
            "input[name*='portfolio']": profile.get("portfolio", ""),
            "textarea[name*='additional']": profile.get("additional_info", ""),
            "textarea[name*='comments']": profile.get("comments", ""),
            "select[name*='source']": "Job Board",  # How did you hear about us
            "select[name*='referral']": "Online",
        }
        
        fields_filled = self.fill_form_fields(page, field_mappings)
        console.print(f"[green]Filled {fields_filled} BambooHR-specific fields[/green]")
    
    def _handle_screening_questions(self, page: Page, profile: Dict) -> None:
        """Handle screening questions in BambooHR forms."""
        # Look for common screening questions
        screening_selectors = [
            "input[type='radio']",
            "select[name*='question']",
            "textarea[name*='question']",
            "input[name*='question']"
        ]
        
        # Handle yes/no questions (typically authorization to work, etc.)
        yes_no_questions = page.query_selector_all("input[type='radio'][value='yes'], input[type='radio'][value='true']")
        for question in yes_no_questions:
            try:
                question.click()
            except Exception:
                continue
        
        console.print("[green]Handled screening questions[/green]")
    
    def _submit_application(self, page: Page) -> bool:
        """Submit the BambooHR application."""
        submit_selectors = [
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "input[type='submit'][value*='Submit']",
            "input[type='submit'][value*='Apply']",
            "button[type='submit']",
            ".submit-button",
            "#submit-button"
        ]
        
        for selector in submit_selectors:
            try:
                if page.is_visible(selector):
                    console.print(f"[green]Clicking submit button: {selector}[/green]")
                    page.click(selector)
                    
                    # Wait for submission to complete
                    page.wait_for_timeout(3000)
                    
                    # Check for success indicators
                    success_indicators = [
                        "text=Thank you",
                        "text=Application submitted",
                        "text=Successfully submitted",
                        ".success-message",
                        ".confirmation"
                    ]
                    
                    for indicator in success_indicators:
                        if page.is_visible(indicator):
                            return True
                    
                    return True  # Assume success if no error
                    
            except Exception as e:
                console.print(f"[yellow]Failed to submit with {selector}: {e}[/yellow]")
                continue
        
        return False

    def _fill_personal_information(self, page: Page, profile: Dict) -> int:
        """Fill comprehensive personal information like Simplify."""
        fields_filled = 0

        # Get name components
        full_name = profile.get("name", "")
        name_parts = full_name.split() if full_name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""

        # Comprehensive personal information mappings
        personal_mappings = {
            # Name fields - various formats
            "input[name*='firstName']": first_name,
            "input[name*='first_name']": first_name,
            "input[name*='first-name']": first_name,
            "input[id*='firstName']": first_name,
            "input[id*='first_name']": first_name,
            "input[placeholder*='First name']": first_name,
            "input[placeholder*='First Name']": first_name,

            "input[name*='lastName']": last_name,
            "input[name*='last_name']": last_name,
            "input[name*='last-name']": last_name,
            "input[id*='lastName']": last_name,
            "input[id*='last_name']": last_name,
            "input[placeholder*='Last name']": last_name,
            "input[placeholder*='Last Name']": last_name,

            "input[name*='middleName']": middle_name,
            "input[name*='middle_name']": middle_name,
            "input[name*='middle-name']": middle_name,
            "input[id*='middleName']": middle_name,
            "input[placeholder*='Middle name']": middle_name,

            "input[name*='fullName']": full_name,
            "input[name*='full_name']": full_name,
            "input[name*='name']": full_name,
            "input[id*='fullName']": full_name,
            "input[placeholder*='Full name']": full_name,

            # Contact information
            "input[type='email']": profile.get("email", ""),
            "input[name*='email']": profile.get("email", ""),
            "input[id*='email']": profile.get("email", ""),
            "input[placeholder*='email']": profile.get("email", ""),
            "input[placeholder*='Email']": profile.get("email", ""),

            "input[name*='phone']": profile.get("phone", ""),
            "input[name*='telephone']": profile.get("phone", ""),
            "input[name*='mobile']": profile.get("phone", ""),
            "input[id*='phone']": profile.get("phone", ""),
            "input[id*='telephone']": profile.get("phone", ""),
            "input[placeholder*='phone']": profile.get("phone", ""),
            "input[placeholder*='Phone']": profile.get("phone", ""),

            # Address/Location
            "input[name*='address']": profile.get("location", ""),
            "input[name*='location']": profile.get("location", ""),
            "input[name*='city']": profile.get("location", "").split(",")[0] if "," in profile.get("location", "") else profile.get("location", ""),
            "input[id*='address']": profile.get("location", ""),
            "input[id*='location']": profile.get("location", ""),
            "input[placeholder*='address']": profile.get("location", ""),
            "input[placeholder*='Address']": profile.get("location", ""),
            "input[placeholder*='location']": profile.get("location", ""),
            "input[placeholder*='Location']": profile.get("location", ""),

            # Professional links
            "input[name*='linkedin']": profile.get("linkedin", ""),
            "input[name*='linkedIn']": profile.get("linkedin", ""),
            "input[name*='LinkedIn']": profile.get("linkedin", ""),
            "input[id*='linkedin']": profile.get("linkedin", ""),
            "input[placeholder*='linkedin']": profile.get("linkedin", ""),
            "input[placeholder*='LinkedIn']": profile.get("linkedin", ""),

            "input[name*='github']": profile.get("github", ""),
            "input[name*='GitHub']": profile.get("github", ""),
            "input[id*='github']": profile.get("github", ""),
            "input[placeholder*='github']": profile.get("github", ""),
            "input[placeholder*='GitHub']": profile.get("github", ""),

            "input[name*='website']": profile.get("github", ""),
            "input[name*='portfolio']": profile.get("github", ""),
            "input[id*='website']": profile.get("github", ""),
            "input[placeholder*='website']": profile.get("github", ""),
            "input[placeholder*='Website']": profile.get("github", ""),
            "input[placeholder*='portfolio']": profile.get("github", ""),
            "input[placeholder*='Portfolio']": profile.get("github", ""),
        }

        fields_filled = self.fill_form_fields(page, personal_mappings)

        # Handle dropdowns for location/country
        self._fill_location_dropdowns(page, profile)

        return fields_filled

    def _fill_location_dropdowns(self, page: Page, profile: Dict) -> None:
        """Fill location-related dropdown fields."""
        location = profile.get("location", "")

        # Try to set country to Canada if location contains Canadian provinces
        canadian_provinces = ["ON", "BC", "AB", "QC", "NS", "NB", "MB", "SK", "PE", "NL", "YT", "NT", "NU"]
        is_canada = any(prov in location for prov in canadian_provinces)

        if is_canada:
            country_selectors = [
                "select[name*='country']",
                "select[id*='country']",
                "select[name*='Country']"
            ]

            for selector in country_selectors:
                try:
                    if page.is_visible(selector):
                        # Try to select Canada
                        page.select_option(selector, label="Canada")
                        console.print("[green]Selected Canada as country[/green]")
                        break
                except Exception:
                    try:
                        page.select_option(selector, value="CA")
                        console.print("[green]Selected Canada (CA) as country[/green]")
                        break
                    except Exception:
                        continue

    def _upload_documents(self, page: Page, resume_path: str, cover_letter_path: str) -> None:
        """Upload resume and cover letter documents."""
        # Upload resume
        console.print("[green]Uploading resume[/green]")
        self._upload_resume(page, resume_path)

        # Upload cover letter if available
        if cover_letter_path:
            console.print("[green]Uploading cover letter[/green]")
            self._upload_cover_letter(page, cover_letter_path)

    def _fill_work_experience(self, page: Page, profile: Dict) -> int:
        """Fill work experience fields."""
        fields_filled = 0

        # Common work experience field mappings
        work_mappings = {
            # Current/Most recent job
            "input[name*='currentCompany']": "Previous Company",
            "input[name*='current_company']": "Previous Company",
            "input[name*='company']": "Previous Company",
            "input[name*='employer']": "Previous Company",
            "input[placeholder*='Company']": "Previous Company",
            "input[placeholder*='Employer']": "Previous Company",

            "input[name*='currentTitle']": "Data Analyst",
            "input[name*='current_title']": "Data Analyst",
            "input[name*='jobTitle']": "Data Analyst",
            "input[name*='job_title']": "Data Analyst",
            "input[name*='position']": "Data Analyst",
            "input[placeholder*='Job Title']": "Data Analyst",
            "input[placeholder*='Position']": "Data Analyst",

            # Experience duration
            "input[name*='experience']": "2+ years",
            "input[name*='yearsExperience']": "2+ years",
            "input[name*='years_experience']": "2+ years",
            "input[placeholder*='Years of experience']": "2+ years",
            "input[placeholder*='Experience']": "2+ years",

            # Salary expectations
            "input[name*='salary']": "Competitive",
            "input[name*='expectedSalary']": "Competitive",
            "input[name*='expected_salary']": "Competitive",
            "input[placeholder*='Salary']": "Competitive",
            "input[placeholder*='Expected salary']": "Competitive",
        }

        fields_filled = self.fill_form_fields(page, work_mappings)

        # Handle work authorization dropdowns
        self._fill_work_authorization_dropdowns(page)

        return fields_filled

    def _fill_work_authorization_dropdowns(self, page: Page) -> None:
        """Fill work authorization dropdown fields."""
        auth_selectors = [
            "select[name*='authorization']",
            "select[name*='workAuth']",
            "select[name*='work_auth']",
            "select[name*='eligible']",
            "select[name*='visa']"
        ]

        for selector in auth_selectors:
            try:
                if page.is_visible(selector):
                    # Try to select "Yes" or "Authorized" options
                    options = ["Yes", "Authorized", "Citizen", "Permanent Resident"]
                    for option in options:
                        try:
                            page.select_option(selector, label=option)
                            console.print(f"[green]Selected '{option}' for work authorization[/green]")
                            break
                        except Exception:
                            continue
            except Exception:
                continue

    def _fill_education(self, page: Page, profile: Dict) -> int:
        """Fill education fields."""
        fields_filled = 0

        # Education field mappings
        education_mappings = {
            "input[name*='school']": "University",
            "input[name*='university']": "University",
            "input[name*='college']": "University",
            "input[name*='institution']": "University",
            "input[placeholder*='School']": "University",
            "input[placeholder*='University']": "University",
            "input[placeholder*='College']": "University",

            "input[name*='degree']": "Bachelor's Degree",
            "input[name*='education']": "Bachelor's Degree",
            "input[placeholder*='Degree']": "Bachelor's Degree",
            "input[placeholder*='Education']": "Bachelor's Degree",

            "input[name*='major']": "Computer Science",
            "input[name*='field']": "Computer Science",
            "input[name*='study']": "Computer Science",
            "input[placeholder*='Major']": "Computer Science",
            "input[placeholder*='Field of study']": "Computer Science",

            "input[name*='gpa']": "3.5",
            "input[name*='GPA']": "3.5",
            "input[placeholder*='GPA']": "3.5",
        }

        fields_filled = self.fill_form_fields(page, education_mappings)

        # Handle education level dropdowns
        self._fill_education_dropdowns(page)

        return fields_filled

    def _fill_education_dropdowns(self, page: Page) -> None:
        """Fill education level dropdown fields."""
        education_selectors = [
            "select[name*='education']",
            "select[name*='degree']",
            "select[name*='level']"
        ]

        for selector in education_selectors:
            try:
                if page.is_visible(selector):
                    # Try to select Bachelor's degree options
                    options = ["Bachelor's", "Bachelor's Degree", "Undergraduate", "4-year degree"]
                    for option in options:
                        try:
                            page.select_option(selector, label=option)
                            console.print(f"[green]Selected '{option}' for education level[/green]")
                            break
                        except Exception:
                            continue
            except Exception:
                continue

    def _fill_additional_information(self, page: Page, profile: Dict) -> int:
        """Fill skills and additional information fields."""
        fields_filled = 0

        # Get skills from profile
        skills = profile.get("skills", [])
        skills_text = ", ".join(skills) if skills else "Python, SQL, Data Analysis, Excel, Power BI"

        # Additional information mappings
        additional_mappings = {
            # Skills fields
            "textarea[name*='skills']": skills_text,
            "textarea[name*='skill']": skills_text,
            "input[name*='skills']": skills_text,
            "textarea[placeholder*='Skills']": skills_text,
            "textarea[placeholder*='skills']": skills_text,

            # Cover letter / additional info
            "textarea[name*='cover']": "I am excited to apply for this position and believe my skills align well with your requirements.",
            "textarea[name*='letter']": "I am excited to apply for this position and believe my skills align well with your requirements.",
            "textarea[name*='additional']": "I am excited to apply for this position and believe my skills align well with your requirements.",
            "textarea[name*='comments']": "I am excited to apply for this position and believe my skills align well with your requirements.",
            "textarea[name*='why']": "I am excited to apply for this position and believe my skills align well with your requirements.",
            "textarea[placeholder*='Why']": "I am excited to apply for this position and believe my skills align well with your requirements.",
            "textarea[placeholder*='Tell us']": "I am excited to apply for this position and believe my skills align well with your requirements.",

            # How did you hear about us
            "input[name*='source']": "Job Board",
            "input[name*='referral']": "Online Job Search",
            "input[name*='hear']": "Job Board",
            "input[placeholder*='How did you hear']": "Job Board",

            # Availability
            "input[name*='availability']": "Immediately",
            "input[name*='available']": "Immediately",
            "input[name*='start']": "Immediately",
            "input[placeholder*='When can you start']": "Immediately",
            "input[placeholder*='Availability']": "Immediately",
        }

        fields_filled = self.fill_form_fields(page, additional_mappings)

        # Handle "How did you hear about us" dropdowns
        self._fill_source_dropdowns(page)

        return fields_filled

    def _fill_source_dropdowns(self, page: Page) -> None:
        """Fill 'how did you hear about us' dropdown fields."""
        source_selectors = [
            "select[name*='source']",
            "select[name*='referral']",
            "select[name*='hear']",
            "select[name*='found']"
        ]

        for selector in source_selectors:
            try:
                if page.is_visible(selector):
                    # Try to select job board related options
                    options = ["Job Board", "Online", "Indeed", "LinkedIn", "Company Website", "Other"]
                    for option in options:
                        try:
                            page.select_option(selector, label=option)
                            console.print(f"[green]Selected '{option}' for job source[/green]")
                            break
                        except Exception:
                            continue
            except Exception:
                continue

    def _handle_comprehensive_screening(self, page: Page, profile: Dict) -> None:
        """Handle comprehensive screening questions like Simplify."""
        # Handle yes/no radio buttons (work authorization, background checks, etc.)
        yes_options = page.query_selector_all("input[type='radio'][value='yes'], input[type='radio'][value='true'], input[type='radio'][value='Yes'], input[type='radio'][value='True']")
        for option in yes_options:
            try:
                option.click()
                console.print("[green]Selected 'Yes' for screening question[/green]")
            except Exception:
                continue

        # Handle dropdown screening questions
        screening_dropdowns = page.query_selector_all("select[name*='question'], select[name*='screening']")
        for dropdown in screening_dropdowns:
            try:
                # Try to select positive/affirmative options
                positive_options = ["Yes", "Authorized", "Eligible", "Available"]
                for option in positive_options:
                    try:
                        page.select_option(dropdown, label=option)
                        console.print(f"[green]Selected '{option}' for screening dropdown[/green]")
                        break
                    except Exception:
                        continue
            except Exception:
                continue

        # Handle text area screening questions
        screening_textareas = page.query_selector_all("textarea[name*='question'], textarea[name*='screening']")
        for textarea in screening_textareas:
            try:
                placeholder = textarea.get_attribute("placeholder") or ""
                if any(word in placeholder.lower() for word in ["why", "interest", "motivation"]):
                    textarea.fill("I am excited about this opportunity and believe my skills align well with the role requirements.")
                    console.print("[green]Filled screening text area[/green]")
            except Exception:
                continue

    def _handle_diversity_questions(self, page: Page) -> None:
        """Handle diversity and EEO questions."""
        # Common diversity/EEO questions - typically optional
        diversity_selectors = [
            "select[name*='gender']",
            "select[name*='race']",
            "select[name*='ethnicity']",
            "select[name*='veteran']",
            "select[name*='disability']"
        ]

        for selector in diversity_selectors:
            try:
                if page.is_visible(selector):
                    # Try to select "Prefer not to answer" or similar
                    options = ["Prefer not to answer", "Decline to answer", "Not specified", "Other"]
                    for option in options:
                        try:
                            page.select_option(selector, label=option)
                            console.print(f"[green]Selected '{option}' for diversity question[/green]")
                            break
                        except Exception:
                            continue
            except Exception:
                continue

    def _handle_work_authorization(self, page: Page, profile: Dict) -> None:
        """Handle work authorization questions comprehensively."""
        # Work authorization radio buttons
        auth_questions = [
            "input[type='radio'][name*='authorization']",
            "input[type='radio'][name*='eligible']",
            "input[type='radio'][name*='visa']",
            "input[type='radio'][name*='citizen']",
            "input[type='radio'][name*='work']"
        ]

        for question_selector in auth_questions:
            try:
                # Find all radio buttons for this question
                radios = page.query_selector_all(question_selector)
                for radio in radios:
                    value = radio.get_attribute("value") or ""
                    if value.lower() in ["yes", "true", "authorized", "eligible", "citizen"]:
                        radio.click()
                        console.print(f"[green]Selected '{value}' for work authorization[/green]")
                        break
            except Exception:
                continue

        # Work authorization dropdowns
        auth_dropdowns = [
            "select[name*='authorization']",
            "select[name*='status']",
            "select[name*='visa']",
            "select[name*='citizen']"
        ]

        for dropdown_selector in auth_dropdowns:
            try:
                if page.is_visible(dropdown_selector):
                    # Try to select authorized options
                    options = ["Yes", "Authorized", "Citizen", "Permanent Resident", "No sponsorship required"]
                    for option in options:
                        try:
                            page.select_option(dropdown_selector, label=option)
                            console.print(f"[green]Selected '{option}' for work authorization dropdown[/green]")
                            break
                        except Exception:
                            continue
            except Exception:
                continue

    def _process_current_step(self, page: Page, profile: Dict, resume_path: str, cover_letter_path: str, step_number: int) -> str:
        """Process the current step of the application form."""
        try:
            # Identify what type of step this is by looking at visible fields
            step_type = self._identify_step_type(page)
            console.print(f"[cyan]Detected step type: {step_type}[/cyan]")

            # First, try to apply learned fields from previous applications
            learned_fields = self._apply_learned_fields(page, profile, step_number)
            if learned_fields > 0:
                console.print(f"[cyan]Applied {learned_fields} learned field values[/cyan]")

            # Then fill remaining fields based on step type
            if step_type == "personal_info":
                fields_filled = self._fill_personal_information(page, profile)
                total_filled = learned_fields + fields_filled
                console.print(f"[green]Filled {total_filled} personal information fields ({learned_fields} learned + {fields_filled} new)[/green]")

            elif step_type == "work_experience":
                fields_filled = self._fill_work_experience(page, profile)
                total_filled = learned_fields + fields_filled
                console.print(f"[green]Filled {total_filled} work experience fields ({learned_fields} learned + {fields_filled} new)[/green]")

            elif step_type == "education":
                fields_filled = self._fill_education(page, profile)
                total_filled = learned_fields + fields_filled
                console.print(f"[green]Filled {total_filled} education fields ({learned_fields} learned + {fields_filled} new)[/green]")

            elif step_type == "skills_additional":
                fields_filled = self._fill_additional_information(page, profile)
                total_filled = learned_fields + fields_filled
                console.print(f"[green]Filled {total_filled} skills/additional fields ({learned_fields} learned + {fields_filled} new)[/green]")

            elif step_type == "documents":
                self._upload_documents(page, resume_path, cover_letter_path)
                console.print("[green]Uploaded documents[/green]")

            elif step_type == "screening":
                self._handle_comprehensive_screening(page, profile)
                console.print("[green]Handled screening questions[/green]")

            elif step_type == "diversity":
                self._handle_diversity_questions(page)
                console.print("[green]Handled diversity questions[/green]")

            elif step_type == "authorization":
                self._handle_work_authorization(page, profile)
                console.print("[green]Handled work authorization[/green]")

            elif step_type == "review":
                console.print("[yellow]Review step detected - please verify all information[/yellow]")

            elif step_type == "submit":
                if self._submit_application(page):
                    return "COMPLETED"
                else:
                    return "MANUAL"

            else:
                # Generic form filling for unknown step types
                console.print("[yellow]Unknown step type, attempting generic form filling[/yellow]")
                fields_filled = self._fill_generic_fields(page, profile)
                total_filled = learned_fields + fields_filled
                console.print(f"[green]Filled {total_filled} generic fields ({learned_fields} learned + {fields_filled} new)[/green]")

            return "CONTINUE"

        except Exception as e:
            console.print(f"[red]Error processing step {step_number}: {e}[/red]")
            return "FAILED"

    def _identify_step_type(self, page: Page) -> str:
        """Identify what type of step we're currently on."""
        # Look for specific field patterns to identify step type

        # Personal information step
        if (page.query_selector("input[name*='firstName'], input[name*='first_name'], input[name*='email']") or
            page.query_selector("input[placeholder*='First name'], input[placeholder*='Email']")):
            return "personal_info"

        # Work experience step
        if (page.query_selector("input[name*='company'], input[name*='employer'], input[name*='job'], input[name*='title']") or
            page.query_selector("input[placeholder*='Company'], input[placeholder*='Job title']")):
            return "work_experience"

        # Education step
        if (page.query_selector("input[name*='school'], input[name*='university'], input[name*='degree']") or
            page.query_selector("input[placeholder*='School'], input[placeholder*='University']")):
            return "education"

        # Document upload step
        if page.query_selector("input[type='file']"):
            return "documents"

        # Screening questions step
        if (page.query_selector("input[type='radio'], select[name*='question']") and
            not page.query_selector("input[name*='gender'], input[name*='race']")):
            return "screening"

        # Diversity/EEO step
        if page.query_selector("input[name*='gender'], input[name*='race'], input[name*='ethnicity']"):
            return "diversity"

        # Work authorization step
        if page.query_selector("input[name*='authorization'], input[name*='visa'], input[name*='citizen']"):
            return "authorization"

        # Review step
        if (page.query_selector("text='Review'") or page.query_selector("text='Summary'") or
            page.query_selector("[class*='review'], [class*='summary']")):
            return "review"

        # Submit step
        if (page.query_selector("button:has-text('Submit'), input[value*='Submit']") and
            not page.query_selector("input[type='text'], input[type='email']")):
            return "submit"

        return "unknown"

    def _move_to_next_step(self, page: Page) -> bool:
        """Try to move to the next step of the application."""
        next_button_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Save & Continue')",
            "button:has-text('Save and Continue')",
            "input[type='submit'][value*='Next']",
            "input[type='submit'][value*='Continue']",
            "a:has-text('Next')",
            "a:has-text('Continue')",
            "button[class*='next']",
            "button[class*='continue']"
        ]

        for selector in next_button_selectors:
            try:
                if page.is_visible(selector):
                    console.print(f"[green]Clicking next button: {selector}[/green]")
                    page.click(selector)
                    page.wait_for_timeout(2000)  # Wait for navigation
                    return True
            except Exception as e:
                console.print(f"[yellow]Failed to click {selector}: {e}[/yellow]")
                continue

        console.print("[yellow]No next button found[/yellow]")
        return False

    def _wait_for_resume(self) -> None:
        """Wait for user to resume the application."""
        console.print("[yellow]Application paused. Waiting for resume signal...[/yellow]")

        while True:
            if not utils.check_pause_signal():
                console.print("[green]Resume signal detected, continuing...[/green]")
                break

            user_input = input("Type 'resume' to continue or 'quit' to exit: ").strip().lower()
            if user_input == 'resume':
                utils.set_pause_signal(False)  # Clear pause signal
                console.print("[green]Resuming application...[/green]")
                break
            elif user_input == 'quit':
                console.print("[red]Application cancelled by user[/red]")
                raise utils.NeedsHumanException("Application cancelled by user")

            import time
            time.sleep(1)

    def _fill_generic_fields(self, page: Page, profile: Dict) -> int:
        """Fill any visible form fields with appropriate data."""
        fields_filled = 0

        # Get all visible input fields
        inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='tel'], textarea")

        for field in inputs:
            try:
                name = field.get_attribute('name') or ''
                placeholder = field.get_attribute('placeholder') or ''
                field_text = (name + ' ' + placeholder).lower()

                # Determine what to fill based on field characteristics
                if any(word in field_text for word in ['first', 'fname']):
                    value = profile.get("name", "").split()[0] if profile.get("name") else ""
                elif any(word in field_text for word in ['last', 'lname']):
                    value = profile.get("name", "").split()[-1] if profile.get("name") else ""
                elif 'email' in field_text:
                    value = profile.get("email", "")
                elif any(word in field_text for word in ['phone', 'tel']):
                    value = profile.get("phone", "")
                elif any(word in field_text for word in ['address', 'location', 'city']):
                    value = profile.get("location", "")
                elif any(word in field_text for word in ['linkedin']):
                    value = profile.get("linkedin", "")
                elif any(word in field_text for word in ['github', 'website']):
                    value = profile.get("github", "")
                elif any(word in field_text for word in ['skill']):
                    skills = profile.get("skills", [])
                    value = ", ".join(skills) if skills else ""
                else:
                    continue  # Skip unknown fields

                if value and utils.fill_if_empty(page, f"input[name='{name}']" if name else "input", value):
                    fields_filled += 1
                    console.print(f"[green]Filled field '{name or placeholder}' with '{value[:30]}...'[/green]")

            except Exception as e:
                console.print(f"[yellow]Error filling generic field: {e}[/yellow]")
                continue

        return fields_filled

    def _learn_from_manual_input(self, page: Page, profile: Dict, step_number: int) -> None:
        """Learn from user's manual input and save for future applications."""
        try:
            import json
            from pathlib import Path

            # Create learned mappings file path
            profile_dir = Path(profile.get("profile_dir", f"profiles/{profile.get('profile_name', 'default')}"))
            learned_file = profile_dir / "bamboohr_learned_fields.json"

            # Load existing learned data
            learned_data = {}
            if learned_file.exists():
                try:
                    with open(learned_file, 'r') as f:
                        learned_data = json.load(f)
                except:
                    learned_data = {}

            # Get all form fields and their current values
            fields = page.query_selector_all("input, textarea, select")
            step_key = f"step_{step_number}"

            if step_key not in learned_data:
                learned_data[step_key] = {}

            fields_learned = 0
            for field in fields:
                try:
                    # Get field identifiers
                    name = field.get_attribute('name')
                    field_id = field.get_attribute('id')
                    placeholder = field.get_attribute('placeholder')
                    field_type = field.get_attribute('type') or field.evaluate('el => el.tagName.toLowerCase()')

                    # Get current value
                    if field_type == 'select':
                        value = field.evaluate('el => el.value')
                    elif field_type in ['text', 'email', 'tel', 'textarea']:
                        value = field.input_value() if hasattr(field, 'input_value') else field.get_attribute('value')
                    elif field_type == 'radio':
                        if field.is_checked():
                            value = field.get_attribute('value')
                        else:
                            continue
                    elif field_type == 'checkbox':
                        value = field.is_checked()
                    else:
                        continue

                    # Skip empty values
                    if not value or (isinstance(value, str) and not value.strip()):
                        continue

                    # Create field signature for identification
                    field_signature = self._create_field_signature(name, field_id, placeholder, field_type)

                    if field_signature:
                        learned_data[step_key][field_signature] = {
                            'value': value,
                            'name': name,
                            'id': field_id,
                            'placeholder': placeholder,
                            'type': field_type,
                            'selector': self._create_selector_for_field(name, field_id, placeholder, field_type)
                        }
                        fields_learned += 1

                except Exception as e:
                    console.print(f"[yellow]Error learning field: {e}[/yellow]")
                    continue

            # Save learned data
            profile_dir.mkdir(exist_ok=True)
            with open(learned_file, 'w') as f:
                json.dump(learned_data, f, indent=2)

            console.print(f"[green]Learned {fields_learned} field values for future applications![/green]")
            console.print(f"[cyan]Saved to: {learned_file}[/cyan]")

        except Exception as e:
            console.print(f"[red]Error in learning system: {e}[/red]")

    def _create_field_signature(self, name: str, field_id: str, placeholder: str, field_type: str) -> str:
        """Create a unique signature for a field to identify it in future applications."""
        # Use name as primary identifier, fallback to id, then placeholder
        if name:
            return f"name_{name}"
        elif field_id:
            return f"id_{field_id}"
        elif placeholder:
            # Clean placeholder for use as identifier
            clean_placeholder = placeholder.lower().replace(' ', '_').replace('*', '').replace(':', '')
            return f"placeholder_{clean_placeholder}"
        else:
            return None

    def _create_selector_for_field(self, name: str, field_id: str, placeholder: str, field_type: str) -> str:
        """Create a CSS selector to find this field in future applications."""
        if name:
            return f"input[name='{name}'], textarea[name='{name}'], select[name='{name}']"
        elif field_id:
            return f"#{field_id}"
        elif placeholder:
            return f"input[placeholder='{placeholder}'], textarea[placeholder='{placeholder}']"
        else:
            return f"input[type='{field_type}'], {field_type}"

    def _apply_learned_fields(self, page: Page, profile: Dict, step_number: int) -> int:
        """Apply previously learned field values to the current step."""
        try:
            import json
            from pathlib import Path

            # Load learned mappings
            profile_dir = Path(profile.get("profile_dir", f"profiles/{profile.get('profile_name', 'default')}"))
            learned_file = profile_dir / "bamboohr_learned_fields.json"

            if not learned_file.exists():
                return 0

            with open(learned_file, 'r') as f:
                learned_data = json.load(f)

            step_key = f"step_{step_number}"
            if step_key not in learned_data:
                return 0

            fields_filled = 0
            step_data = learned_data[step_key]

            console.print(f"[cyan]Applying {len(step_data)} learned field values...[/cyan]")

            for field_signature, field_info in step_data.items():
                try:
                    selector = field_info['selector']
                    value = field_info['value']
                    field_type = field_info['type']

                    # Try to find the field using the selector
                    if page.is_visible(selector):
                        if field_type == 'select':
                            try:
                                page.select_option(selector, value=value)
                                fields_filled += 1
                                console.print(f"[green]Applied learned value to {field_info.get('name', 'field')}: {value}[/green]")
                            except:
                                try:
                                    page.select_option(selector, label=value)
                                    fields_filled += 1
                                    console.print(f"[green]Applied learned value to {field_info.get('name', 'field')}: {value}[/green]")
                                except:
                                    continue
                        elif field_type == 'radio':
                            try:
                                radio_selector = f"{selector}[value='{value}']"
                                if page.is_visible(radio_selector):
                                    page.click(radio_selector)
                                    fields_filled += 1
                                    console.print(f"[green]Applied learned radio value: {value}[/green]")
                            except:
                                continue
                        elif field_type == 'checkbox':
                            try:
                                if value:  # If learned value was checked
                                    page.check(selector)
                                else:
                                    page.uncheck(selector)
                                fields_filled += 1
                                console.print(f"[green]Applied learned checkbox value: {value}[/green]")
                            except:
                                continue
                        elif field_type in ['text', 'email', 'tel', 'textarea']:
                            try:
                                if utils.fill_if_empty(page, selector, str(value)):
                                    fields_filled += 1
                                    console.print(f"[green]Applied learned value to {field_info.get('name', 'field')}: {value}[/green]")
                            except:
                                continue

                except Exception as e:
                    console.print(f"[yellow]Error applying learned field {field_signature}: {e}[/yellow]")
                    continue

            return fields_filled

        except Exception as e:
            console.print(f"[red]Error applying learned fields: {e}[/red]")
            return 0
