#!/usr/bin/env python3
"""
Multi-Profile Rate Limiting and IP Management
Handles safe job searching across multiple profiles from same IP.
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ProfileSession:
    """Track session info for each profile."""

    profile_name: str
    last_request_time: Optional[datetime] = None
    request_count: int = 0
    daily_request_count: int = 0
    last_reset_date: Optional[str] = None
    is_cooling_down: bool = False
    cooldown_until: Optional[datetime] = None


class MultiProfileRateLimiter:
    """
    Manages rate limiting across multiple profiles to avoid IP detection.

    Key Safety Features:
    - Delays between profiles from same IP
    - Daily request limits per profile
    - Randomized timing to avoid patterns
    - Cooling down periods for overuse
    """

    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.session_file = self.profiles_dir / "rate_limit_sessions.json"
        self.sessions: Dict[str, ProfileSession] = {}
        self.load_sessions()

        # Safety limits
        self.min_delay_between_profiles = 30  # 30 seconds minimum
        self.max_delay_between_profiles = 120  # 2 minutes maximum
        self.daily_request_limit = 50  # Max requests per profile per day
        self.cooldown_period = 3600  # 1 hour cooldown if limits exceeded

    def load_sessions(self):
        """Load existing session data."""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    data = json.load(f)
                    for profile_name, session_data in data.items():
                        session = ProfileSession(
                            profile_name=profile_name,
                            request_count=session_data.get("request_count", 0),
                            daily_request_count=session_data.get("daily_request_count", 0),
                            last_reset_date=session_data.get("last_reset_date"),
                            is_cooling_down=session_data.get("is_cooling_down", False),
                        )

                        # Parse datetime strings
                        if session_data.get("last_request_time"):
                            session.last_request_time = datetime.fromisoformat(
                                session_data["last_request_time"]
                            )
                        if session_data.get("cooldown_until"):
                            session.cooldown_until = datetime.fromisoformat(
                                session_data["cooldown_until"]
                            )

                        self.sessions[profile_name] = session
            except Exception as e:
                print(f"Warning: Could not load session data: {e}")

    def save_sessions(self):
        """Save session data to file."""
        try:
            data = {}
            for profile_name, session in self.sessions.items():
                data[profile_name] = {
                    "request_count": session.request_count,
                    "daily_request_count": session.daily_request_count,
                    "last_reset_date": session.last_reset_date,
                    "is_cooling_down": session.is_cooling_down,
                    "last_request_time": (
                        session.last_request_time.isoformat() if session.last_request_time else None
                    ),
                    "cooldown_until": (
                        session.cooldown_until.isoformat() if session.cooldown_until else None
                    ),
                }

            self.profiles_dir.mkdir(exist_ok=True)
            with open(self.session_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session data: {e}")

    def can_make_request(self, profile_name: str) -> tuple[bool, str]:
        """
        Check if profile can make a request safely.
        Returns (can_request, reason_if_not)
        """
        now = datetime.now()
        session = self.sessions.get(profile_name)

        if not session:
            # Create new session
            session = ProfileSession(profile_name=profile_name)
            self.sessions[profile_name] = session

        # Reset daily count if new day
        today = now.strftime("%Y-%m-%d")
        if session.last_reset_date != today:
            session.daily_request_count = 0
            session.last_reset_date = today

        # Check if in cooldown
        if session.is_cooling_down and session.cooldown_until:
            if now < session.cooldown_until:
                remaining = session.cooldown_until - now
                return False, f"Profile in cooldown for {remaining.seconds//60} more minutes"
            else:
                # Cooldown expired
                session.is_cooling_down = False
                session.cooldown_until = None

        # Check daily limit
        if session.daily_request_count >= self.daily_request_limit:
            session.is_cooling_down = True
            session.cooldown_until = now + timedelta(seconds=self.cooldown_period)
            self.save_sessions()
            return False, f"Daily limit ({self.daily_request_limit}) reached for profile"

        # Check minimum delay between requests for this profile
        if session.last_request_time:
            time_since_last = now - session.last_request_time
            min_profile_delay = 300  # 5 minutes between requests for same profile
            if time_since_last.total_seconds() < min_profile_delay:
                remaining = min_profile_delay - time_since_last.total_seconds()
                return False, f"Profile needs {remaining//60:.0f} more minutes before next request"

        return True, "OK"

    def get_safe_delay_before_request(self, profile_name: str) -> int:
        """
        Calculate safe delay before making request to avoid IP detection.
        Returns delay in seconds.
        """
        # Check last request across ALL profiles
        last_any_request = None
        for session in self.sessions.values():
            if session.last_request_time:
                if not last_any_request or session.last_request_time > last_any_request:
                    last_any_request = session.last_request_time

        if last_any_request:
            time_since_any_request = datetime.now() - last_any_request
            required_delay = self.min_delay_between_profiles

            if time_since_any_request.total_seconds() < required_delay:
                additional_delay = required_delay - time_since_any_request.total_seconds()
                # Add random factor to avoid patterns
                random_factor = random.uniform(0.5, 1.5)
                return int(additional_delay * random_factor)

        # Add small random delay even if no recent requests
        return random.randint(5, 15)

    def record_request(self, profile_name: str):
        """Record that a request was made for this profile."""
        now = datetime.now()
        session = self.sessions.get(profile_name)

        if not session:
            session = ProfileSession(profile_name=profile_name)
            self.sessions[profile_name] = session

        session.last_request_time = now
        session.request_count += 1
        session.daily_request_count += 1

        self.save_sessions()

    def get_status_report(self) -> Dict:
        """Get status report for all profiles."""
        report = {"total_profiles": len(self.sessions), "profiles": {}}

        for profile_name, session in self.sessions.items():
            can_request, reason = self.can_make_request(profile_name)
            delay = self.get_safe_delay_before_request(profile_name)

            report["profiles"][profile_name] = {
                "can_request": can_request,
                "reason": reason,
                "recommended_delay": delay,
                "daily_requests": session.daily_request_count,
                "daily_limit": self.daily_request_limit,
                "is_cooling_down": session.is_cooling_down,
                "last_request": (
                    session.last_request_time.isoformat() if session.last_request_time else None
                ),
            }

        return report


def safe_multi_profile_search(profiles: List[str], search_function, **kwargs):
    """
    Safely execute job searches across multiple profiles with proper delays.

    Args:
        profiles: List of profile names to search
        search_function: Function to call for each profile
        **kwargs: Arguments to pass to search function
    """
    limiter = MultiProfileRateLimiter()
    results = {}

    for profile_name in profiles:
        print(f"\n=== Processing Profile: {profile_name} ===")

        # Check if we can make request
        can_request, reason = limiter.can_make_request(profile_name)
        if not can_request:
            print(f"❌ Skipping {profile_name}: {reason}")
            results[profile_name] = {"status": "skipped", "reason": reason}
            continue

        # Calculate safe delay
        delay = limiter.get_safe_delay_before_request(profile_name)
        if delay > 0:
            print(f"⏳ Waiting {delay} seconds for IP safety...")
            time.sleep(delay)

        # Make the request
        try:
            print(f"🚀 Starting job search for {profile_name}")
            result = search_function(profile_name, **kwargs)
            limiter.record_request(profile_name)
            results[profile_name] = {"status": "success", "result": result}
            print(f"✅ Completed {profile_name}")
        except Exception as e:
            print(f"❌ Error with {profile_name}: {e}")
            results[profile_name] = {"status": "error", "error": str(e)}

    return results


if __name__ == "__main__":
    # Example usage
    limiter = MultiProfileRateLimiter()
    report = limiter.get_status_report()

    print("=== Multi-Profile Safety Status ===")
    for profile, status in report["profiles"].items():
        print(f"\nProfile: {profile}")
        print(f"  Can request: {status['can_request']}")
        print(f"  Daily requests: {status['daily_requests']}/{status['daily_limit']}")
        if not status["can_request"]:
            print(f"  Reason: {status['reason']}")
        else:
            print(f"  Recommended delay: {status['recommended_delay']} seconds")
