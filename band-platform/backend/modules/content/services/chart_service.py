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

# Import drive service account for shared band drive access
from modules.drive.services.drive_service_account import drive_service_account

from io import BytesIO
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class ChartService:
    """Service for managing charts with Google Drive integration."""
    
    def __init__(self, user_email: str = "murray@projectbrass.live"):
        """Initialize the chart service."""
        self.user_email = user_email
        self.drive_service = None
        # Use the master assets folder - we'll scan recursively for all content
        self._master_folder_id = os.getenv("GOOGLE_DRIVE_SOURCE_FOLDER_ID")
        
    async def _get_drive_service(self):
        """Get authenticated Google Drive service using service account."""
        if not self.drive_service:
            # Authenticate with service account for shared band drive access
            authenticated = await drive_service_account.authenticate()
            if not authenticated:
                raise AuthenticationError(f"Failed to authenticate with Google Drive service account. Please check service account configuration.")
            
            self.drive_service = drive_service_account
        
        return self.drive_service
    
    async def _get_master_folder(self) -> str:
        """Get the master Google Drive folder for all assets."""
        if not self._master_folder_id:
            # Use root folder if not configured
            logger.warning(f"No master folder configured, using root folder")
            self._master_folder_id = "root"
        return self._master_folder_id
    
    async def list_charts(
        self,
        folder_id: Optional[str] = None,
        instrument: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chart]:
        """List charts from Google Drive with recursive scanning and intelligent filtering."""
        try:
            drive_service = await self._get_drive_service()
            target_folder = folder_id or await self._get_master_folder()
            
            # Recursively get all files from the master folder and subfolders
            all_files = await self._get_files_recursive(drive_service, target_folder)
            
            # Filter for chart files based on naming conventions and file types
            charts = []
            for file in all_files:
                # Parse the file to see if it's a chart
                parsed_file = await self._parse_file_to_chart(file)
                
                # Only include files that:
                # 1. Parse successfully as charts
                # 2. Are PDF or image files (common chart formats)
                # 3. Match the instrument filter if provided
                if parsed_file:
                    # Charts must be PDFs only
                    mime_type = file.get('mimeType', '')
                    filename = file.get('name', '').lower()
                    
                    is_pdf = (
                        mime_type == 'application/pdf' or 
                        filename.endswith('.pdf')
                    )
                    
                    if is_pdf:
                        # Apply instrument filter if provided
                        if not instrument or self._matches_instrument(parsed_file, instrument):
                            charts.append(parsed_file)
            
            # Apply pagination
            paginated_charts = charts[offset:offset + limit]
            
            logger.info(f"Found {len(charts)} total charts, returning {len(paginated_charts)} (offset={offset}, limit={limit})")
            return paginated_charts
            
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
    
    async def _get_files_recursive(self, drive_service, folder_id: str) -> List[dict]:
        """Recursively get all files from a folder and its subfolders."""
        all_files = []
        
        try:
            # Get files in current folder
            files = await drive_service.list_files(
                folder_id=folder_id,
                page_size=1000  # Get more files at once for efficiency
            )
            
            for file in files:
                mime_type = file.get('mimeType', '')
                
                # If it's a folder, recursively get its contents
                if mime_type == 'application/vnd.google-apps.folder':
                    subfolder_files = await self._get_files_recursive(drive_service, file['id'])
                    all_files.extend(subfolder_files)
                else:
                    # Add the file to our list
                    all_files.append(file)
                    
        except Exception as e:
            logger.warning(f"Error scanning folder {folder_id}: {e}")
            
        return all_files
    
    def _matches_instrument(self, chart: Chart, instrument: str) -> bool:
        """Check if a chart matches the requested instrument/transposition."""
        instrument_lower = instrument.lower()
        
        # Check if the chart's key matches the instrument transposition
        if chart.key and chart.key.lower() == instrument_lower:
            return True
            
        # Check if any of the chart's instruments match
        if chart.instruments:
            for inst in chart.instruments:
                if instrument_lower in inst.lower():
                    return True
                    
        # Check special cases for transposition groups
        transposition_groups = {
            'bb': ['trumpet', 'tenor'],
            'eb': ['alto', 'bari'],
            'concert': ['violin'],
            'bassclef': ['trombone'],
            'chords': ['piano', 'keys', 'guitar', 'bass', 'drums'],
            'lyrics': ['vocal', 'voice', 'singer', 'lyric']
        }
        
        # Check if the requested instrument is a transposition group
        if instrument_lower in transposition_groups:
            chart_text = f"{chart.title} {chart.filename} {' '.join(chart.instruments or [])}".lower()
            for keyword in transposition_groups[instrument_lower]:
                if keyword in chart_text:
                    return True
                    
        return False
    
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
            target_folder = folder_id or await self._get_master_folder()
            
            # Get all files recursively
            all_files = await self._get_files_recursive(drive_service, target_folder)
            
            # Filter files that match the search query
            matching_charts = []
            query_lower = query.lower()
            
            for file in all_files:
                filename = file.get('name', '').lower()
                
                # Check if file matches search query
                if query_lower in filename:
                    # Charts must be PDFs only
                    mime_type = file.get('mimeType', '')
                    is_pdf = (
                        mime_type == 'application/pdf' or 
                        filename.endswith('.pdf')
                    )
                    
                    if is_pdf:
                        chart = await self._parse_file_to_chart(file)
                        if chart and (not instrument or self._matches_instrument(chart, instrument)):
                            matching_charts.append(chart)
                            if len(matching_charts) >= limit:
                                break
            
            logger.info(f"Search for '{query}' returned {len(matching_charts)} charts")
            return matching_charts
            
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
        """Get available folders that contain charts from Google Drive."""
        try:
            drive_service = await self._get_drive_service()
            
            # Start from the master folder
            master_folder = await self._get_master_folder()
            
            # Get all folders recursively
            all_folders = await self._get_folders_with_charts(drive_service, master_folder)
            
            logger.info(f"Found {len(all_folders)} folders containing charts")
            return all_folders
            
        except Exception as e:
            logger.error(f"Failed to get chart folders: {e}")
            raise
    
    async def _get_folders_with_charts(self, drive_service, folder_id: str, path: str = "") -> List[dict]:
        """Recursively find all folders that contain chart files."""
        folders_with_charts = []
        
        try:
            # Get all items in current folder
            items = await drive_service.list_files(
                folder_id=folder_id,
                page_size=1000
            )
            
            chart_count = 0
            subfolders = []
            
            for item in items:
                mime_type = item.get('mimeType', '')
                
                if mime_type == 'application/vnd.google-apps.folder':
                    # It's a subfolder - we'll process it recursively
                    subfolders.append(item)
                else:
                    # Check if it's a PDF chart file
                    filename = item.get('name', '').lower()
                    is_pdf = (
                        mime_type == 'application/pdf' or 
                        filename.endswith('.pdf')
                    )
                    
                    if is_pdf:
                        chart_count += 1
            
            # If this folder contains charts, add it to the list
            if chart_count > 0:
                folder_name = await self._get_folder_name(drive_service, folder_id)
                folders_with_charts.append({
                    'id': folder_id,
                    'name': folder_name,
                    'path': path,
                    'chart_count': chart_count
                })
            
            # Recursively process subfolders
            for subfolder in subfolders:
                subfolder_path = f"{path}/{subfolder['name']}" if path else subfolder['name']
                subfolder_results = await self._get_folders_with_charts(
                    drive_service, 
                    subfolder['id'], 
                    subfolder_path
                )
                folders_with_charts.extend(subfolder_results)
                
        except Exception as e:
            logger.warning(f"Error scanning folder {folder_id}: {e}")
            
        return folders_with_charts
    
    async def _get_folder_name(self, drive_service, folder_id: str) -> str:
        """Get the name of a folder by its ID."""
        try:
            if folder_id == await self._get_master_folder():
                return "Master Assets"
            metadata = await drive_service.get_file_metadata(folder_id)
            return metadata.get('name', 'Unknown Folder')
        except Exception:
            return "Unknown Folder"
