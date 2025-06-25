#!/usr/bin/env python3
"""Test profile loading functionality."""

import json
from pathlib import Path

def test_profile_loading():
    """Test loading the Nirajan profile."""
    try:
        # Direct JSON loading
        profile_path = Path("profiles/Nirajan/Nirajan.json")
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                print("✅ Profile loaded successfully!")
                print(f"Name: {profile_data.get('name', 'Unknown')}")
                print(f"Keywords: {profile_data.get('keywords', [])}")
                print(f"Skills: {profile_data.get('skills', [])}")
                print(f"Total search terms: {len(profile_data.get('keywords', []) + profile_data.get('skills', []))}")
                return True
        else:
            print(f"❌ Profile file not found: {profile_path}")
            return False
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return False

if __name__ == "__main__":
    test_profile_loading() 