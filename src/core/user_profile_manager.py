#!/usr/bin/env python3
"""
Modern User Profile Manager - Simple, robust, and easy to debug
Enhanced with better error handling and modern Python patterns.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProfileData:
    """Simple profile data structure."""
    name: str
    email: str = ""
    phone: str = ""
    location: str = ""
    resume_path: str = ""
    cover_letter_path: str = ""
    linkedin_url: str = ""
    portfolio_url: str = ""
    skills: Optional[List[str]] = None
    experience_years: int = 0
    education: str = ""
    created_at: str = ""
    updated_at: str = ""
    settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.settings is None:
            self.settings = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()

class ModernUserProfileManager:
    """
    Modern user profile manager with simple, robust operations.
    Enhanced error handling and easy debugging.
    """
    
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = "profile.json"
        self.settings_file = "settings.json"
        logger.info(f"✅ Modern profile manager initialized: {self.profiles_dir}")
    
    def create_profile(self, name: str, profile_data: Optional[Dict] = None) -> bool:
        """
        Create a new user profile.
        Returns True if created, False if already exists.
        """
        try:
            profile_path = self.profiles_dir / name
            if profile_path.exists():
                logger.warning(f"⚠️ Profile '{name}' already exists")
                return False
            
            # Create profile directory
            profile_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize profile data
            if profile_data is None:
                profile_data = {}
            
            profile = ProfileData(
                name=name,
                email=profile_data.get('email', ''),
                phone=profile_data.get('phone', ''),
                location=profile_data.get('location', ''),
                resume_path=profile_data.get('resume_path', ''),
                cover_letter_path=profile_data.get('cover_letter_path', ''),
                linkedin_url=profile_data.get('linkedin_url', ''),
                portfolio_url=profile_data.get('portfolio_url', ''),
                skills=profile_data.get('skills', []),
                experience_years=profile_data.get('experience_years', 0),
                education=profile_data.get('education', '')
            )
            
            # Save profile
            self._save_profile(name, profile)
            
            # Create default settings
            default_settings = {
                'auto_apply': False,
                'preferred_sites': ['indeed', 'linkedin', 'eluta'],
                'max_applications_per_day': 10,
                'notification_email': profile.email,
                'resume_version': 'latest',
                'cover_letter_template': 'default'
            }
            self._save_settings(name, default_settings)
            
            logger.info(f"✅ Created profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create profile '{name}': {e}")
            return False
    
    def get_profile(self, name: str) -> Optional[ProfileData]:
        """Get profile data by name."""
        try:
            profile_path = self.profiles_dir / name / self.profile_file
            if not profile_path.exists():
                logger.warning(f"⚠️ Profile '{name}' not found")
                return None
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = ProfileData(**data)
            logger.info(f"✅ Loaded profile: {name}")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Failed to load profile '{name}': {e}")
            return None
    
    def update_profile(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update profile data."""
        try:
            profile = self.get_profile(name)
            if not profile:
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            profile.update_timestamp()
            
            # Save updated profile
            self._save_profile(name, profile)
            
            logger.info(f"✅ Updated profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update profile '{name}': {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile and all its data."""
        try:
            profile_path = self.profiles_dir / name
            if not profile_path.exists():
                logger.warning(f"⚠️ Profile '{name}' not found")
                return False
            
            # Remove entire profile directory
            shutil.rmtree(profile_path)
            
            logger.info(f"✅ Deleted profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete profile '{name}': {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """Get list of all profile names."""
        try:
            profiles = []
            for item in self.profiles_dir.iterdir():
                if item.is_dir() and (item / self.profile_file).exists():
                    profiles.append(item.name)
            
            logger.info(f"✅ Found {len(profiles)} profiles")
            return sorted(profiles)
            
        except Exception as e:
            logger.error(f"❌ Failed to list profiles: {e}")
            return []
    
    def get_settings(self, name: str) -> Dict[str, Any]:
        """Get profile settings."""
        try:
            settings_path = self.profiles_dir / name / self.settings_file
            if not settings_path.exists():
                logger.warning(f"⚠️ Settings for profile '{name}' not found")
                return {}
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            logger.info(f"✅ Loaded settings for profile: {name}")
            return settings
            
        except Exception as e:
            logger.error(f"❌ Failed to load settings for profile '{name}': {e}")
            return {}
    
    def update_settings(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update profile settings."""
        try:
            settings = self.get_settings(name)
            settings.update(updates)
            
            self._save_settings(name, settings)
            
            logger.info(f"✅ Updated settings for profile: {name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update settings for profile '{name}': {e}")
            return False
    
    def get_resume_path(self, name: str) -> Optional[str]:
        """Get the resume file path for a profile."""
        try:
            profile = self.get_profile(name)
            if not profile or not profile.resume_path:
                return None
            
            resume_path = Path(profile.resume_path)
            if resume_path.is_absolute():
                return str(resume_path) if resume_path.exists() else None
            else:
                # Relative to profile directory
                full_path = self.profiles_dir / name / resume_path
                return str(full_path) if full_path.exists() else None
                
        except Exception as e:
            logger.error(f"❌ Failed to get resume path for profile '{name}': {e}")
            return None
    
    def get_cover_letter_path(self, name: str) -> Optional[str]:
        """Get the cover letter file path for a profile."""
        try:
            profile = self.get_profile(name)
            if not profile or not profile.cover_letter_path:
                return None
            
            cover_path = Path(profile.cover_letter_path)
            if cover_path.is_absolute():
                return str(cover_path) if cover_path.exists() else None
            else:
                # Relative to profile directory
                full_path = self.profiles_dir / name / cover_path
                return str(full_path) if full_path.exists() else None
                
        except Exception as e:
            logger.error(f"❌ Failed to get cover letter path for profile '{name}': {e}")
            return None
    
    def copy_document(self, name: str, source_path: str, document_type: str = "resume") -> bool:
        """Copy a document to the profile directory."""
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"❌ Source file not found: {source_path}")
                return False
            
            profile_path = self.profiles_dir / name
            profile_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = source.suffix
            filename = f"{document_type}_{timestamp}{extension}"
            
            dest_path = profile_path / filename
            
            # Copy file
            shutil.copy2(source, dest_path)
            
            # Update profile
            if document_type == "resume":
                self.update_profile(name, {"resume_path": str(dest_path)})
            elif document_type == "cover_letter":
                self.update_profile(name, {"cover_letter_path": str(dest_path)})
            
            logger.info(f"✅ Copied {document_type} to profile '{name}': {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to copy {document_type} for profile '{name}': {e}")
            return False
    
    def get_profile_stats(self) -> Dict[str, Any]:
        """Get statistics about all profiles."""
        try:
            profiles = self.list_profiles()
            stats = {
                'total_profiles': len(profiles),
                'profiles_with_resume': 0,
                'profiles_with_cover_letter': 0,
                'profiles_with_email': 0,
                'profiles_with_linkedin': 0,
                'recent_profiles': 0
            }
            
            # Check each profile
            for name in profiles:
                profile = self.get_profile(name)
                if profile:
                    if profile.resume_path:
                        stats['profiles_with_resume'] += 1
                    if profile.cover_letter_path:
                        stats['profiles_with_cover_letter'] += 1
                    if profile.email:
                        stats['profiles_with_email'] += 1
                    if profile.linkedin_url:
                        stats['profiles_with_linkedin'] += 1
                    
                    # Check if profile was created in last 30 days
                    try:
                        created = datetime.fromisoformat(profile.created_at)
                        if (datetime.now() - created).days <= 30:
                            stats['recent_profiles'] += 1
                    except:
                        pass
            
            logger.info(f"✅ Retrieved profile stats: {stats['total_profiles']} total profiles")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get profile stats: {e}")
            return {'total_profiles': 0}
    
    def backup_profile(self, name: str, backup_dir: str = "backups") -> bool:
        """Create a backup of a profile."""
        try:
            profile_path = self.profiles_dir / name
            if not profile_path.exists():
                logger.warning(f"⚠️ Profile '{name}' not found for backup")
                return False
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{name}_backup_{timestamp}"
            backup_dest = backup_path / backup_name
            
            # Copy entire profile directory
            shutil.copytree(profile_path, backup_dest)
            
            logger.info(f"✅ Created backup of profile '{name}': {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to backup profile '{name}': {e}")
            return False
    
    def _save_profile(self, name: str, profile: ProfileData):
        """Save profile data to file."""
        profile_path = self.profiles_dir / name / self.profile_file
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _save_settings(self, name: str, settings: Dict[str, Any]):
        """Save settings to file."""
        settings_path = self.profiles_dir / name / self.settings_file
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

# Global profile manager instance
_profile_manager = None

def get_profile_manager(profiles_dir: str = "profiles") -> ModernUserProfileManager:
    """Get global profile manager instance."""
    global _profile_manager
    
    if _profile_manager is None:
        _profile_manager = ModernUserProfileManager(profiles_dir)
    
    return _profile_manager

def get_user_profile_manager(profile_name: str = "default") -> ModernUserProfileManager:
    """Get a user profile manager instance."""
    return ModernUserProfileManager(profile_name)

# Backward compatibility alias
UserProfileManager = ModernUserProfileManager
