"""
Google Drive service using Service Account authentication.
This allows all band members to access the same shared Google Drive
without needing individual permissions.
"""

import os
import logging
from typing import Optional, List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import io

logger = logging.getLogger(__name__)


class GoogleDriveServiceAccount:
    """
    Google Drive service using Service Account authentication.
    This is used to access a shared band Google Drive that all users can access.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    def __init__(self):
        self.creds = None
        self.service = None
        self.service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        self.shared_folder_id = os.getenv('GOOGLE_DRIVE_SOURCE_FOLDER_ID')

    async def authenticate(self) -> bool:
        """
        Authenticate using service account credentials.
        """
        if not self.service_account_file:
            logger.error("GOOGLE_SERVICE_ACCOUNT_FILE not configured")
            return False
            
        if not os.path.exists(self.service_account_file):
            logger.error(f"Service account file not found: {self.service_account_file}")
            return False

        try:
            self.creds = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=self.SCOPES
            )
            
            self.service = build("drive", "v3", credentials=self.creds)
            logger.info("Successfully authenticated with service account")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with service account: {e}")
            return False

    async def list_files(
        self, 
        folder_id: Optional[str] = None,
        page_size: int = 100,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in a Google Drive folder.
        """
        if not self.service:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Google Drive")

        try:
            folder_id = folder_id or self.shared_folder_id
            
            # Build query
            if query:
                q = query
            else:
                q = f"'{folder_id}' in parents and trashed=false"
            
            results = (
                self.service.files()
                .list(
                    q=q,
                    pageSize=page_size,
                    fields="files(id, name, mimeType, modifiedTime, size, parents)",
                    orderBy="name"
                )
                .execute()
            )

            return results.get("files", [])

        except HttpError as error:
            logger.error(f"Error listing files: {error}")
            return []

    async def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file.
        """
        if not self.service:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Google Drive")

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, parents"
            ).execute()
            
            return file

        except HttpError as error:
            logger.error(f"Error getting file metadata: {error}")
            return None

    async def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Download file content from Google Drive.
        """
        if not self.service:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Google Drive")

        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}% complete.")
            
            return file_content.getvalue()

        except HttpError as error:
            logger.error(f"Error downloading file: {error}")
            return None

    async def list_files_recursive(
        self, 
        folder_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recursively list all files in a folder and its subfolders.
        """
        folder_id = folder_id or self.shared_folder_id
        all_files = []
        
        # Get files in current folder
        files = await self.list_files(folder_id=folder_id, page_size=1000)
        
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively get files from subfolder
                subfolder_files = await self.list_files_recursive(file['id'])
                all_files.extend(subfolder_files)
            else:
                all_files.append(file)
        
        return all_files


# Global instance
drive_service_account = GoogleDriveServiceAccount()