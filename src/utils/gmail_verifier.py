"""
Gmail Verifier Module
Provides Gmail verification and email checking functionality.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class GmailVerifier:
    """Verifies Gmail accounts and checks email functionality."""

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.console = Console()
        self.email = profile.get("email", "")
        self.password = profile.get("email_password", "")

    def verify_email_format(self, email: str) -> bool:
        """Verify if email format is valid."""
        if not email:
            return False

        # Basic email format validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def verify_gmail_account(self, email: str = None, password: str = None) -> Dict[str, Any]:
        """Verify Gmail account credentials."""
        email_to_verify = email or self.email
        password_to_verify = password or self.password

        result = {"valid": False, "error": None, "capabilities": []}

        if not email_to_verify or not password_to_verify:
            result["error"] = "Email or password not provided"
            return result

        if not self.verify_email_format(email_to_verify):
            result["error"] = "Invalid email format"
            return result

        if not email_to_verify.endswith("@gmail.com"):
            result["error"] = "Only Gmail accounts are supported"
            return result

        # Try to connect to Gmail SMTP
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email_to_verify, password_to_verify)
            server.quit()

            result["valid"] = True
            result["capabilities"] = ["smtp", "send_email"]

        except smtplib.SMTPAuthenticationError:
            result["error"] = "Invalid credentials"
        except smtplib.SMTPException as e:
            result["error"] = f"SMTP error: {str(e)}"
        except Exception as e:
            result["error"] = f"Connection error: {str(e)}"

        return result

    def send_test_email(self, to_email: str = None) -> Dict[str, Any]:
        """Send a test email to verify functionality."""
        result = {"sent": False, "error": None, "message_id": None}

        if not self.email or not self.password:
            result["error"] = "Email credentials not configured"
            return result

        # Verify account first
        verification = self.verify_gmail_account()
        if not verification["valid"]:
            result["error"] = verification["error"]
            return result

        to_email = to_email or self.email  # Send to self if no recipient specified

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = "AutoJobAgent Test Email"

            body = """
            This is a test email from AutoJobAgent.
            
            If you received this email, your Gmail integration is working correctly.
            
            Best regards,
            AutoJobAgent System
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email, self.password)

            text = msg.as_string()
            server.sendmail(self.email, to_email, text)
            server.quit()

            result["sent"] = True
            result["message_id"] = f"test_{self.get_current_timestamp()}"

        except Exception as e:
            result["error"] = f"Failed to send email: {str(e)}"

        return result

    def check_email_quota(self) -> Dict[str, Any]:
        """Check Gmail sending quota and limits."""
        quota_info = {
            "daily_limit": 500,  # Gmail's typical daily sending limit
            "per_second_limit": 20,  # Gmail's per-second limit
            "remaining_today": "unknown",
            "reset_time": "unknown",
        }

        # Note: Gmail doesn't provide quota information via SMTP
        # This is a placeholder for future implementation with Gmail API

        return quota_info

    def validate_email_settings(self) -> Dict[str, Any]:
        """Validate email settings in profile."""
        validation = {
            "email_valid": False,
            "password_configured": False,
            "smtp_accessible": False,
            "recommendations": [],
        }

        # Check email format
        if self.verify_email_format(self.email):
            validation["email_valid"] = True
        else:
            validation["recommendations"].append("Invalid email format")

        # Check if password is configured
        if self.password:
            validation["password_configured"] = True
        else:
            validation["recommendations"].append("Email password not configured")

        # Test SMTP access
        if validation["email_valid"] and validation["password_configured"]:
            verification = self.verify_gmail_account()
            validation["smtp_accessible"] = verification["valid"]
            if not verification["valid"]:
                validation["recommendations"].append(f"SMTP access failed: {verification['error']}")

        return validation

    def get_email_templates(self) -> Dict[str, str]:
        """Get email templates for job applications."""
        templates = {
            "cover_letter": """
Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company_name}. 

{cover_letter_content}

I look forward to discussing how my skills and experience can contribute to your team.

Best regards,
{applicant_name}
            """,
            "follow_up": """
Dear {hiring_manager_name},

I hope this email finds you well. I wanted to follow up on my application for the {job_title} position at {company_name}.

{follow_up_content}

Thank you for your time and consideration.

Best regards,
{applicant_name}
            """,
            "thank_you": """
Dear {hiring_manager_name},

Thank you for taking the time to interview me for the {job_title} position at {company_name}.

{thank_you_content}

I look forward to hearing from you.

Best regards,
{applicant_name}
            """,
        }

        return templates

    def get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")
