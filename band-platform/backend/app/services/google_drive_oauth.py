"""
Google Drive service using OAuth2 user authentication.
This is more secure than service account keys and works with organization policies.
"""

import os
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import settings


class GoogleDriveOAuthService:
    """
    Google Drive service using OAuth2 user authentication.
    More secure than service accounts for organizations with strict policies.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",  # Create/manage files created by the app
    ]

    def __init__(self):
        self.creds = None
        self.service = None
        self.token_file = "google_token.json"

    async def get_auth_url(self) -> str:
        """
        Generate OAuth2 authorization URL for user to authenticate.
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri],
                }
            },
            scopes=self.SCOPES,
            redirect_uri=settings.google_redirect_uri,
        )

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
        )

        return auth_url

    async def handle_callback(self, authorization_code: str) -> bool:
        """
        Handle OAuth2 callback and save credentials.
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [settings.google_redirect_uri],
                    }
                },
                scopes=self.SCOPES,
                redirect_uri=settings.google_redirect_uri,
            )

            flow.fetch_token(code=authorization_code)

            # Save credentials
            creds = flow.credentials
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

            self.creds = creds
            return True

        except Exception as e:
            print(f"Error handling OAuth callback: {e}")
            return False

    async def authenticate(self) -> bool:
        """
        Load saved credentials or return False if authentication needed.
        """
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(
                self.token_file, self.SCOPES
            )

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                # Save refreshed token
                with open(self.token_file, "w") as token:
                    token.write(self.creds.to_json())
            else:
                return False

        self.service = build("drive", "v3", credentials=self.creds)
        return True

    async def list_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        List contents of a Google Drive folder.
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="files(id, name, mimeType, modifiedTime)",
                    pageSize=100,
                )
                .execute()
            )

            return results.get("files", [])

        except HttpError as error:
            print(f"Error listing folder contents: {error}")
            return []

    async def get_file_content(self, file_id: str) -> bytes:
        """
        Download file content from Google Drive.
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            request = self.service.files().get_media(fileId=file_id)
            return request.execute()

        except HttpError as error:
            print(f"Error downloading file: {error}")
            return None

    async def create_folder(
        self, name: str, parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a folder in Google Drive.
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")

        file_metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}

        if parent_id:
            file_metadata["parents"] = [parent_id]

        try:
            folder = (
                self.service.files().create(body=file_metadata, fields="id").execute()
            )

            return folder.get("id")

        except HttpError as error:
            print(f"Error creating folder: {error}")
            return None

    async def share_folder(
        self, folder_id: str, email: str, role: str = "reader"
    ) -> bool:
        """
        Share a folder with a user.
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            permission = {"type": "user", "role": role, "emailAddress": email}

            self.service.permissions().create(
                fileId=folder_id, body=permission, sendNotificationEmail=False
            ).execute()

            return True

        except HttpError as error:
            print(f"Error sharing folder: {error}")
            return False


# Singleton instance
drive_oauth_service = GoogleDriveOAuthService()
