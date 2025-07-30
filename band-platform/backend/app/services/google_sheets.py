"""
Google Sheets API service for setlist and gig data parsing with timezone handling.

This module provides comprehensive Google Sheets integration following the PRP requirements
for real-time setlist management and gig scheduling with proper timezone support.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import asynccontextmanager

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import backoff
import pytz

from ..config import settings

logger = logging.getLogger(__name__)


class SheetsAPIError(Exception):
    """Custom exception for Google Sheets API errors."""
    pass


class GoogleSheetsService:
    """
    Google Sheets API service for setlist and gig data management.
    
    This service handles reading and writing setlist data from Google Sheets
    with proper timezone handling and real-time sync capabilities.
    """
    
    def __init__(self, credentials: Optional[Credentials] = None):
        """
        Initialize the Google Sheets service.
        
        Args:
            credentials: Optional Google OAuth credentials.
        """
        self.credentials = credentials
        self.service = None
        
        # Statistics
        self.stats = {
            "requests_made": 0,
            "errors": 0,
            "setlists_processed": 0,
            "gigs_processed": 0,
            "last_sync": None,
        }
    
    @asynccontextmanager
    async def _get_service(self):
        """
        Get authenticated Google Sheets service with automatic token refresh.
        
        Yields:
            The authenticated Google Sheets service.
            
        Raises:
            SheetsAPIError: If authentication fails.
        """
        if not self.credentials:
            raise SheetsAPIError("No credentials provided")
        
        # Refresh credentials if expired
        if self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                logger.debug("Google credentials refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh Google credentials: {e}")
                raise SheetsAPIError(f"Failed to refresh credentials: {e}")
        
        # Build service
        try:
            service = build('sheets', 'v4', credentials=self.credentials)
            yield service
        except Exception as e:
            logger.error(f"Failed to build Google Sheets service: {e}")
            raise SheetsAPIError(f"Failed to build service: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        (HttpError, ConnectionError),
        max_tries=5,
        max_time=300,
        giveup=lambda e: isinstance(e, HttpError) and 400 <= e.resp.status < 500 and e.resp.status != 429
    )
    async def _make_request(self, request_func, *args, **kwargs):
        """
        Make a Google Sheets API request with exponential backoff.
        
        Args:
            request_func: The API request function to call.
            *args, **kwargs: Arguments to pass to the request function.
            
        Returns:
            The API response.
        """
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
            logger.error(f"Google Sheets API error: {e}")
            raise SheetsAPIError(f"Sheets API error: {e}")
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Unexpected error in Google Sheets API request: {e}")
            raise SheetsAPIError(f"Unexpected error: {e}")
    
    async def read_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        value_render_option: str = "UNFORMATTED_VALUE",
        date_time_render_option: str = "FORMATTED_STRING"
    ) -> List[List[Any]]:
        """
        Read data from a specific range in a Google Sheet.
        
        Args:
            spreadsheet_id: The Google Sheets ID.
            range_name: The range to read (e.g., "Sheet1!A1:F10").
            value_render_option: How values should be rendered.
            date_time_render_option: How dates should be rendered.
            
        Returns:
            List of rows, where each row is a list of cell values.
        """
        async with self._get_service() as service:
            def make_request():
                return service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueRenderOption=value_render_option,
                    dateTimeRenderOption=date_time_render_option
                ).execute()
            
            response = await self._make_request(make_request)
            values = response.get('values', [])
            
            logger.debug(f"Read {len(values)} rows from {range_name}")
            return values
    
    async def batch_read_ranges(
        self,
        spreadsheet_id: str,
        ranges: List[str],
        value_render_option: str = "UNFORMATTED_VALUE"
    ) -> Dict[str, List[List[Any]]]:
        """
        Read multiple ranges from a Google Sheet in a single request.
        
        Args:
            spreadsheet_id: The Google Sheets ID.
            ranges: List of range names to read.
            value_render_option: How values should be rendered.
            
        Returns:
            Dictionary mapping range names to their values.
        """
        async with self._get_service() as service:
            def make_request():
                return service.spreadsheets().values().batchGet(
                    spreadsheetId=spreadsheet_id,
                    ranges=ranges,
                    valueRenderOption=value_render_option
                ).execute()
            
            response = await self._make_request(make_request)
            value_ranges = response.get('valueRanges', [])
            
            result = {}
            for i, range_name in enumerate(ranges):
                if i < len(value_ranges):
                    result[range_name] = value_ranges[i].get('values', [])
                else:
                    result[range_name] = []
            
            logger.debug(f"Batch read {len(ranges)} ranges")
            return result
    
    async def write_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """
        Write data to a specific range in a Google Sheet.
        
        Args:
            spreadsheet_id: The Google Sheets ID.
            range_name: The range to write to.
            values: List of rows to write.
            value_input_option: How input data should be interpreted.
            
        Returns:
            Response from the API.
        """
        async with self._get_service() as service:
            def make_request():
                body = {
                    'values': values,
                    'majorDimension': 'ROWS'
                }
                return service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body
                ).execute()
            
            response = await self._make_request(make_request)
            logger.debug(f"Wrote {len(values)} rows to {range_name}")
            return response
    
    async def parse_setlist_data(
        self,
        spreadsheet_id: str,
        range_name: str = "Setlist!A:F",
        band_timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Parse setlist data from a Google Sheet with proper structure.
        
        Expected columns: Order | Song Title | Key | Duration | Notes | Status
        
        Args:
            spreadsheet_id: The Google Sheets ID.
            range_name: The range containing setlist data.
            band_timezone: Timezone for the band.
            
        Returns:
            Parsed setlist data with items and metadata.
        """
        try:
            values = await self.read_range(spreadsheet_id, range_name)
            
            if not values:
                return {
                    "items": [],
                    "metadata": {"total_items": 0, "estimated_duration": 0}
                }
            
            # Expected header: Order | Song Title | Key | Duration | Notes | Status
            headers = values[0] if values else []
            if len(headers) < 2:
                raise SheetsAPIError("Invalid setlist format: insufficient columns")
            
            items = []
            total_duration = 0
            
            for row_idx, row in enumerate(values[1:], 1):  # Skip header
                if not row or len(row) < 2:  # Need at least order and title
                    continue
                
                try:
                    # Parse row data with defaults
                    order = self._parse_int(row[0]) if row[0] else row_idx
                    title = str(row[1]).strip() if len(row) > 1 else f"Song {row_idx}"
                    key = str(row[2]).strip() if len(row) > 2 and row[2] else None
                    duration_str = str(row[3]).strip() if len(row) > 3 and row[3] else None
                    notes = str(row[4]).strip() if len(row) > 4 and row[4] else None
                    status = str(row[5]).strip().lower() if len(row) > 5 and row[5] else "active"
                    
                    # Parse duration
                    duration_minutes = self._parse_duration(duration_str)
                    if duration_minutes:
                        total_duration += duration_minutes
                    
                    # Validate key if provided
                    if key and not self._is_valid_key(key):
                        logger.warning(f"Invalid key '{key}' in row {row_idx + 1}")
                        key = None
                    
                    item = {
                        "order_index": order,
                        "title": title,
                        "key": key,
                        "estimated_duration_minutes": duration_minutes,
                        "notes": notes,
                        "status": status,
                        "source_row": row_idx + 1,
                        "last_updated": datetime.now(timezone.utc)
                    }
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Error parsing setlist row {row_idx + 1}: {e}")
                    continue
            
            # Sort by order
            items.sort(key=lambda x: x["order_index"])
            
            metadata = {
                "total_items": len(items),
                "estimated_duration": total_duration,
                "source_range": range_name,
                "parsed_at": datetime.now(timezone.utc),
                "band_timezone": band_timezone
            }
            
            self.stats["setlists_processed"] += 1
            logger.info(f"Parsed setlist with {len(items)} items, duration: {total_duration} minutes")
            
            return {
                "items": items,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing setlist data: {e}")
            raise SheetsAPIError(f"Failed to parse setlist: {e}")
    
    async def parse_gig_data(
        self,
        spreadsheet_id: str,
        range_name: str = "Gigs!A:H",
        band_timezone: str = "UTC"
    ) -> List[Dict[str, Any]]:
        """
        Parse gig/event data from a Google Sheet with timezone handling.
        
        Expected columns: Date | Venue | Load-in | Downbeat | Dress Code | Personnel | Notes | Status
        
        Args:
            spreadsheet_id: The Google Sheets ID.
            range_name: The range containing gig data.
            band_timezone: Timezone for the band.
            
        Returns:
            List of parsed gig data.
        """
        try:
            values = await self.read_range(spreadsheet_id, range_name)
            
            if not values:
                return []
            
            # Skip header row
            gigs = []
            tz = pytz.timezone(band_timezone)
            
            for row_idx, row in enumerate(values[1:], 1):  # Skip header
                if not row or len(row) < 2:  # Need at least date and venue
                    continue
                
                try:
                    # Parse row data
                    date_str = str(row[0]).strip() if row[0] else None
                    venue = str(row[1]).strip() if len(row) > 1 else None
                    load_in = str(row[2]).strip() if len(row) > 2 and row[2] else None
                    downbeat = str(row[3]).strip() if len(row) > 3 and row[3] else None
                    dress_code = str(row[4]).strip() if len(row) > 4 and row[4] else None
                    personnel = str(row[5]).strip() if len(row) > 5 and row[5] else None
                    notes = str(row[6]).strip() if len(row) > 6 and row[6] else None
                    status = str(row[7]).strip().lower() if len(row) > 7 and row[7] else "confirmed"
                    
                    if not date_str or not venue:
                        continue
                    
                    # Parse date with timezone
                    gig_date = self._parse_date_with_timezone(date_str, tz)
                    if not gig_date:
                        logger.warning(f"Invalid date '{date_str}' in gig row {row_idx + 1}")
                        continue
                    
                    # Parse times
                    load_in_time = self._parse_time_with_timezone(load_in, gig_date, tz) if load_in else None
                    downbeat_time = self._parse_time_with_timezone(downbeat, gig_date, tz) if downbeat else None
                    
                    gig = {
                        "performance_date": gig_date.date(),
                        "venue": venue,
                        "load_in_time": load_in_time,
                        "downbeat_time": downbeat_time,
                        "dress_code": dress_code,
                        "personnel": personnel,
                        "notes": notes,
                        "status": status,
                        "source_row": row_idx + 1,
                        "timezone": band_timezone,
                        "last_updated": datetime.now(timezone.utc)
                    }
                    
                    gigs.append(gig)
                    
                except Exception as e:
                    logger.warning(f"Error parsing gig row {row_idx + 1}: {e}")
                    continue
            
            self.stats["gigs_processed"] += len(gigs)
            logger.info(f"Parsed {len(gigs)} gigs from sheet")
            
            return gigs
            
        except Exception as e:
            logger.error(f"Error parsing gig data: {e}")
            raise SheetsAPIError(f"Failed to parse gigs: {e}")
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer value safely."""
        try:
            return int(float(str(value))) if value else None
        except (ValueError, TypeError):
            return None
    
    def _parse_duration(self, duration_str: Optional[str]) -> Optional[float]:
        """
        Parse duration string into minutes.
        
        Supports formats like: "3:30", "3.5", "3 min", "3m30s"
        """
        if not duration_str:
            return None
        
        duration_str = duration_str.strip().lower()
        
        try:
            # Handle MM:SS format
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes + (seconds / 60)
            
            # Handle "3m30s" format
            if 'm' in duration_str and 's' in duration_str:
                import re
                match = re.match(r'(\d+)m(\d+)s', duration_str)
                if match:
                    minutes = float(match.group(1))
                    seconds = float(match.group(2))
                    return minutes + (seconds / 60)
            
            # Handle "3 min" or "3m" format
            if 'min' in duration_str or 'm' in duration_str:
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', duration_str)
                if match:
                    return float(match.group(1))
            
            # Handle plain number (assume minutes)
            return float(duration_str)
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse duration: {duration_str}")
            return None
    
    def _is_valid_key(self, key: str) -> bool:
        """Check if a musical key is valid."""
        from ..services.content_parser import VALID_KEYS
        return key in VALID_KEYS
    
    def _parse_date_with_timezone(self, date_str: str, tz: pytz.BaseTzInfo) -> Optional[datetime]:
        """Parse date string with timezone."""
        try:
            # Try common date formats
            date_formats = [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%m/%d/%y",
                "%d/%m/%Y",
                "%B %d, %Y",
                "%b %d, %Y"
            ]
            
            for fmt in date_formats:
                try:
                    naive_date = datetime.strptime(date_str, fmt)
                    return tz.localize(naive_date)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None
    
    def _parse_time_with_timezone(
        self, 
        time_str: str, 
        base_date: datetime, 
        tz: pytz.BaseTzInfo
    ) -> Optional[datetime]:
        """Parse time string and combine with date and timezone."""
        try:
            # Try common time formats
            time_formats = [
                "%H:%M",
                "%I:%M %p",
                "%I:%M%p",
                "%H:%M:%S"
            ]
            
            for fmt in time_formats:
                try:
                    time_obj = datetime.strptime(time_str, fmt).time()
                    combined = datetime.combine(base_date.date(), time_obj)
                    return tz.localize(combined)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse time: {time_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing time '{time_str}': {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset service statistics."""
        self.stats = {
            "requests_made": 0,
            "errors": 0,
            "setlists_processed": 0,
            "gigs_processed": 0,
            "last_sync": None,
        }


# Convenience functions for service creation

def create_sheets_service(credentials: Credentials) -> GoogleSheetsService:
    """
    Create a Google Sheets service instance.
    
    Args:
        credentials: Google OAuth credentials.
        
    Returns:
        Configured GoogleSheetsService instance.
    """
    return GoogleSheetsService(credentials)


async def test_sheets_connection(service: GoogleSheetsService, spreadsheet_id: str) -> bool:
    """
    Test Google Sheets API connection.
    
    Args:
        service: GoogleSheetsService instance.
        spreadsheet_id: Test spreadsheet ID.
        
    Returns:
        True if connection is successful.
    """
    try:
        # Try to read a simple range
        await service.read_range(spreadsheet_id, "A1:A1")
        return True
    except Exception as e:
        logger.error(f"Sheets connection test failed: {e}")
        return False