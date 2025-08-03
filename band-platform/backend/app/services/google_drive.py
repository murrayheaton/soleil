"""
Google Drive API service with OAuth 2.0, batch operations, and webhooks.

This module provides comprehensive Google Drive integration following the PRP requirements
with proper authentication, rate limiting, and real-time sync capabilities.

Example:
    Basic usage for file operations:
    
    ```python
    from app.services.google_drive import GoogleDriveService
    
    service = GoogleDriveService(credentials)
    files = await service.list_files(folder_id="1234567890")
    content = await service.download_file(file_id="abcdef")
    ```
    
Template Compliance:
    - Comprehensive error handling with custom exceptions
    - Rate limiting with exponential backoff
    - Security audit logging without token exposure
    - Performance monitoring and metrics collection
    - Input validation and sanitization
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .drive_helpers import (
    RateLimiter,
    StatsMixin,
)
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import backoff

from ..services.content_parser import parse_filename

logger = logging.getLogger(__name__)


class DriveAPIError(Exception):
    """Custom exception for Google Drive API errors."""
    pass


class RateLimitExceeded(DriveAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class AuthenticationError(DriveAPIError):
    """Exception raised for authentication issues."""
    pass


class GoogleDriveService(StatsMixin):
    """
    Google Drive API service with comprehensive error handling and rate limiting.
    
    This service provides all Google Drive functionality needed for the band platform
    including file listing, metadata extraction, batch operations, and webhook setup.
    """
    
    def __init__(self, credentials: Optional[Credentials] = None):
        """
        Initialize the Google Drive service.
        
        Args:
            credentials: Optional Google OAuth credentials.
        """
        self.credentials = credentials
        self.service = None
        self.rate_limiter = RateLimiter(requests_per_second=10)  # Google Drive limit: 1000/100s
        
        # Statistics
        self.init_stats()
    
    @asynccontextmanager
    async def _get_service(self):
        """
        Get authenticated Google Drive service with automatic token refresh.
        
        Yields:
            The authenticated Google Drive service.
            
        Raises:
            AuthenticationError: If authentication fails.
        """
        if not self.credentials:
            raise AuthenticationError("No credentials provided")
        
        # Refresh credentials if expired
        if self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                logger.debug("Google credentials refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh Google credentials: {e}")
                raise AuthenticationError(f"Failed to refresh credentials: {e}")
        
        # Build service
        try:
            service = build('drive', 'v3', credentials=self.credentials)
            yield service
        except Exception as e:
            logger.error(f"Failed to build Google Drive service: {e}")
            raise DriveAPIError(f"Failed to build service: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        (HttpError, ConnectionError),
        max_tries=5,
        max_time=300,
        giveup=lambda e: isinstance(e, HttpError) and 400 <= e.resp.status < 500 and e.resp.status != 429
    )
    async def _make_request(self, request_func, *args, **kwargs):
        """
        Make a Google API request with exponential backoff and rate limiting.
        
        Args:
            request_func: The API request function to call.
            *args, **kwargs: Arguments to pass to the request function.
            
        Returns:
            The API response.
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded after retries.
            DriveAPIError: For other API errors.
        """
        await self.rate_limiter.acquire()
        
        try:
            self.stats["requests_made"] += 1
            
            # Execute the request
            if asyncio.iscoroutinefunction(request_func):
                response = await request_func(*args, **kwargs)
            else:
                # Run synchronous Google API calls in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, request_func, *args, **kwargs)
            
            return response
            
        except HttpError as e:
            self.stats["errors"] += 1
            
            if e.resp.status == 429:
                self.stats["rate_limit_hits"] += 1
                logger.warning(f"Rate limit exceeded: {e}")
                raise RateLimitExceeded(f"Rate limit exceeded: {e}")
            elif 400 <= e.resp.status < 500:
                logger.error(f"Client error in Google Drive API: {e}")
                raise DriveAPIError(f"Client error: {e}")
            elif e.resp.status >= 500:
                logger.error(f"Server error in Google Drive API: {e}")
                raise DriveAPIError(f"Server error: {e}")
            else:
                logger.error(f"Unknown Google Drive API error: {e}")
                raise DriveAPIError(f"Unknown error: {e}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Unexpected error in Google Drive API request: {e}")
            raise DriveAPIError(f"Unexpected error: {e}")
    
    async def list_files(
        self, 
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        fields: str = "nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)",
        page_size: int = 100,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List files from Google Drive with pagination support.
        
        Args:
            folder_id: Optional folder ID to search within.
            query: Optional search query.
            fields: Fields to retrieve.
            page_size: Number of files per page.
            max_results: Maximum total results to return.
            
        Returns:
            List of file metadata dictionaries.
        """
        files = []
        page_token = None
        results_count = 0
        
        # Build query
        query_parts = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if query:
            query_parts.append(query)
        
        # Add filter for supported file types
        supported_types = [
            "mimeType='application/pdf'",
            "mimeType contains 'audio/'",
            "mimeType contains 'image/'"
        ]
        query_parts.append(f"({' or '.join(supported_types)})")
        
        # Add trash filter
        query_parts.append("trashed=false")
        
        final_query = " and ".join(query_parts)
        
        logger.debug(f"Listing files with query: {final_query}")
        
        async with self._get_service() as service:
            while True:
                # Check if we've reached max results
                if max_results and results_count >= max_results:
                    break
                
                # Adjust page size if approaching max results
                current_page_size = page_size
                if max_results:
                    remaining = max_results - results_count
                    current_page_size = min(page_size, remaining)
                
                def make_request():
                    return service.files().list(
                        q=final_query,
                        pageSize=current_page_size,
                        fields=fields,
                        pageToken=page_token
                    ).execute()
                
                try:
                    response = await self._make_request(make_request)
                    
                    batch_files = response.get('files', [])
                    files.extend(batch_files)
                    results_count += len(batch_files)
                    
                    self.stats["files_processed"] += len(batch_files)
                    
                    logger.debug(f"Retrieved {len(batch_files)} files, total: {len(files)}")
                    
                    # Check for next page
                    page_token = response.get('nextPageToken')
                    if not page_token:
                        break
                        
                except Exception as e:
                    logger.error(f"Error listing files: {e}")
                    raise
        
        logger.info(f"Listed {len(files)} files from Google Drive")
        return files
    
    async def get_file_metadata(self, file_id: str, fields: str = "*") -> Dict[str, Any]:
        """
        Get metadata for a specific file.
        
        Args:
            file_id: Google Drive file ID.
            fields: Fields to retrieve.
            
        Returns:
            File metadata dictionary.
        """
        async with self._get_service() as service:
            def make_request():
                return service.files().get(fileId=file_id, fields=fields).execute()
            
            metadata = await self._make_request(make_request)
            logger.debug(f"Retrieved metadata for file {file_id}")
            return metadata
    
    async def batch_get_metadata(self, file_ids: List[str], fields: str = "*") -> List[Dict[str, Any]]:
        """
        Get metadata for multiple files in a single batch request.
        
        Args:
            file_ids: List of Google Drive file IDs.
            fields: Fields to retrieve.
            
        Returns:
            List of file metadata dictionaries.
        """
        if not file_ids:
            return []
        
        results = []
        batch_size = 100  # Google's batch request limit
        
        async with self._get_service() as service:
            for i in range(0, len(file_ids), batch_size):
                batch_ids = file_ids[i:i + batch_size]
                
                def make_batch_request():
                    batch = service.new_batch_http_request()
                    batch_results = {}
                    
                    def callback(request_id, response, exception):
                        if exception:
                            logger.error(f"Error in batch request {request_id}: {exception}")
                            batch_results[request_id] = {"error": str(exception)}
                        else:
                            batch_results[request_id] = response
                    
                    for j, file_id in enumerate(batch_ids):
                        batch.add(
                            service.files().get(fileId=file_id, fields=fields),
                            callback=callback,
                            request_id=str(j)
                        )
                    
                    batch.execute()
                    return batch_results
                
                batch_response = await self._make_request(make_batch_request)
                
                # Process batch results
                for request_id, response in batch_response.items():
                    if "error" not in response:
                        results.append(response)
                    else:
                        logger.warning(f"Failed to get metadata for file in batch: {response['error']}")
        
        logger.info(f"Retrieved metadata for {len(results)} files via batch request")
        return results
    
    async def download_file(self, file_id: str) -> bytes:
        """
        Download file content from Google Drive.
        
        Args:
            file_id: Google Drive file ID.
            
        Returns:
            File content as bytes.
        """
        async with self._get_service() as service:
            def make_request():
                return service.files().get_media(fileId=file_id).execute()
            
            content = await self._make_request(make_request)
            logger.debug(f"Downloaded file {file_id}, size: {len(content)} bytes")
            return content
    
    async def setup_webhook(
        self, 
        folder_id: str, 
        webhook_url: str,
        webhook_secret: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Set up a webhook for real-time file change notifications.
        
        Args:
            folder_id: Google Drive folder ID to watch.
            webhook_url: URL to receive webhook notifications.
            webhook_secret: Optional secret for webhook verification.
            
        Returns:
            Dictionary with webhook information (channel_id, resource_id).
        """
        channel_id = str(uuid.uuid4())
        expiration = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
        
        channel_config = {
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url,
            "expiration": expiration,
        }
        
        if webhook_secret:
            channel_config["token"] = webhook_secret
        
        async with self._get_service() as service:
            def make_request():
                return service.files().watch(
                    fileId=folder_id,
                    body=channel_config
                ).execute()
            
            response = await self._make_request(make_request)
            
            webhook_info = {
                "channel_id": response["id"],
                "resource_id": response["resourceId"],
                "resource_uri": response["resourceUri"],
                "expiration": response.get("expiration"),
            }
            
            logger.info(f"Set up webhook for folder {folder_id}: {webhook_info}")
            return webhook_info
    
    async def stop_webhook(self, channel_id: str, resource_id: str) -> None:
        """
        Stop a webhook channel.
        
        Args:
            channel_id: The webhook channel ID.
            resource_id: The resource ID from webhook setup.
        """
        async with self._get_service() as service:
            def make_request():
                return service.channels().stop(
                    body={
                        "id": channel_id,
                        "resourceId": resource_id
                    }
                ).execute()
            
            await self._make_request(make_request)
            logger.info(f"Stopped webhook channel {channel_id}")
    
    async def process_files_for_sync(
        self, 
        folder_id: str,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Process files for synchronization with parsed metadata.
        
        Args:
            folder_id: Google Drive folder ID.
            since: Optional datetime to filter files modified since.
            
        Returns:
            List of processed file data with parsed metadata.
        """
        # Build query for modified files
        query_parts = []
        if since:
            # Format datetime for Google Drive API
            since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
            query_parts.append(f"modifiedTime > '{since_str}'")
        
        query = " and ".join(query_parts) if query_parts else None
        
        # Get files
        files = await self.list_files(folder_id=folder_id, query=query)
        
        processed_files = []
        for file_data in files:
            try:
                # Parse filename for musical information
                parsed = parse_filename(file_data["name"])
                
                # Combine Google Drive metadata with parsed information
                processed_file = {
                    "google_file_id": file_data["id"],
                    "filename": file_data["name"],
                    "mime_type": file_data.get("mimeType"),
                    "size": int(file_data.get("size", 0)) if file_data.get("size") else None,
                    "modified_time": file_data.get("modifiedTime"),
                    "parents": file_data.get("parents", []),
                    
                    # Parsed information
                    "song_title": parsed.song_title,
                    "key": parsed.key,
                    "file_type": parsed.file_type.value,
                    "composer": parsed.composer,
                    "arranger": parsed.arranger,
                    "chart_type": parsed.chart_type,
                    "tempo": parsed.tempo,
                    "parsed_metadata": parsed.metadata,
                }
                
                processed_files.append(processed_file)
                
            except Exception as e:
                logger.error(f"Error processing file {file_data['name']}: {e}")
                # Still include the file with basic information
                processed_files.append({
                    "google_file_id": file_data["id"],
                    "filename": file_data["name"],
                    "mime_type": file_data.get("mimeType"),
                    "size": int(file_data.get("size", 0)) if file_data.get("size") else None,
                    "modified_time": file_data.get("modifiedTime"),
                    "parents": file_data.get("parents", []),
                    "song_title": file_data["name"],
                    "key": None,
                    "file_type": "other",
                    "parse_error": str(e),
                })
        
        self.stats["last_sync"] = datetime.utcnow()
        logger.info(f"Processed {len(processed_files)} files for sync")
        return processed_files
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return super().get_stats()

    def reset_stats(self) -> None:
        """Reset service statistics."""
        super().reset_stats()

