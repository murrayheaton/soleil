"""
Chart service for Google Drive integration.

This service connects the existing Google Drive services to the chart API endpoints,
allowing bands to list, search, and download charts from their Google Drive accounts.
"""

import asyncio
import logging
from typing import List, Optional, AsyncGenerator
from datetime import datetime

from ..models.content import Chart, ChartListResponse
from .soleil_content_parser import parse_filename

# Import from the main app services
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.services.google_drive import GoogleDriveService, DriveAPIError, AuthenticationError
from app.config import settings

from io import BytesIO
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class ChartService:
    """Service for managing charts with Google Drive integration."""
    
    def __init__(self, user_email: str = "murray@projectbrass.live"):
        """Initialize the chart service."""
        self.user_email = user_email
        self.drive_service = None
        self._default_folder_id = None  # Will be set from config or environment
        
        # Configure default charts folder for murray@projectbrass.live
        # This should be set via environment variable in production
        if user_email == "murray@projectbrass.live":
            self._default_folder_id = os.getenv("GOOGLE_DRIVE_CHARTS_FOLDER_ID")
        
    async def _get_drive_service(self) -> GoogleDriveService:
        """Get authenticated Google Drive service."""
        if not self.drive_service:
            # For now, we'll skip authentication until we fix the import issues
            # TODO: Implement proper authentication flow
            raise Exception(f"Google Drive authentication not yet implemented. Please use the drive module endpoints instead.")
            
            # Original code commented out:
            # authenticated = await drive_oauth_service.authenticate()
            # if not authenticated:
            #     raise Exception(f"Google Drive authentication required for user {self.user_email}. Please authenticate first.")
            
            # # Create authenticated GoogleDriveService
            # self.drive_service = GoogleDriveService(credentials=drive_oauth_service.creds)
        
        return self.drive_service
    
    async def _get_default_folder(self) -> str:
        """Get the default Google Drive folder for charts."""
        if not self._default_folder_id:
            # For murray@projectbrass.live, use root folder if not configured
            logger.warning(f"No default charts folder configured for {self.user_email}, using root folder")
            self._default_folder_id = "root"
        return self._default_folder_id
    
    async def list_charts(
        self,
        folder_id: Optional[str] = None,
        instrument: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chart]:
        """List charts from Google Drive with optional filtering."""
        try:
            drive_service = await self._get_drive_service()
            target_folder = folder_id or await self._get_default_folder()
            
            # List files from Google Drive folder
            files = await drive_service.list_files(
                folder_id=target_folder,
                max_results=limit + offset
            )
            
            # Parse chart metadata from filenames
            charts = []
            for file in files[offset:offset + limit]:
                chart = await self._parse_file_to_chart(file)
                if chart and (not instrument or instrument.lower() in chart.instruments):
                    charts.append(chart)
            
            logger.info(f"Listed {len(charts)} charts from folder {target_folder}")
            return charts
            
        except Exception as e:
            logger.error(f"Failed to list charts: {e}")
            raise
    
    async def get_chart(self, chart_id: str) -> Optional[Chart]:
        """Get chart metadata by Google Drive file ID."""
        try:
            drive_service = await self._get_drive_service()
            
            # Get file metadata from Google Drive
            file_metadata = await drive_service.get_file_metadata(chart_id)
            if not file_metadata:
                return None
            
            # Parse chart metadata
            chart = await self._parse_file_to_chart(file_metadata)
            logger.info(f"Retrieved chart {chart_id}")
            return chart
            
        except Exception as e:
            logger.error(f"Failed to get chart {chart_id}: {e}")
            raise
    
    async def download_chart(self, chart_id: str) -> Optional[AsyncGenerator[bytes, None]]:
        """Download chart file from Google Drive with streaming."""
        try:
            drive_service = await self._get_drive_service()
            
            # Download file content from Google Drive
            file_content = await drive_service.download_file(chart_id)
            if not file_content:
                return None
            
            # Create streaming response from bytes
            async def stream_file():
                chunk_size = 8192
                file_stream = BytesIO(file_content)
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            
            logger.info(f"Streaming chart {chart_id}")
            return stream_file()
            
        except Exception as e:
            logger.error(f"Failed to download chart {chart_id}: {e}")
            raise
    
    async def search_charts(
        self,
        query: str,
        folder_id: Optional[str] = None,
        instrument: Optional[str] = None,
        limit: int = 20
    ) -> List[Chart]:
        """Search charts by name or content in Google Drive."""
        try:
            drive_service = await self._get_drive_service()
            target_folder = folder_id or await self._get_default_folder()
            
            # Build search query for Google Drive API
            search_query = f"name contains '{query}'"
            
            # Search files in Google Drive
            search_results = await drive_service.list_files(
                folder_id=target_folder,
                query=search_query,
                max_results=limit * 2  # Get more results for filtering
            )
            
            # Parse and filter results
            charts = []
            for file in search_results:
                chart = await self._parse_file_to_chart(file)
                if chart and (not instrument or instrument.lower() in chart.instruments):
                    charts.append(chart)
                    if len(charts) >= limit:
                        break
            
            logger.info(f"Search for '{query}' returned {len(charts)} charts")
            return charts
            
        except Exception as e:
            logger.error(f"Failed to search charts: {e}")
            raise
    
    async def _parse_file_to_chart(self, file_metadata: dict) -> Optional[Chart]:
        """Parse Google Drive file metadata into Chart model."""
        try:
            # Extract basic file info
            file_id = file_metadata.get('id')
            filename = file_metadata.get('name', '')
            mime_type = file_metadata.get('mimeType', '')
            size = file_metadata.get('size', 0)
            created_time = file_metadata.get('createdTime')
            modified_time = file_metadata.get('modifiedTime')
            
            # Parse filename using SOLEIL content parser
            parsed = parse_filename(filename)
            
            # Create Chart model using SOLEIL parsing system
            chart = Chart(
                id=file_id,
                filename=filename,
                title=parsed.song_title,
                instruments=[],  # Will be populated based on key and user's instruments
                key=parsed.key,
                tempo=parsed.tempo,
                time_signature=None,  # Not in current parsing
                difficulty=None,  # Not in current parsing
                mime_type=mime_type,
                size=size,
                created_at=datetime.fromisoformat(created_time.replace('Z', '+00:00')) if created_time else None,
                modified_at=datetime.fromisoformat(modified_time.replace('Z', '+00:00')) if modified_time else None,
                google_drive_id=file_id,
                download_url=f"/charts/{file_id}/download"
            )
            
            return chart
            
        except Exception as e:
            logger.warning(f"Failed to parse file {file_metadata.get('name', 'unknown')}: {e}")
            return None
    
    async def get_chart_folders(self) -> List[dict]:
        """Get available chart folders from Google Drive."""
        try:
            drive_service = await self._get_drive_service()
            
            # List folders from the default folder
            default_folder = await self._get_default_folder()
            
            # Search for folders in the default folder
            folder_query = "mimeType='application/vnd.google-apps.folder'"
            folders = await drive_service.list_files(
                folder_id=default_folder,
                query=folder_query,
                max_results=100
            )
            
            # Filter folders that contain chart files
            chart_folders = []
            for folder in folders:
                chart_count = await self._count_charts_in_folder(folder['id'])
                if chart_count > 0:
                    folder_data = {
                        'id': folder['id'],
                        'name': folder['name'],
                        'chart_count': chart_count
                    }
                    chart_folders.append(folder_data)
            
            logger.info(f"Found {len(chart_folders)} chart folders")
            return chart_folders
            
        except Exception as e:
            logger.error(f"Failed to get chart folders: {e}")
            raise
    
    async def _count_charts_in_folder(self, folder_id: str) -> int:
        """Count the number of chart files in a folder."""
        try:
            drive_service = await self._get_drive_service()
            files = await drive_service.list_files(
                folder_id=folder_id,
                max_results=1000  # Reasonable limit for counting
            )
            return len(files)
        except Exception:
            return 0
