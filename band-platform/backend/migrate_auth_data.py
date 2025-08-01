#!/usr/bin/env python3
"""
Migrate existing authentication data to new consolidated format.
Run this before deploying the new authentication system.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

def migrate_auth_data():
    """Migrate and consolidate authentication data."""
    print("Starting authentication data migration...")
    
    # Backup existing data
    backup_dir = Path("auth_migration_backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Files to check for migration
    auth_files = [
        "google_token.json",
        "user_profiles.json",
        "session_data.json"  # If exists
    ]
    
    for file in auth_files:
        if Path(file).exists():
            shutil.copy2(file, backup_dir / f"{file}.backup")
            print(f"Backed up {file}")
    
    # Migrate token data
    if Path("google_token.json").exists():
        with open("google_token.json", 'r') as f:
            tokens = json.load(f)
        
        # Add migration timestamp
        tokens['migrated_at'] = datetime.now().isoformat()
        
        # Ensure all required fields exist
        tokens.setdefault('auth_method', 'oauth')
        tokens.setdefault('created_at', datetime.now().isoformat())
        
        # Add expires_at if not present
        if 'expires_at' not in tokens and 'expires_in' in tokens:
            tokens['expires_at'] = (
                datetime.now().timestamp() + 
                tokens.get('expires_in', 3600)
            )
        
        with open("google_token.json", 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print("Token data migrated successfully")
    
    # Migrate user profiles
    if Path("user_profiles.json").exists():
        with open("user_profiles.json", 'r') as f:
            profiles = json.load(f)
        
        # Update profile format if needed
        for user_id, profile in profiles.items():
            # Ensure consistent fields
            profile.setdefault('id', user_id)
            profile.setdefault('created_at', datetime.now().isoformat())
            profile.setdefault('updated_at', datetime.now().isoformat())
            profile.setdefault('instruments', [])
            profile.setdefault('ui_scale', 'small')
            
            # Ensure proper transposition symbols
            if 'transposition' in profile:
                if profile['transposition'] == 'Bb':
                    profile['transposition'] = 'B♭'
                elif profile['transposition'] == 'Eb':
                    profile['transposition'] = 'E♭'
        
        with open("user_profiles.json", 'w') as f:
            json.dump(profiles, f, indent=2)
        
        print(f"Migrated {len(profiles)} user profiles")
    
    print("\nMigration complete! Backup stored in:", backup_dir)
    print("If issues occur, restore from backup files.")

if __name__ == "__main__":
    migrate_auth_data()