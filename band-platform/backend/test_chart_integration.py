"""
Test script for Google Drive chart integration.

This script tests the connection between the chart service and Google Drive APIs.
"""

import asyncio
import logging
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(__file__))

from modules.content.services.chart_service import ChartService
from app.services.google_drive_oauth import drive_oauth_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_google_drive_auth():
    """Test Google Drive authentication."""
    print("Testing Google Drive authentication...")
    
    try:
        authenticated = await drive_oauth_service.authenticate()
        if authenticated:
            print("✅ Google Drive authentication successful!")
            return True
        else:
            print("❌ Google Drive authentication failed")
            print("Need to authenticate first. Get auth URL...")
            auth_url = await drive_oauth_service.get_auth_url()
            print(f"🔗 Visit this URL to authenticate: {auth_url}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False


async def test_chart_service():
    """Test chart service functionality."""
    print("\nTesting chart service...")
    
    try:
        chart_service = ChartService()
        
        # Test listing charts
        print("Testing chart listing...")
        charts = await chart_service.list_charts(limit=5)
        print(f"✅ Found {len(charts)} charts")
        
        if charts:
            # Test getting a specific chart
            chart_id = charts[0].id
            print(f"Testing specific chart retrieval for ID: {chart_id}")
            chart = await chart_service.get_chart(chart_id)
            if chart:
                print(f"✅ Retrieved chart: {chart.title}")
            else:
                print("❌ Failed to retrieve specific chart")
            
            # Test searching charts
            print("Testing chart search...")
            search_results = await chart_service.search_charts("test", limit=3)
            print(f"✅ Search returned {len(search_results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Chart service error: {e}")
        return False


async def test_chart_folders():
    """Test chart folder listing."""
    print("\nTesting chart folder listing...")
    
    try:
        chart_service = ChartService()
        folders = await chart_service.get_chart_folders()
        print(f"✅ Found {len(folders)} folders with charts")
        
        for folder in folders[:3]:  # Show first 3 folders
            print(f"  📁 {folder.get('name', 'Unknown')}: {folder.get('chart_count', 0)} charts")
        
        return True
        
    except Exception as e:
        print(f"❌ Folder listing error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🎵 SOLEil Chart Service Integration Test")
    print("=" * 50)
    
    # Test authentication
    auth_success = await test_google_drive_auth()
    
    if auth_success:
        # Test chart service
        await test_chart_service()
        await test_chart_folders()
    else:
        print("\n⚠️  Skipping chart service tests - authentication required")
        print("Please authenticate with Google Drive first using the provided URL")
    
    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(main())