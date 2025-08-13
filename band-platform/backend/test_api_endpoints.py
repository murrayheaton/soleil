"""
Test script for chart API endpoints.

This script demonstrates how the Google Drive integration works with the API endpoints.
"""

import requests
import json


def test_api_endpoints():
    """Test the chart API endpoints."""
    base_url = "http://localhost:8000/api/content"
    
    print("🎵 Testing SOLEil Chart API Endpoints")
    print("=" * 50)
    
    # Test authentication status
    print("1. Testing Google Drive authentication status...")
    try:
        response = requests.get(f"{base_url}/auth/google/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Auth Status: {data.get('message', 'Unknown')}")
            if not data.get('authenticated', False):
                print(f"🔗 Auth URL: {data.get('auth_url', 'Not available')}")
        else:
            print(f"❌ Auth status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to check auth status: {e}")
    
    print()
    
    # Test chart listing
    print("2. Testing chart listing...")
    try:
        response = requests.get(f"{base_url}/charts?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Charts endpoint responded: {data.get('total', 0)} charts found")
        elif response.status_code == 401:
            print("⚠️  Charts listing requires authentication")
        else:
            print(f"❌ Charts listing failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed to test chart listing: {e}")
    
    print()
    
    # Test folder listing
    print("3. Testing folder listing...")
    try:
        response = requests.get(f"{base_url}/folders")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Folders endpoint responded: {len(data.get('folders', []))} folders found")
        elif response.status_code == 401:
            print("⚠️  Folder listing requires authentication")
        else:
            print(f"❌ Folder listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to test folder listing: {e}")
    
    print()
    
    # Test search
    print("4. Testing chart search...")
    try:
        response = requests.get(f"{base_url}/charts/search?query=test&limit=3")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search endpoint responded: {data.get('total', 0)} results")
        elif response.status_code == 401:
            print("⚠️  Chart search requires authentication")
        else:
            print(f"❌ Chart search failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to test chart search: {e}")
    
    print("\n" + "=" * 50)
    print("API endpoint tests completed!")
    print("\nNote: Authentication is required for most endpoints.")
    print("Visit /api/content/auth/google/url to get the authentication URL.")


if __name__ == "__main__":
    test_api_endpoints()