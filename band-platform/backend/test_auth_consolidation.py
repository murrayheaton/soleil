#!/usr/bin/env python3
"""
Test script to validate authentication consolidation
"""

import os
import json
from pathlib import Path

def test_auth_consolidation():
    """Test that authentication consolidation was successful."""
    print("🔐 Testing Authentication Consolidation")
    print("=" * 50)
    
    # Test 1: Check that .env.production exists and has real secrets
    print("\n1. Testing .env.production consolidation...")
    env_prod_path = Path(".env.production")
    if env_prod_path.exists():
        with open(env_prod_path, 'r') as f:
            content = f.read()
            
        # Check for real Google credentials
        if "360999037847" in content:
            print("   ✅ Real Google Client ID found")
        else:
            print("   ❌ Google Client ID missing or placeholder")
            
        if "GOCSPX-" in content:
            print("   ✅ Real Google Client Secret found")
        else:
            print("   ❌ Google Client Secret missing or placeholder")
            
        if "solepower.live" in content:
            print("   ✅ Production URLs configured")
        else:
            print("   ❌ Production URLs not configured")
    else:
        print("   ❌ .env.production not found")
    
    # Test 2: Check token manager implementation
    print("\n2. Testing token manager implementation...")
    start_server_path = Path("start_server.py")
    if start_server_path.exists():
        with open(start_server_path, 'r') as f:
            content = f.read()
            
        if "class TokenManager" in content:
            print("   ✅ TokenManager class implemented")
        else:
            print("   ❌ TokenManager class not found")
            
        if "_refresh_token" in content:
            print("   ✅ Token refresh functionality implemented")
        else:
            print("   ❌ Token refresh functionality missing")
            
        if "SessionMiddleware" in content:
            print("   ✅ Session middleware configured")
        else:
            print("   ❌ Session middleware not configured")
    else:
        print("   ❌ start_server.py not found")
    
    # Test 3: Check migrated auth data
    print("\n3. Testing migrated authentication data...")
    
    # Check google_token.json
    if Path("google_token.json").exists():
        with open("google_token.json", 'r') as f:
            tokens = json.load(f)
            
        if "expires_at" in tokens:
            print("   ✅ Token expiration timestamp added")
        else:
            print("   ❌ Token expiration timestamp missing")
            
        if "migrated_at" in tokens:
            print("   ✅ Migration timestamp found")
        else:
            print("   ❌ Migration timestamp missing")
            
        if "user_email" in tokens:
            print(f"   ✅ User email preserved: {tokens['user_email']}")
        else:
            print("   ❌ User email missing")
    else:
        print("   ❌ google_token.json not found")
        
    # Check user_profiles.json
    if Path("user_profiles.json").exists():
        with open("user_profiles.json", 'r') as f:
            profiles = json.load(f)
            
        print(f"   ✅ {len(profiles)} user profiles found")
        
        for email, profile in profiles.items():
            if "created_at" in profile and "updated_at" in profile:
                print(f"   ✅ Profile timestamps added for {email}")
            else:
                print(f"   ❌ Profile timestamps missing for {email}")
                
            # Check for proper Unicode flat symbols
            if "transposition" in profile:
                transposition = profile["transposition"]
                if "♭" in transposition:
                    print(f"   ✅ Proper flat symbol: {transposition}")
                else:
                    print(f"   ⚠️  Transposition format: {transposition}")
    else:
        print("   ❌ user_profiles.json not found")
    
    # Test 4: Check backup files exist
    print("\n4. Testing backup integrity...")
    backup_dir = Path("auth_migration_backup")
    if backup_dir.exists():
        backup_files = list(backup_dir.glob("*.backup"))
        print(f"   ✅ {len(backup_files)} backup files created")
        for backup_file in backup_files:
            print(f"     - {backup_file.name}")
    else:
        print("   ❌ No backup directory found")
    
    # Test 5: Check Docker configuration
    print("\n5. Testing Docker configuration...")
    dockerfile_path = Path("Dockerfile")
    if dockerfile_path.exists():
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            
        if 'CMD ["python", "start_server.py"]' in content:
            print("   ✅ Docker configured to use start_server.py")
        else:
            print("   ❌ Docker still using old configuration")
    else:
        print("   ❌ Dockerfile not found")
    
    print("\n" + "=" * 50)
    print("🎯 Authentication Consolidation Test Complete")
    print("\nNext steps:")
    print("1. Run cleanup script: ./cleanup_redundant_files.sh")
    print("2. Test locally with: python start_server.py")
    print("3. Deploy to production with verified secrets")

if __name__ == "__main__":
    test_auth_consolidation()