#!/usr/bin/env python3
"""
Profile Management Script for SOLEil Platform
Easily manage user profiles in the registry for development and testing purposes.
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProfileManager:
    """Manages user profiles in the SOLEil platform."""
    
    def __init__(self, profiles_file: str = "user_profiles.json"):
        self.profiles_file = Path(profiles_file)
        self.backup_dir = Path("profile_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def load_profiles(self) -> Dict:
        """Load profiles from the registry file."""
        try:
            if not self.profiles_file.exists():
                logger.warning(f"Profile file {self.profiles_file} not found")
                return {}
            
            with open(self.profiles_file, 'r') as f:
                profiles = json.load(f)
            
            logger.info(f"Loaded {len(profiles)} profiles from {self.profiles_file}")
            return profiles
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            return {}
    
    def save_profiles(self, profiles: Dict) -> bool:
        """Save profiles to the registry file."""
        try:
            # Create backup before saving
            self.create_backup()
            
            with open(self.profiles_file, 'w') as f:
                json.dump(profiles, f, indent=2)
            
            logger.info(f"Saved {len(profiles)} profiles to {self.profiles_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            return False
    
    def create_backup(self) -> str:
        """Create a backup of the current profile registry."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"profiles_backup_{timestamp}.json"
        
        try:
            if self.profiles_file.exists():
                shutil.copy2(self.profiles_file, backup_file)
                logger.info(f"Created backup: {backup_file}")
                return str(backup_file)
            else:
                logger.warning("No profiles file to backup")
                return ""
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return ""
    
    def list_profiles(self, show_details: bool = False) -> None:
        """List all profiles in the registry."""
        profiles = self.load_profiles()
        
        if not profiles:
            print("📋 No profiles found in registry")
            return
        
        print(f"📋 Found {len(profiles)} profiles in registry:")
        print("=" * 80)
        
        for user_id, profile in profiles.items():
            email = profile.get('email', 'Unknown')
            name = profile.get('name', 'Unknown')
            created = profile.get('created_at', 'Unknown')
            instruments = profile.get('instruments', [])
            
            print(f"👤 User ID: {user_id}")
            print(f"📧 Email: {email}")
            print(f"📛 Name: {name}")
            print(f"📅 Created: {created}")
            
            if instruments:
                print(f"🎵 Instruments: {', '.join(instruments)}")
            
            if show_details:
                print(f"🔧 UI Scale: {profile.get('ui_scale', 'Unknown')}")
                print(f"🔄 Last Updated: {profile.get('updated_at', 'Unknown')}")
                print(f"📊 Last Accessed: {profile.get('last_accessed', 'Unknown')}")
            
            print("-" * 40)
    
    def remove_profile(self, identifier: str, force: bool = False) -> bool:
        """Remove a profile from the registry."""
        profiles = self.load_profiles()
        
        # Find profile by email or user ID
        profile_to_remove = None
        user_id_to_remove = None
        
        for user_id, profile in profiles.items():
            if profile.get('email') == identifier or user_id == identifier:
                profile_to_remove = profile
                user_id_to_remove = user_id
                break
        
        if not profile_to_remove:
            logger.error(f"Profile not found: {identifier}")
            return False
        
        # Show profile details and ask for confirmation
        print(f"🗑️  About to remove profile:")
        print(f"   User ID: {user_id_to_remove}")
        print(f"   Email: {profile_to_remove.get('email')}")
        print(f"   Name: {profile_to_remove.get('name')}")
        
        if not force:
            confirm = input("❓ Are you sure? Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("❌ Profile removal cancelled")
                return False
        
        # Remove the profile
        del profiles[user_id_to_remove]
        
        if self.save_profiles(profiles):
            logger.info(f"Successfully removed profile: {identifier}")
            print(f"✅ Profile removed: {identifier}")
            return True
        else:
            logger.error(f"Failed to save profiles after removal")
            return False
    
    def remove_all_profiles(self, force: bool = False) -> bool:
        """Remove all profiles from the registry (DANGEROUS!)."""
        profiles = self.load_profiles()
        
        if not profiles:
            print("📋 No profiles to remove")
            return True
        
        print(f"🗑️  About to remove ALL {len(profiles)} profiles!")
        print("⚠️  This will clear the entire user registry!")
        
        if not force:
            confirm = input("❓ Are you absolutely sure? Type 'DELETE ALL' to confirm: ")
            if confirm != 'DELETE ALL':
                print("❌ Bulk profile removal cancelled")
                return False
        
        # Create backup before bulk removal
        backup_file = self.create_backup()
        
        # Clear all profiles
        profiles.clear()
        
        if self.save_profiles(profiles):
            logger.info(f"Successfully removed all profiles. Backup: {backup_file}")
            print(f"✅ All profiles removed. Backup created: {backup_file}")
            return True
        else:
            logger.error("Failed to save empty profile registry")
            return False
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore profiles from a backup file."""
        backup_path = self.backup_dir / backup_file
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Load backup
            with open(backup_path, 'r') as f:
                backup_profiles = json.load(f)
            
            # Create backup of current state
            self.create_backup()
            
            # Restore from backup
            if self.save_profiles(backup_profiles):
                logger.info(f"Successfully restored {len(backup_profiles)} profiles from {backup_file}")
                print(f"✅ Restored {len(backup_profiles)} profiles from backup: {backup_file}")
                return True
            else:
                logger.error("Failed to save restored profiles")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> None:
        """List available backup files."""
        if not self.backup_dir.exists():
            print("📁 No backup directory found")
            return
        
        backup_files = list(self.backup_dir.glob("profiles_backup_*.json"))
        
        if not backup_files:
            print("📁 No backup files found")
            return
        
        print(f"📁 Found {len(backup_files)} backup files:")
        print("=" * 60)
        
        for backup_file in sorted(backup_files, reverse=True):
            stat = backup_file.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            print(f"📄 {backup_file.name}")
            print(f"   Size: {size} bytes")
            print(f"   Modified: {modified}")
            print("-" * 30)

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Manage user profiles in SOLEil platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all profiles
  python manage_profiles.py list
  
  # List profiles with details
  python manage_profiles.py list --details
  
  # Remove specific profile by email
  python manage_profiles.py remove user@example.com
  
  # Remove specific profile by user ID
  python manage_profiles.py remove 12345
  
  # Remove all profiles (with confirmation)
  python manage_profiles.py remove-all
  
  # List available backups
  python manage_profiles.py backups
  
  # Restore from backup
  python manage_profiles.py restore profiles_backup_20241201_143022.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all profiles')
    list_parser.add_argument('--details', action='store_true', help='Show detailed profile information')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a specific profile')
    remove_parser.add_argument('identifier', help='Email or user ID to remove')
    remove_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Remove all command
    remove_all_parser = subparsers.add_parser('remove-all', help='Remove all profiles (DANGEROUS!)')
    remove_all_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Backup commands
    subparsers.add_parser('backups', help='List available backup files')
    
    restore_parser = subparsers.add_parser('restore', help='Restore profiles from backup')
    restore_parser.add_argument('backup_file', help='Backup file name to restore from')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize profile manager
    manager = ProfileManager()
    
    try:
        if args.command == 'list':
            manager.list_profiles(show_details=args.details)
        
        elif args.command == 'remove':
            manager.remove_profile(args.identifier, force=args.force)
        
        elif args.command == 'remove-all':
            manager.remove_all_profiles(force=args.force)
        
        elif args.command == 'backups':
            manager.list_backups()
        
        elif args.command == 'restore':
            manager.restore_backup(args.backup_file)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
