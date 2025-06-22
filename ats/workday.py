"""
Workday ATS submitter implementation.
Handles job application automation for Workday-based job portals.
"""

from typing import Dict

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_submitter import BaseSubmitter
import utils
import utils

console = Console()

class WorkdaySubmitter(BaseSubmitter):
    """
    Submitter for Workday ATS.
    Handles automation of job applications on Workday-based portals.
    """
    
    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Submit an application to Workday ATS with dynamic form filling.

        Args:
            job: Job dictionary with details
            profile: User profile dictionary
            resume_path: Path to the resume file
            cover_letter_path: Path to the cover letter file

        Returns:
            Status string (e.g., "Applied", "Failed", "Manual")
        """
        # Create a new page
        page = self.ctx.new_page()

        try:
            # Navigate to the job URL
            console.print(f"[green]Navigating to job URL: {job['url']}[/green]")
            page.goto(job["url"], timeout=30000)
            self.wait_for_navigation(page)

            # Check for CAPTCHA
            self.check_for_captcha(page)

            # Auto-login using saved session/credentials
            if self.handle_login(page, profile, job["url"]):
                console.print("[green]Login completed[/green]")
            else:
                console.print("[yellow]Manual login may be required[/yellow]")

            # Wait for page to fully load after login
            page.wait_for_timeout(3000)

            # Find and click Apply button
            if not self._click_apply_button_enhanced(page):
                console.print("[yellow]Could not find Apply button[/yellow]")
                return "Manual"

            # Dynamic form filling - go through all form fields line by line
            return self._dynamic_form_filling(page, profile, resume_path, cover_letter_path)
            
        except utils.NeedsHumanException:
            console.print("[yellow]Human intervention required[/yellow]")
            self.wait_for_human(page, "Please complete the application manually")
            return "Manual"
        
        except Exception as e:
            console.print(f"[bold red]Workday submission error: {e}[/bold red]")
            return "Failed"
        
        finally:
            # Close the page
            page.close()

    def _handle_login_with_user_input(self, page, job_url: str) -> bool:
        """Enhanced login handling with user interaction and auto-fill."""
        try:
            # Check if login is needed
            login_indicators = [
                "text='Sign In'",
                "text='Login'",
                "text='Log In'",
                "button:has-text('Sign In')",
                "a:has-text('Sign In')",
                "input[type='email']",
                "input[type='password']",
                "input[name*='username']",
                "input[name*='email']"
            ]

            needs_login = any(page.is_visible(selector) for selector in login_indicators)

            if not needs_login:
                console.print("[green]Already logged in or no login required[/green]")
                return True

            console.print("[yellow]Login required detected[/yellow]")

            # Ask user about login preference
            console.print("\n[bold cyan]Login Options:[/bold cyan]")
            console.print("1. Auto-fill with default credentials")
            console.print("2. Manual login")
            console.print("3. Skip login (if already logged in elsewhere)")

            choice = input("Choose option (1/2/3): ").strip()

            if choice == "1":
                return self._auto_fill_login(page, job_url)
            elif choice == "2":
                return self._manual_login(page)
            else:
                console.print("[yellow]Skipping login - assuming already logged in[/yellow]")
                return True

        except Exception as e:
            console.print(f"[red]Error in login handling: {e}[/red]")
            return False

    def _auto_fill_login(self, page, job_url: str) -> bool:
        """Auto-fill login with default credentials."""
        try:
            console.print("[cyan]Auto-filling login credentials...[/cyan]")

            # Extract domain for password pattern
            domain = self._extract_domain_for_password(job_url)
            default_email = "Nirajan.tech@gmail.com"
            default_password = f"pwd@{domain}99"

            console.print(f"[cyan]Using email: {default_email}[/cyan]")
            console.print(f"[cyan]Using password pattern: pwd@{domain}99[/cyan]")

            # Fill email field
            email_selectors = [
                "input[type='email']",
                "input[name*='email']",
                "input[name*='username']",
                "input[name*='user']",
                "input[id*='email']",
                "input[id*='username']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']"
            ]

            email_filled = False
            for selector in email_selectors:
                if page.is_visible(selector):
                    page.fill(selector, default_email)
                    console.print(f"[green]Filled email field: {selector}[/green]")
                    email_filled = True
                    break

            # Fill password field
            password_selectors = [
                "input[type='password']",
                "input[name*='password']",
                "input[name*='pwd']",
                "input[id*='password']",
                "input[placeholder*='password']",
                "input[placeholder*='Password']"
            ]

            password_filled = False
            for selector in password_selectors:
                if page.is_visible(selector):
                    page.fill(selector, default_password)
                    console.print(f"[green]Filled password field: {selector}[/green]")
                    password_filled = True
                    break

            if not email_filled or not password_filled:
                console.print("[yellow]Could not find all login fields, switching to manual[/yellow]")
                return self._manual_login(page)

            # Try to click login button
            login_button_selectors = [
                "button:has-text('Sign In')",
                "button:has-text('Login')",
                "button:has-text('Log In')",
                "input[type='submit']",
                "button[type='submit']",
                "a:has-text('Sign In')"
            ]

            for selector in login_button_selectors:
                if page.is_visible(selector):
                    console.print(f"[green]Clicking login button: {selector}[/green]")
                    page.click(selector)
                    break

            # Wait for login to complete
            page.wait_for_timeout(5000)

            # Check if login was successful
            if self._check_login_success(page):
                console.print("[green]Auto-login successful![/green]")
                return True
            else:
                console.print("[yellow]Auto-login may have failed, please verify manually[/yellow]")
                return self._manual_login(page)

        except Exception as e:
            console.print(f"[red]Error in auto-fill login: {e}[/red]")
            return self._manual_login(page)

    def _extract_domain_for_password(self, url: str) -> str:
        """Extract domain name for password pattern."""
        try:
            # Extract domain from URL for password pattern
            if "myworkdayjobs" in url:
                return "Myworkdayjobs"
            elif "workday" in url:
                return "Workday"
            elif "td.wd3" in url:
                return "TDBank"
            else:
                # Generic extraction
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.split('.')[0]
                return domain.capitalize()
        except:
            return "Workday"

    def _manual_login(self, page) -> bool:
        """Handle manual login with user guidance."""
        console.print("[yellow]Please complete the login manually in the browser[/yellow]")
        console.print("[yellow]After logging in successfully, press Enter to continue...[/yellow]")
        input()

        if self._check_login_success(page):
            console.print("[green]Manual login successful![/green]")
            return True
        else:
            console.print("[yellow]Login status unclear, continuing anyway...[/yellow]")
            return True

    def _check_login_success(self, page) -> bool:
        """Check if login was successful."""
        try:
            # Look for indicators that login was successful
            success_indicators = [
                "text='Apply'",
                "text='Dashboard'",
                "text='Profile'",
                "text='My Applications'",
                "button:has-text('Apply')",
                "[data-automation-id*='apply']"
            ]

            # Wait a bit for page to load
            page.wait_for_timeout(3000)

            for indicator in success_indicators:
                if page.is_visible(indicator):
                    return True

            # Check if we're still on login page
            login_indicators = [
                "input[type='password']",
                "text='Sign In'",
                "text='Login'"
            ]

            for indicator in login_indicators:
                if page.is_visible(indicator):
                    return False

            # If no clear indicators, assume success
            return True

        except:
            return True

    def _click_apply_button_enhanced(self, page) -> bool:
        """Enhanced Apply button detection and clicking."""
        apply_selectors = [
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "button:has-text('Apply Now')",
            "a:has-text('Apply Now')",
            "button:has-text('Apply for this Job')",
            "[data-automation-id*='apply']",
            ".apply-button",
            "#apply-button",
            "button[class*='apply']"
        ]

        for selector in apply_selectors:
            try:
                if page.is_visible(selector):
                    console.print(f"[green]Clicking Apply button: {selector}[/green]")
                    page.click(selector)
                    page.wait_for_timeout(3000)  # Wait for navigation
                    return True
            except Exception as e:
                console.print(f"[yellow]Failed to click {selector}: {e}[/yellow]")
                continue

        console.print("[yellow]No Apply button found[/yellow]")
        return False

    def _dynamic_form_filling(self, page, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Dynamic form filling that goes through all form fields line by line.
        This is the main intelligent form filling engine.
        """
        console.print("[bold cyan]Starting dynamic form filling process[/bold cyan]")

        try:
            step_count = 0
            max_steps = 15  # Safety limit

            while step_count < max_steps:
                step_count += 1
                console.print(f"\n[bold blue]═══ FORM STEP {step_count} ═══[/bold blue]")

                # Wait for page to stabilize
                page.wait_for_timeout(2000)

                # Analyze current page and fill all visible fields
                fields_filled = self._analyze_and_fill_current_page(page, profile, resume_path, cover_letter_path)
                console.print(f"[green]Filled {fields_filled} fields on this step[/green]")

                # Ask user if everything looks correct
                console.print(f"[yellow]Step {step_count} completed. Please review the filled fields.[/yellow]")
                user_input = input("Continue to next step? (y/n/manual): ").strip().lower()

                if user_input == 'n':
                    console.print("[yellow]Please make corrections manually, then press Enter...[/yellow]")
                    input()
                elif user_input == 'manual':
                    console.print("[yellow]Switching to manual mode[/yellow]")
                    return "Manual"

                # Try to move to next step
                if not self._move_to_next_step(page):
                    # No more steps, try to submit
                    console.print("[cyan]No more steps found, attempting to submit...[/cyan]")
                    if self._submit_application_enhanced(page):
                        return "Applied"
                    else:
                        console.print("[yellow]Could not submit automatically[/yellow]")
                        return "Manual"

            console.print("[yellow]Maximum steps reached, attempting final submission...[/yellow]")
            if self._submit_application_enhanced(page):
                return "Applied"
            else:
                return "Manual"

        except Exception as e:
            console.print(f"[red]Error in dynamic form filling: {e}[/red]")
            return "Failed"

    def _analyze_and_fill_current_page(self, page, profile: Dict, resume_path: str, cover_letter_path: str) -> int:
        """
        Analyze the current page and intelligently fill all visible form fields.
        This goes line by line through every field it can find.
        """
        fields_filled = 0

        console.print("[cyan]Analyzing current page for form fields...[/cyan]")

        # 1. Handle file uploads first
        fields_filled += self._handle_file_uploads(page, resume_path, cover_letter_path)

        # 2. Fill text inputs
        fields_filled += self._fill_text_inputs(page, profile)

        # 3. Handle dropdowns/selects
        fields_filled += self._fill_dropdowns(page, profile)

        # 4. Handle radio buttons
        fields_filled += self._fill_radio_buttons(page, profile)

        # 5. Handle checkboxes
        fields_filled += self._fill_checkboxes(page, profile)

        # 6. Fill text areas
        fields_filled += self._fill_text_areas(page, profile)

        return fields_filled

    def _handle_file_uploads(self, page, resume_path: str, cover_letter_path: str) -> int:
        """Handle all file upload fields on the current page."""
        uploads_handled = 0

        # Find all file input fields
        file_inputs = page.query_selector_all("input[type='file']")

        for i, file_input in enumerate(file_inputs):
            try:
                # Get field context to determine what type of file is expected
                field_name = file_input.get_attribute("name") or ""
                field_id = file_input.get_attribute("id") or ""

                # Look for labels or nearby text to understand the field
                label_text = ""
                try:
                    # Try to find associated label
                    if field_id:
                        label = page.query_selector(f"label[for='{field_id}']")
                        if label:
                            label_text = label.inner_text().lower()

                    # If no label, look for nearby text
                    if not label_text:
                        parent = file_input.query_selector("..")
                        if parent:
                            label_text = parent.inner_text().lower()[:100]  # First 100 chars
                except:
                    pass

                console.print(f"[cyan]File upload field {i+1}: name='{field_name}', id='{field_id}', context='{label_text[:50]}'[/cyan]")

                # Determine which file to upload based on context
                if any(keyword in (field_name + field_id + label_text).lower() for keyword in ['resume', 'cv']):
                    console.print(f"[green]Uploading resume to field {i+1}[/green]")
                    file_input.set_input_files(resume_path)
                    uploads_handled += 1
                elif any(keyword in (field_name + field_id + label_text).lower() for keyword in ['cover', 'letter']):
                    if cover_letter_path:
                        console.print(f"[green]Uploading cover letter to field {i+1}[/green]")
                        file_input.set_input_files(cover_letter_path)
                        uploads_handled += 1
                else:
                    # Ask user what to upload
                    console.print(f"[yellow]Unknown file upload field {i+1}. What should be uploaded?[/yellow]")
                    console.print("1. Resume")
                    console.print("2. Cover Letter")
                    console.print("3. Skip")
                    choice = input("Choose (1/2/3): ").strip()

                    if choice == "1":
                        file_input.set_input_files(resume_path)
                        uploads_handled += 1
                    elif choice == "2" and cover_letter_path:
                        file_input.set_input_files(cover_letter_path)
                        uploads_handled += 1

            except Exception as e:
                console.print(f"[yellow]Error handling file upload {i+1}: {e}[/yellow]")
                continue

        return uploads_handled

    def _fill_text_inputs(self, page, profile: Dict) -> int:
        """Fill all text input fields with appropriate data from profile."""
        fields_filled = 0

        # Get all text input fields
        text_inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='tel'], input:not([type])")

        console.print(f"[cyan]Found {len(text_inputs)} text input fields[/cyan]")

        for i, input_field in enumerate(text_inputs):
            try:
                # Skip if field is already filled
                current_value = input_field.input_value()
                if current_value and current_value.strip():
                    console.print(f"[yellow]Field {i+1} already has value: '{current_value[:30]}...'[/yellow]")
                    continue

                # Get field identifiers
                field_name = input_field.get_attribute("name") or ""
                field_id = input_field.get_attribute("id") or ""
                placeholder = input_field.get_attribute("placeholder") or ""

                # Get label text
                label_text = self._get_field_label(page, input_field, field_id)

                # Combine all context for analysis
                field_context = (field_name + " " + field_id + " " + placeholder + " " + label_text).lower()

                console.print(f"[cyan]Text field {i+1}: context='{field_context[:60]}...'[/cyan]")

                # Determine what to fill based on context
                value = self._determine_field_value(field_context, profile)

                if value:
                    input_field.fill(value)
                    console.print(f"[green]Filled field {i+1} with: '{value}'[/green]")
                    fields_filled += 1
                else:
                    console.print(f"[yellow]No value determined for field {i+1}[/yellow]")

            except Exception as e:
                console.print(f"[yellow]Error filling text field {i+1}: {e}[/yellow]")
                continue

        return fields_filled

    def _get_field_label(self, page, field, field_id: str) -> str:
        """Get the label text for a form field."""
        try:
            # Try to find associated label
            if field_id:
                label = page.query_selector(f"label[for='{field_id}']")
                if label:
                    return label.inner_text()

            # Look for nearby label or text
            parent = field.query_selector("..")
            if parent:
                # Look for label in parent
                label = parent.query_selector("label")
                if label:
                    return label.inner_text()

                # Get parent text (first 100 chars)
                parent_text = parent.inner_text()
                return parent_text[:100] if parent_text else ""

            return ""
        except:
            return ""

    def _determine_field_value(self, field_context: str, profile: Dict) -> str:
        """
        Determine what value to fill based on field context and profile.
        This is the intelligence that maps field context to profile data.
        """
        # Get name components
        full_name = profile.get("name", "")
        name_parts = full_name.split() if full_name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""

        # Name fields
        if any(keyword in field_context for keyword in ['first name', 'firstname', 'first_name', 'fname']):
            return first_name
        elif any(keyword in field_context for keyword in ['last name', 'lastname', 'last_name', 'lname', 'surname']):
            return last_name
        elif any(keyword in field_context for keyword in ['middle name', 'middlename', 'middle_name', 'mname']):
            return middle_name
        elif any(keyword in field_context for keyword in ['full name', 'fullname', 'full_name', 'name']) and 'first' not in field_context and 'last' not in field_context:
            return full_name

        # Contact fields
        elif any(keyword in field_context for keyword in ['email', 'e-mail', 'mail']):
            return profile.get("email", "")
        elif any(keyword in field_context for keyword in ['phone', 'telephone', 'mobile', 'cell']):
            return profile.get("phone", "")

        # Address fields
        elif any(keyword in field_context for keyword in ['address', 'street', 'location', 'city']):
            return profile.get("location", "")
        elif any(keyword in field_context for keyword in ['postal', 'zip', 'postcode']):
            # Extract postal code from location if available
            location = profile.get("location", "")
            # Simple regex for Canadian postal codes
            import re
            postal_match = re.search(r'[A-Z]\d[A-Z]\s?\d[A-Z]\d', location)
            return postal_match.group() if postal_match else ""

        # Professional fields
        elif any(keyword in field_context for keyword in ['linkedin', 'linked in']):
            return profile.get("linkedin", "")
        elif any(keyword in field_context for keyword in ['github', 'git hub']):
            return profile.get("github", "")
        elif any(keyword in field_context for keyword in ['website', 'portfolio', 'url']):
            return profile.get("github", "")  # Use GitHub as website

        # Work fields
        elif any(keyword in field_context for keyword in ['company', 'employer', 'current job', 'current position']):
            return "Previous Company"  # Generic value
        elif any(keyword in field_context for keyword in ['job title', 'position', 'role', 'title']) and 'job' in field_context:
            return "Data Analyst"  # Based on your profile
        elif any(keyword in field_context for keyword in ['salary', 'compensation', 'pay']):
            return "Competitive"
        elif any(keyword in field_context for keyword in ['experience', 'years']):
            return "2+ years"

        # Education fields
        elif any(keyword in field_context for keyword in ['school', 'university', 'college', 'education']):
            return "University"
        elif any(keyword in field_context for keyword in ['degree', 'qualification']):
            return "Bachelor's Degree"
        elif any(keyword in field_context for keyword in ['major', 'field of study', 'subject']):
            return "Computer Science"
        elif any(keyword in field_context for keyword in ['gpa', 'grade']):
            return "3.5"

        # Other common fields
        elif any(keyword in field_context for keyword in ['how did you hear', 'source', 'referral']):
            return "Job Board"
        elif any(keyword in field_context for keyword in ['availability', 'start date', 'when can you start']):
            return "Immediately"

        return ""  # No match found
