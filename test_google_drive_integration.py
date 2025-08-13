#!/usr/bin/env python3
"""
Test script to verify Google Drive integration is working
"""

import sys
import os
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "band-platform" / "backend"))

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_google_drive_integration():
    """Test the Google Drive chart integration"""
    
    print(f"{BLUE}🎸 Testing SOLEil Google Drive Integration{RESET}\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / "band-platform" / "backend" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"{GREEN}✅ Environment file loaded{RESET}")
    else:
        print(f"{RED}❌ No .env file found at {env_path}{RESET}")
        return
    
    # Check credentials
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret:
        print(f"{GREEN}✅ Google OAuth credentials found{RESET}")
        print(f"   Client ID: {client_id[:30]}...")
    else:
        print(f"{RED}❌ Google OAuth credentials missing{RESET}")
        return
    
    # Test backend API
    base_url = "http://localhost:8000"
    
    print(f"\n{BLUE}Testing Backend API...{RESET}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✅ Backend is running{RESET}")
        else:
            print(f"{YELLOW}⚠️  Backend returned status {response.status_code}{RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Backend is not running. Start it with: ./start_services.sh{RESET}")
        return
    
    # Test auth status
    try:
        response = requests.get(f"{base_url}/api/auth/google/status", timeout=5)
        data = response.json()
        
        if data.get('authenticated'):
            print(f"{GREEN}✅ Google Drive authenticated{RESET}")
            print(f"   User: {data.get('user_email', 'Unknown')}")
        else:
            print(f"{YELLOW}⚠️  Not authenticated with Google Drive{RESET}")
            
            # Get auth URL
            response = requests.get(f"{base_url}/api/auth/google/url", timeout=5)
            if response.status_code == 200:
                auth_data = response.json()
                print(f"\n{BLUE}To authenticate:{RESET}")
                print(f"1. Visit this URL:\n   {auth_data.get('auth_url', 'URL not available')}")
                print(f"2. Complete the OAuth flow")
                print(f"3. Run this test again")
    except Exception as e:
        print(f"{RED}❌ Error checking auth status: {e}{RESET}")
    
    # Test charts endpoint
    print(f"\n{BLUE}Testing Chart Endpoints...{RESET}")
    
    try:
        response = requests.get(f"{base_url}/api/charts", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            chart_count = data.get('total', 0)
            print(f"{GREEN}✅ Charts endpoint working{RESET}")
            print(f"   Found {chart_count} charts")
            
            # Show first few charts if available
            charts = data.get('charts', [])
            if charts:
                print(f"\n   First few charts:")
                for chart in charts[:3]:
                    print(f"   - {chart.get('name', 'Unknown')}")
        elif response.status_code == 401:
            print(f"{YELLOW}⚠️  Authentication required for charts{RESET}")
            print(f"   Please authenticate with Google Drive first")
        else:
            print(f"{YELLOW}⚠️  Charts endpoint returned status {response.status_code}{RESET}")
            
    except Exception as e:
        print(f"{RED}❌ Error testing charts: {e}{RESET}")
    
    # Summary
    print(f"\n{BLUE}={'='*50}{RESET}")
    print(f"{BLUE}Summary:{RESET}")
    print(f"- OAuth Credentials: {GREEN}Configured{RESET}" if client_id else f"{RED}Missing{RESET}")
    print(f"- Backend Server: {GREEN}Running{RESET}" if 'response' in locals() else f"{RED}Not Running{RESET}")
    print(f"- Google Drive: Check authentication status above")
    print(f"- Chart API: Check status above")
    
    print(f"\n{BLUE}Next Steps:{RESET}")
    print("1. If backend not running: ./start_services.sh")
    print("2. If not authenticated: Follow the OAuth URL above")
    print("3. If authenticated: Charts should be accessible!")


if __name__ == "__main__":
    try:
        test_google_drive_integration()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{RESET}")