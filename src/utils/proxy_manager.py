#!/usr/bin/env python3
"""
Proxy Manager for Multi-Profile Job Searching
Handles rotating proxies to avoid IP detection across multiple resume profiles.
"""

import json
import random
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import time
from rich.console import Console

console = Console()


@dataclass
class ProxyConfig:
    """Configuration for a single proxy."""

    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks5
    location: Optional[str] = None
    provider: Optional[str] = None
    is_working: bool = True
    last_tested: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dict for requests."""
        proxy_url = f"{self.protocol}://"
        if self.username and self.password:
            proxy_url += f"{self.username}:{self.password}@"
        proxy_url += f"{self.host}:{self.port}"

        return {"http": proxy_url, "https": proxy_url}

    def __str__(self) -> str:
        return f"{self.location or 'Unknown'} ({self.host}:{self.port})"


class ProxyManager:
    """
    Manages proxy rotation for multi-profile job searching.

    Features:
    - Proxy health checking
    - Profile-to-proxy assignment
    - Automatic failover
    - Location-based routing
    """

    def __init__(self, config_file: str = "config/proxies.json"):
        self.config_file = Path(config_file)
        self.proxies: List[ProxyConfig] = []
        self.profile_assignments: Dict[str, str] = {}  # profile_name -> proxy_id
        self.load_config()

    def load_config(self):
        """Load proxy configuration from file."""
        if not self.config_file.exists():
            self.create_sample_config()
            return

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

            # Load proxies
            for proxy_data in data.get("proxies", []):
                proxy = ProxyConfig(
                    host=proxy_data["host"],
                    port=proxy_data["port"],
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                    protocol=proxy_data.get("protocol", "http"),
                    location=proxy_data.get("location"),
                    provider=proxy_data.get("provider"),
                    is_working=proxy_data.get("is_working", True),
                )
                self.proxies.append(proxy)

            # Load assignments
            self.profile_assignments = data.get("profile_assignments", {})

            console.print(f"[green]Loaded {len(self.proxies)} proxies from config[/green]")

        except Exception as e:
            console.print(f"[red]Error loading proxy config: {e}[/red]")
            self.create_sample_config()

    def create_sample_config(self):
        """Create a sample proxy configuration file."""
        sample_config = {
            "proxies": [
                {
                    "host": "proxy1.example.com",
                    "port": 8080,
                    "username": "your_username",
                    "password": "your_password",
                    "protocol": "http",
                    "location": "Toronto, CA",
                    "provider": "ProxyProvider1",
                    "is_working": True,
                },
                {
                    "host": "proxy2.example.com",
                    "port": 8080,
                    "username": "your_username",
                    "password": "your_password",
                    "protocol": "http",
                    "location": "Vancouver, CA",
                    "provider": "ProxyProvider1",
                    "is_working": True,
                },
            ],
            "profile_assignments": {
                "DataScientist_Resume": "proxy1.example.com:8080",
                "SoftwareEng_Resume": "proxy2.example.com:8080",
            },
            "settings": {"test_url": "http://httpbin.org/ip", "timeout": 10, "retry_attempts": 3},
        }

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(sample_config, f, indent=2)

        console.print(f"[yellow]Created sample config at {self.config_file}[/yellow]")
        console.print("[yellow]Please edit with your actual proxy details![/yellow]")

    def test_proxy(self, proxy: ProxyConfig) -> bool:
        """Test if a proxy is working."""
        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxy.to_dict(), timeout=10)

            if response.status_code == 200:
                ip_data = response.json()
                console.print(f"[green]✅ {proxy} - IP: {ip_data.get('origin')}[/green]")
                proxy.is_working = True
                proxy.last_tested = time.time()
                return True
            else:
                console.print(f"[red]❌ {proxy} - Status: {response.status_code}[/red]")
                proxy.is_working = False
                return False

        except Exception as e:
            console.print(f"[red]❌ {proxy} - Error: {e}[/red]")
            proxy.is_working = False
            return False

    def test_all_proxies(self):
        """Test all configured proxies."""
        console.print("[cyan]Testing all proxies...[/cyan]")
        working_count = 0

        for proxy in self.proxies:
            if self.test_proxy(proxy):
                working_count += 1

        console.print(
            f"\n[bold]Proxy Test Results: {working_count}/{len(self.proxies)} working[/bold]"
        )
        return working_count

    def assign_proxy_to_profile(
        self, profile_name: str, proxy_preference: str = None
    ) -> Optional[ProxyConfig]:
        """
        Assign a proxy to a profile.

        Args:
            profile_name: Name of the profile
            proxy_preference: Preferred location/provider (optional)
        """
        # Check if already assigned
        if profile_name in self.profile_assignments:
            proxy_id = self.profile_assignments[profile_name]
            proxy = self.get_proxy_by_id(proxy_id)
            if proxy and proxy.is_working:
                return proxy

        # Find available working proxy
        working_proxies = [p for p in self.proxies if p.is_working]

        if not working_proxies:
            console.print("[red]No working proxies available![/red]")
            return None

        # Prefer location-based assignment if specified
        if proxy_preference:
            preferred = [
                p for p in working_proxies if proxy_preference.lower() in (p.location or "").lower()
            ]
            if preferred:
                working_proxies = preferred

        # Avoid assigning same proxy to multiple profiles
        assigned_proxies = set(self.profile_assignments.values())
        available_proxies = [
            p for p in working_proxies if f"{p.host}:{p.port}" not in assigned_proxies
        ]

        if available_proxies:
            chosen_proxy = random.choice(available_proxies)
        else:
            # All proxies assigned, use least used one
            chosen_proxy = random.choice(working_proxies)

        # Save assignment
        proxy_id = f"{chosen_proxy.host}:{chosen_proxy.port}"
        self.profile_assignments[profile_name] = proxy_id
        self.save_assignments()

        console.print(f"[green]Assigned {chosen_proxy} to profile '{profile_name}'[/green]")
        return chosen_proxy

    def get_proxy_by_id(self, proxy_id: str) -> Optional[ProxyConfig]:
        """Get proxy by host:port identifier."""
        for proxy in self.proxies:
            if f"{proxy.host}:{proxy.port}" == proxy_id:
                return proxy
        return None

    def get_proxy_for_profile(self, profile_name: str) -> Optional[ProxyConfig]:
        """Get the assigned proxy for a profile."""
        if profile_name in self.profile_assignments:
            proxy_id = self.profile_assignments[profile_name]
            return self.get_proxy_by_id(proxy_id)
        return None

    def save_assignments(self):
        """Save profile assignments to config file."""
        try:
            # Read current config
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    data = json.load(f)
            else:
                data = {}

            # Update assignments
            data["profile_assignments"] = self.profile_assignments

            # Write back
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            console.print(f"[red]Error saving assignments: {e}[/red]")

    def show_status(self):
        """Show current proxy status and assignments."""
        console.print("\n=== Proxy Manager Status ===")

        # Show proxies
        from rich.table import Table

        table = Table(title="Available Proxies")
        table.add_column("Location", style="cyan")
        table.add_column("Host:Port", style="yellow")
        table.add_column("Status", style="bold")
        table.add_column("Assigned To", style="green")

        assigned_proxies = {v: k for k, v in self.profile_assignments.items()}

        for proxy in self.proxies:
            proxy_id = f"{proxy.host}:{proxy.port}"
            status = "✅ Working" if proxy.is_working else "❌ Failed"
            assigned_to = assigned_proxies.get(proxy_id, "Unassigned")

            table.add_row(proxy.location or "Unknown", proxy_id, status, assigned_to)

        console.print(table)


def setup_proxy_based_search():
    """Set up proxy-based multi-profile searching."""
    console.print("=== Proxy-Based Multi-Profile Setup ===")

    manager = ProxyManager()

    # Test proxies
    working_count = manager.test_all_proxies()

    if working_count == 0:
        console.print("[red]No working proxies found![/red]")
        console.print("[yellow]Please configure proxies in config/proxies.json[/yellow]")
        return

    # Show current status
    manager.show_status()

    # Get available profiles
    profiles_dir = Path("profiles")
    available_profiles = [
        p.name for p in profiles_dir.iterdir() if p.is_dir() and p.name != "__pycache__"
    ]

    console.print(f"\n[cyan]Available profiles: {', '.join(available_profiles)}[/cyan]")

    # Auto-assign proxies
    for profile in available_profiles:
        proxy = manager.assign_proxy_to_profile(profile)
        if proxy:
            console.print(f"[green]{profile} -> {proxy}[/green]")

    console.print("\n[bold green]✅ Proxy assignments complete![/bold green]")
    console.print("[yellow]You can now run multiple profiles simultaneously![/yellow]")


if __name__ == "__main__":
    setup_proxy_based_search()
