#!/usr/bin/env python3
"""
Test script to verify Google Drive service account connection and list files.
"""

import os
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.drive.services.drive_service_account import drive_service_account


async def test_connection():
    """Test Google Drive connection and list files."""
    print("=" * 60)
    print("GOOGLE DRIVE SERVICE ACCOUNT TEST")
    print("=" * 60)
    
    # Check environment variables
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    folder_id = os.getenv('GOOGLE_DRIVE_SOURCE_FOLDER_ID')
    
    print(f"\n1. Environment Variables:")
    print(f"   Service Account File: {service_account_file}")
    print(f"   Folder ID: {folder_id}")
    
    if not service_account_file:
        print("   ❌ ERROR: GOOGLE_SERVICE_ACCOUNT_FILE not set!")
        return
    
    if not os.path.exists(service_account_file):
        print(f"   ❌ ERROR: Service account file not found at {service_account_file}")
        return
    
    # Load and check service account email
    try:
        with open(service_account_file, 'r') as f:
            sa_data = json.load(f)
            print(f"   Service Account Email: {sa_data.get('client_email')}")
    except Exception as e:
        print(f"   ❌ ERROR reading service account file: {e}")
        return
    
    # Test authentication
    print(f"\n2. Testing Authentication...")
    authenticated = await drive_service_account.authenticate()
    if not authenticated:
        print("   ❌ FAILED to authenticate with service account!")
        print("   Check that:")
        print("   - Service account file is valid")
        print("   - Required Python packages are installed (google-api-python-client)")
        return
    
    print("   ✅ Successfully authenticated!")
    
    # Test listing files
    print(f"\n3. Listing Files in Folder {folder_id}...")
    try:
        files = await drive_service_account.list_files(folder_id=folder_id)
        
        if not files:
            print("   ⚠️  No files found!")
            print("   Check that:")
            print(f"   - The folder ID {folder_id} is correct")
            print(f"   - The folder is shared with: {sa_data.get('client_email')}")
            print("   - The folder contains files")
        else:
            print(f"   ✅ Found {len(files)} files:")
            
            # Group by type
            pdfs = [f for f in files if f['name'].lower().endswith('.pdf')]
            folders = [f for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
            others = [f for f in files if f not in pdfs and f not in folders]
            
            if folders:
                print(f"\n   📁 Folders ({len(folders)}):")
                for f in folders[:5]:
                    print(f"      - {f['name']}")
                if len(folders) > 5:
                    print(f"      ... and {len(folders) - 5} more")
            
            if pdfs:
                print(f"\n   📄 PDFs ({len(pdfs)}):")
                for f in pdfs[:10]:
                    print(f"      - {f['name']}")
                if len(pdfs) > 10:
                    print(f"      ... and {len(pdfs) - 10} more")
            
            if others:
                print(f"\n   📎 Other Files ({len(others)}):")
                for f in others[:5]:
                    print(f"      - {f['name']} ({f.get('mimeType', 'unknown')})")
                if len(others) > 5:
                    print(f"      ... and {len(others) - 5} more")
    
    except Exception as e:
        print(f"   ❌ ERROR listing files: {e}")
        print("   This might mean:")
        print("   - The folder is not shared with the service account")
        print("   - The folder ID is incorrect")
        print("   - There's a permission issue")
        return
    
    # Test recursive listing
    print(f"\n4. Testing Recursive Listing (including subfolders)...")
    try:
        all_files = await drive_service_account.list_files_recursive(folder_id=folder_id)
        
        # Filter for PDFs
        all_pdfs = [f for f in all_files if f['name'].lower().endswith('.pdf')]
        
        print(f"   Total files (recursive): {len(all_files)}")
        print(f"   Total PDFs: {len(all_pdfs)}")
        
        if all_pdfs:
            print("\n   Chart-like PDFs (matching naming convention):")
            chart_pdfs = []
            for pdf in all_pdfs:
                name = pdf['name']
                # Check if it matches chart naming convention
                if '_' in name and any(trans in name for trans in ['Bb', 'Eb', 'Concert', 'BassClef', 'Chords', 'Lyrics']):
                    chart_pdfs.append(name)
            
            if chart_pdfs:
                print(f"   ✅ Found {len(chart_pdfs)} charts matching naming convention:")
                for chart in chart_pdfs[:10]:
                    print(f"      - {chart}")
                if len(chart_pdfs) > 10:
                    print(f"      ... and {len(chart_pdfs) - 10} more")
            else:
                print("   ⚠️  No PDFs match the naming convention 'SongName_Transposition.pdf'")
                print("   Expected formats: SongName_Bb.pdf, SongName_Eb.pdf, etc.")
    
    except Exception as e:
        print(f"   ❌ ERROR in recursive listing: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_connection())