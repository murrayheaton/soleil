#!/usr/bin/env python3
"""
Quick test script to connect to Google Drive using OAuth2 user authentication.
This is for development/testing only - production should use service accounts.
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def main():
    """Shows basic usage of the Drive v3 API."""
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # You'll need to create OAuth2 credentials in Google Cloud Console
            # Download them as credentials.json
            if not os.path.exists('credentials.json'):
                print("ERROR: Missing credentials.json")
                print("\nTo create OAuth2 credentials:")
                print("1. Go to Google Cloud Console > APIs & Services > Credentials")
                print("2. Create Credentials > OAuth client ID")
                print("3. Application type: Desktop app")
                print("4. Download and save as 'credentials.json'")
                return
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the Drive service
    service = build('drive', 'v3', credentials=creds)

    # List files in your Drive
    print("\n🔍 Searching for folders in your Drive...")
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.folder'",
        pageSize=10,
        fields="nextPageToken, files(id, name, parents)"
    ).execute()
    
    items = results.get('files', [])
    
    if not items:
        print('No folders found.')
    else:
        print('\nFolders found:')
        for item in items:
            print(f"📁 {item['name']} (ID: {item['id']})")
            
    # Look for band-related folders
    print("\n🎵 Searching for band/music folders...")
    results = service.files().list(
        q="name contains 'band' or name contains 'music' or name contains 'source' or name contains 'chart'",
        pageSize=20,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    items = results.get('files', [])
    if items:
        print("\nBand-related items found:")
        for item in items:
            icon = "📁" if item['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
            print(f"{icon} {item['name']} (ID: {item['id']})")

if __name__ == '__main__':
    main()