#!/usr/bin/env python3
"""
Job Alert Notification Service for JobQst
Sends notifications when new jobs matching user criteria are found.

Features:
- Email notifications using SMTP
- Desktop notifications using plyer
- Configurable notification preferences per profile
- Rate limiting to avoid spam
- Template-based notification content
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

try:
    from plyer import notification
    DESKTOP_NOTIFICATIONS_AVAILABLE = True
except ImportError:
    DESKTOP_NOTIFICATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)


class JobAlertService:
    """Service for sending job alerts and notifications."""
    
    def __init__(self, profile_path: str):
        self.profile_path = Path(profile_path)
        self.config = self._load_notification_config()
        self.last_notification_file = self.profile_path / "last_notification.json"
        
    def _load_notification_config(self) -> Dict[str, Any]:
        """Load notification configuration from profile."""
        config_file = self.profile_path / "notification_config.json"
        
        default_config = {
            "email_enabled": False,
            "desktop_enabled": True,
            "email_address": "",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "min_match_score": 0.7,
            "notification_frequency": "immediate",  # immediate, daily, weekly
            "keywords_filter": [],
            "companies_filter": [],
            "location_types_filter": [],  # remote, hybrid, onsite
            "max_notifications_per_day": 10,
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00"
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading notification config: {e}")
        
        return default_config
    
    def save_notification_config(self, config: Dict[str, Any]) -> bool:
        """Save notification configuration to profile."""
        try:
            config_file = self.profile_path / "notification_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Error saving notification config: {e}")
            return False
    
    def should_send_notification(self) -> bool:
        """Check if notifications should be sent based on frequency and limits."""
        
        # Check frequency setting
        if self.config.get("notification_frequency") == "disabled":
            return False
        
        # Check quiet hours
        if self._is_quiet_time():
            return False
        
        # Check daily limit
        if self._exceeded_daily_limit():
            return False
        
        # Check frequency timing
        last_notification = self._get_last_notification_time()
        if last_notification:
            if self.config.get("notification_frequency") == "daily":
                if datetime.now() - last_notification < timedelta(hours=24):
                    return False
            elif self.config.get("notification_frequency") == "weekly":
                if datetime.now() - last_notification < timedelta(days=7):
                    return False
        
        return True
    
    def send_job_alerts(self, new_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send notifications for new jobs."""
        if not self.should_send_notification():
            return {"status": "skipped", "reason": "notification_conditions_not_met"}
        
        # Filter jobs based on user preferences
        filtered_jobs = self._filter_jobs_for_notification(new_jobs)
        
        if not filtered_jobs:
            return {"status": "skipped", "reason": "no_jobs_match_criteria"}
        
        results = {
            "total_jobs": len(filtered_jobs),
            "email_sent": False,
            "desktop_sent": False,
            "errors": []
        }
        
        # Send email notification
        if self.config.get("email_enabled"):
            try:
                self._send_email_notification(filtered_jobs)
                results["email_sent"] = True
            except Exception as e:
                error_msg = f"Email notification failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Send desktop notification
        if self.config.get("desktop_enabled") and DESKTOP_NOTIFICATIONS_AVAILABLE:
            try:
                self._send_desktop_notification(filtered_jobs)
                results["desktop_sent"] = True
            except Exception as e:
                error_msg = f"Desktop notification failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Update last notification time
        self._update_last_notification_time()
        
        logger.info(f"Job alerts sent: {len(filtered_jobs)} jobs, "
                   f"email: {results['email_sent']}, "
                   f"desktop: {results['desktop_sent']}")
        
        return results
    
    def _filter_jobs_for_notification(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter jobs based on notification preferences."""
        filtered_jobs = []
        
        for job in jobs:
            # Check match score
            match_score = job.get('match_score', 0) or job.get('compatibility_score', 0)
            if match_score < self.config.get("min_match_score", 0.7):
                continue
            
            # Check keywords filter
            keywords_filter = self.config.get("keywords_filter", [])
            if keywords_filter:
                job_text = ' '.join([
                    job.get('title', ''),
                    job.get('description', ''),
                    job.get('keywords', '') if isinstance(job.get('keywords'), str) else ''
                ]).lower()
                
                if not any(keyword.lower() in job_text for keyword in keywords_filter):
                    continue
            
            # Check companies filter
            companies_filter = self.config.get("companies_filter", [])
            if companies_filter:
                company = job.get('company', '').lower()
                if not any(comp.lower() in company for comp in companies_filter):
                    continue
            
            # Check location types filter
            location_types_filter = self.config.get("location_types_filter", [])
            if location_types_filter:
                location_type = job.get('location_type', 'unknown')
                if location_type not in location_types_filter:
                    continue
            
            filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _send_email_notification(self, jobs: List[Dict[str, Any]]) -> None:
        """Send email notification for new jobs."""
        if not self.config.get("email_address"):
            raise Exception("Email address not configured")
        
        # Create email content
        subject = f"JobQst Alert: {len(jobs)} New Job{'s' if len(jobs) > 1 else ''} Found"
        body = self._generate_email_body(jobs)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.config.get("smtp_username", self.config["email_address"])
        msg['To'] = self.config["email_address"]
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
        server.starttls()
        server.login(self.config["smtp_username"], self.config["smtp_password"])
        server.send_message(msg)
        server.quit()
    
    def _send_desktop_notification(self, jobs: List[Dict[str, Any]]) -> None:
        """Send desktop notification for new jobs."""
        if not DESKTOP_NOTIFICATIONS_AVAILABLE:
            raise Exception("Desktop notifications not available (plyer not installed)")
        
        title = f"JobQst: {len(jobs)} New Job{'s' if len(jobs) > 1 else ''}"
        
        if len(jobs) == 1:
            job = jobs[0]
            message = f"{job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}"
        else:
            top_jobs = jobs[:3]
            message = "New opportunities:\n" + "\n".join([
                f"• {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}"
                for job in top_jobs
            ])
            if len(jobs) > 3:
                message += f"\n... and {len(jobs) - 3} more"
        
        notification.notify(
            title=title,
            message=message,
            timeout=10,
            app_name="JobQst"
        )
    
    def _generate_email_body(self, jobs: List[Dict[str, Any]]) -> str:
        """Generate HTML email body for job notifications."""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                .job { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .job-title { font-size: 18px; font-weight: bold; color: #2c3e50; }
                .job-company { font-size: 16px; color: #3498db; margin: 5px 0; }
                .job-location { color: #7f8c8d; margin: 5px 0; }
                .job-score { background-color: #e8f5e8; padding: 5px 10px; border-radius: 3px; display: inline-block; margin: 5px 0; }
                .job-url { margin: 10px 0; }
                .job-url a { color: #3498db; text-decoration: none; }
                .footer { text-align: center; margin-top: 30px; color: #7f8c8d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>JobQst Job Alert</h1>
                <p>Found """ + str(len(jobs)) + """ new job""" + ("s" if len(jobs) > 1 else "") + """ matching your criteria</p>
            </div>
        """
        
        for job in jobs[:10]:  # Limit to 10 jobs in email
            score = job.get('match_score', 0) or job.get('compatibility_score', 0)
            location_type = job.get('location_type', 'Unknown')
            
            html += f"""
            <div class="job">
                <div class="job-title">{job.get('title', 'Unknown Position')}</div>
                <div class="job-company">{job.get('company', 'Unknown Company')}</div>
                <div class="job-location">{job.get('location', 'Location not specified')} • {location_type.title()}</div>
                <div class="job-score">Match Score: {score:.1%}</div>
                <div class="job-url"><a href="{job.get('url', '#')}">View Job Posting</a></div>
            </div>
            """
        
        if len(jobs) > 10:
            html += f"<p><em>... and {len(jobs) - 10} more jobs in your JobQst dashboard</em></p>"
        
        html += """
            <div class="footer">
                <p>This alert was sent by JobQst. You can update your notification preferences in the dashboard.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _is_quiet_time(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self.config.get("quiet_hours", {}).get("enabled", False):
            return False
        
        try:
            now = datetime.now().time()
            start_time = datetime.strptime(
                self.config["quiet_hours"]["start"], "%H:%M"
            ).time()
            end_time = datetime.strptime(
                self.config["quiet_hours"]["end"], "%H:%M"
            ).time()
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # Quiet hours cross midnight
                return now >= start_time or now <= end_time
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def _exceeded_daily_limit(self) -> bool:
        """Check if daily notification limit has been exceeded."""
        try:
            today = datetime.now().date()
            daily_count_file = self.profile_path / f"notifications_{today}.json"
            
            if daily_count_file.exists():
                with open(daily_count_file, 'r') as f:
                    daily_data = json.load(f)
                    count = daily_data.get("count", 0)
                    return count >= self.config.get("max_notifications_per_day", 10)
            
            return False
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return False
    
    def _get_last_notification_time(self) -> Optional[datetime]:
        """Get the timestamp of the last notification."""
        try:
            if self.last_notification_file.exists():
                with open(self.last_notification_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data["last_notification"])
        except Exception as e:
            logger.error(f"Error reading last notification time: {e}")
        
        return None
    
    def _update_last_notification_time(self) -> None:
        """Update the timestamp of the last notification."""
        try:
            now = datetime.now()
            
            # Update last notification time
            with open(self.last_notification_file, 'w') as f:
                json.dump({"last_notification": now.isoformat()}, f)
            
            # Update daily count
            today = now.date()
            daily_count_file = self.profile_path / f"notifications_{today}.json"
            
            count = 0
            if daily_count_file.exists():
                with open(daily_count_file, 'r') as f:
                    data = json.load(f)
                    count = data.get("count", 0)
            
            with open(daily_count_file, 'w') as f:
                json.dump({"count": count + 1, "date": today.isoformat()}, f)
                
        except Exception as e:
            logger.error(f"Error updating notification time: {e}")
    
    def test_notifications(self) -> Dict[str, Any]:
        """Test notification system with sample data."""
        test_job = {
            "title": "Test Software Developer Position",
            "company": "Test Company",
            "location": "Test Location",
            "match_score": 0.85,
            "location_type": "remote",
            "url": "https://example.com/job/test"
        }
        
        return self.send_job_alerts([test_job])

