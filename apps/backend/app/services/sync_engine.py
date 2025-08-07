"""
Sync engine for real-time webhook processing and delta synchronization.

This module orchestrates synchronization between Google Workspace (Drive, Sheets, Calendar)
and the local database, providing real-time updates via webhooks and WebSocket connections.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass
from enum import Enum

from google.oauth2.credentials import Credentials
from sqlalchemy.ext.asyncio import AsyncSession
import backoff

from ..database.connection import get_db_session
from ..models.sync import SyncOperation, SyncStatus, GoogleService
from ..models.user import Band
from .google_drive import GoogleDriveService
from .google_sheets import GoogleSheetsService
from .content_parser import parse_filename
from .websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class SyncEventType(str, Enum):
    """Types of sync events that can occur."""
    FILE_CREATED = "file_created"
    FILE_UPDATED = "file_updated"
    FILE_DELETED = "file_deleted"
    SHEET_UPDATED = "sheet_updated"
    FULL_SYNC = "full_sync"
    DELTA_SYNC = "delta_sync"


@dataclass
class SyncEvent:
    """Represents a sync event to be processed."""
    event_type: SyncEventType
    resource_id: str
    resource_type: str  # 'drive_file', 'sheet', etc.
    band_id: Optional[int] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


class SyncEngineError(Exception):
    """Custom exception for sync engine errors."""
    pass


class SyncEngine:
    """
    Core synchronization engine for the Band Platform.
    
    Handles real-time synchronization between Google Workspace and local database,
    processes webhooks, manages delta sync operations, and broadcasts updates.
    """
    
    def __init__(
        self,
        websocket_manager: Optional[WebSocketManager] = None,
        max_concurrent_syncs: int = 5,
        batch_size: int = 50
    ):
        """
        Initialize the sync engine.
        
        Args:
            websocket_manager: WebSocket manager for real-time updates.
            max_concurrent_syncs: Maximum concurrent sync operations.
            batch_size: Batch size for processing operations.
        """
        self.websocket_manager = websocket_manager
        self.max_concurrent_syncs = max_concurrent_syncs
        self.batch_size = batch_size
        
        # Internal state
        self._running = False
        self._sync_queue: asyncio.Queue = asyncio.Queue()
        self._active_syncs: Set[str] = set()
        self._sync_semaphore = asyncio.Semaphore(max_concurrent_syncs)
        self._last_sync_times: Dict[int, datetime] = {}  # band_id -> last_sync
        
        # Event handlers
        self._event_handlers: Dict[SyncEventType, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "files_synced": 0,
            "sheets_synced": 0,
            "last_sync": None,
            "sync_errors": 0,
            "active_webhooks": 0,
        }
    
    async def start(self) -> None:
        """Start the sync engine background tasks."""
        if self._running:
            logger.warning("Sync engine is already running")
            return
        
        self._running = True
        logger.info("Starting sync engine...")
        
        # Start background task for processing sync queue
        asyncio.create_task(self._process_sync_queue())
        
        # Start periodic tasks
        asyncio.create_task(self._periodic_health_check())
        asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Sync engine started successfully")
    
    async def stop(self) -> None:
        """Stop the sync engine and cleanup resources."""
        if not self._running:
            return
        
        logger.info("Stopping sync engine...")
        self._running = False
        
        # Wait for active syncs to complete (with timeout)
        wait_time = 0
        while self._active_syncs and wait_time < 30:
            logger.info(f"Waiting for {len(self._active_syncs)} active syncs to complete...")
            await asyncio.sleep(1)
            wait_time += 1
        
        if self._active_syncs:
            logger.warning(f"Forcibly stopping with {len(self._active_syncs)} active syncs")
        
        logger.info("Sync engine stopped")
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """
        Handle incoming webhook from Google APIs.
        
        Args:
            webhook_data: Raw webhook payload from Google.
        """
        try:
            # Parse webhook data
            event = self._parse_webhook_data(webhook_data)
            if not event:
                logger.warning(f"Could not parse webhook data: {webhook_data}")
                return
            
            # Add to sync queue
            await self._sync_queue.put(event)
            
            logger.debug(f"Webhook event queued: {event.event_type} for {event.resource_id}")
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            self.stats["events_failed"] += 1
    
    async def trigger_full_sync(self, band_id: int, credentials: Credentials) -> str:
        """
        Trigger a full synchronization for a band.
        
        Args:
            band_id: The band ID to sync.
            credentials: Google OAuth credentials.
            
        Returns:
            Operation ID for tracking.
        """
        operation_id = f"full_sync_{band_id}_{int(datetime.now().timestamp())}"
        
        event = SyncEvent(
            event_type=SyncEventType.FULL_SYNC,
            resource_id=operation_id,
            resource_type="full_sync",
            band_id=band_id,
            metadata={"credentials": credentials}
        )
        
        await self._sync_queue.put(event)
        
        logger.info(f"Full sync triggered for band {band_id}: {operation_id}")
        return operation_id
    
    async def trigger_delta_sync(self, band_id: int, credentials: Credentials) -> str:
        """
        Trigger a delta synchronization for a band.
        
        Args:
            band_id: The band ID to sync.
            credentials: Google OAuth credentials.
            
        Returns:
            Operation ID for tracking.
        """
        operation_id = f"delta_sync_{band_id}_{int(datetime.now().timestamp())}"
        
        event = SyncEvent(
            event_type=SyncEventType.DELTA_SYNC,
            resource_id=operation_id,
            resource_type="delta_sync",
            band_id=band_id,
            metadata={"credentials": credentials}
        )
        
        await self._sync_queue.put(event)
        
        logger.info(f"Delta sync triggered for band {band_id}: {operation_id}")
        return operation_id
    
    def register_event_handler(
        self, 
        event_type: SyncEventType, 
        handler: Callable[[SyncEvent], Any]
    ) -> None:
        """Register an event handler for specific sync events."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _process_sync_queue(self) -> None:
        """Background task to process the sync queue."""
        while self._running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(
                        self._sync_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process event with semaphore for concurrency control
                async with self._sync_semaphore:
                    asyncio.create_task(self._process_sync_event(event))
                
            except Exception as e:
                logger.error(f"Error in sync queue processing: {e}")
                await asyncio.sleep(1)
    
    async def _process_sync_event(self, event: SyncEvent) -> None:
        """
        Process a single sync event.
        
        Args:
            event: The sync event to process.
        """
        operation_id = f"{event.event_type}_{event.resource_id}"
        
        if operation_id in self._active_syncs:
            logger.debug(f"Sync already in progress: {operation_id}")
            return
        
        self._active_syncs.add(operation_id)
        
        try:
            logger.debug(f"Processing sync event: {event.event_type} for {event.resource_id}")
            
            # Record sync operation in database
            async with get_db_session() as session:
                google_service = event.metadata.get("google_service")
                if not google_service:
                    if event.resource_type == "sheet":
                        google_service = GoogleService.SHEETS.value
                    else:
                        google_service = GoogleService.DRIVE.value

                sync_op = SyncOperation(
                    operation_id=operation_id,
                    band_id=event.band_id,
                    sync_type=event.event_type.value,
                    google_service=google_service,
                    status=SyncStatus.IN_PROGRESS,
                    started_at=datetime.now(timezone.utc)
                )
                session.add(sync_op)
                await session.commit()
                
                try:
                    # Process based on event type
                    if event.event_type == SyncEventType.FULL_SYNC:
                        await self._handle_full_sync(event, session)
                    elif event.event_type == SyncEventType.DELTA_SYNC:
                        await self._handle_delta_sync(event, session)
                    elif event.event_type in [
                        SyncEventType.FILE_CREATED, 
                        SyncEventType.FILE_UPDATED, 
                        SyncEventType.FILE_DELETED
                    ]:
                        await self._handle_file_change(event, session)
                    elif event.event_type == SyncEventType.SHEET_UPDATED:
                        await self._handle_sheet_change(event, session)
                    
                    # Mark operation as completed
                    sync_op.status = SyncStatus.COMPLETED
                    sync_op.completed_at = datetime.now(timezone.utc)
                    
                    # Call event handlers
                    await self._call_event_handlers(event)
                    
                    self.stats["events_processed"] += 1
                    
                except Exception as e:
                    # Mark operation as failed
                    sync_op.status = SyncStatus.FAILED
                    sync_op.completed_at = datetime.now(timezone.utc)
                    sync_op.error_message = str(e)
                    self.stats["events_failed"] += 1
                    raise
                
                finally:
                    await session.commit()
        
        except Exception as e:
            logger.error(f"Error processing sync event {operation_id}: {e}")
            self.stats["sync_errors"] += 1
        
        finally:
            self._active_syncs.discard(operation_id)
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=300
    )
    async def _handle_full_sync(self, event: SyncEvent, session: AsyncSession) -> None:
        """Handle full synchronization for a band."""
        credentials = event.metadata.get("credentials")
        if not credentials:
            raise SyncEngineError("No credentials provided for full sync")
        
        band_id = event.band_id
        logger.info(f"Starting full sync for band {band_id}")
        
        # Initialize Google services
        drive_service = GoogleDriveService(credentials)
        sheets_service = GoogleSheetsService(credentials)
        
        # Get band configuration
        band = await session.get(Band, band_id)
        if not band:
            raise SyncEngineError(f"Band {band_id} not found")
        
        # Sync Drive files
        if band.google_drive_folder_id:
            await self._sync_drive_folder(
                drive_service, 
                band.google_drive_folder_id, 
                band_id, 
                session
            )
        
        # Sync Sheets data
        if band.google_sheets_id:
            await self._sync_sheets_data(
                sheets_service,
                band.google_sheets_id,
                band_id,
                session
            )
        
        # Update last sync time
        self._last_sync_times[band_id] = datetime.now(timezone.utc)
        self.stats["last_sync"] = datetime.now(timezone.utc)
        
        # Broadcast update via WebSocket
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_band(
                band_id,
                {
                    "type": "sync_completed",
                    "operation": "full_sync",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        logger.info(f"Full sync completed for band {band_id}")
    
    async def _handle_delta_sync(self, event: SyncEvent, session: AsyncSession) -> None:
        """Handle delta synchronization for a band."""
        credentials = event.metadata.get("credentials")
        if not credentials:
            raise SyncEngineError("No credentials provided for delta sync")
        
        band_id = event.band_id
        last_sync = self._last_sync_times.get(band_id)
        
        logger.info(f"Starting delta sync for band {band_id} since {last_sync}")
        
        # For now, treat delta sync as full sync
        # TODO: Implement proper delta sync with change tokens
        await self._handle_full_sync(event, session)
    
    async def _handle_file_change(self, event: SyncEvent, session: AsyncSession) -> None:
        """Handle individual file changes from Drive webhooks."""
        file_id = event.resource_id
        
        logger.info(f"Processing file change: {event.event_type} for {file_id}")
        
        # TODO: Implement file-specific sync logic
        # This would involve:
        # 1. Getting file metadata from Drive
        # 2. Parsing filename for musical information
        # 3. Updating database record
        # 4. Broadcasting update via WebSocket
        
        self.stats["files_synced"] += 1
    
    async def _handle_sheet_change(self, event: SyncEvent, session: AsyncSession) -> None:
        """Handle sheet changes from Sheets webhooks."""
        sheet_id = event.resource_id
        
        logger.info(f"Processing sheet change for {sheet_id}")
        
        # TODO: Implement sheet-specific sync logic
        # This would involve:
        # 1. Re-parsing setlist/gig data from sheet
        # 2. Updating database records
        # 3. Broadcasting update via WebSocket
        
        self.stats["sheets_synced"] += 1
    
    async def _sync_drive_folder(
        self, 
        drive_service: GoogleDriveService, 
        folder_id: str, 
        band_id: int, 
        session: AsyncSession
    ) -> None:
        """Sync all files in a Google Drive folder."""
        logger.info(f"Syncing Drive folder {folder_id} for band {band_id}")
        
        try:
            # Get all files in folder
            files = await drive_service.list_files_in_folder(folder_id)
            
            # Process files in batches
            for i in range(0, len(files), self.batch_size):
                batch = files[i:i + self.batch_size]
                await self._process_file_batch(batch, band_id, session)
            
            logger.info(f"Synced {len(files)} files from Drive folder {folder_id}")
            
        except Exception as e:
            logger.error(f"Error syncing Drive folder {folder_id}: {e}")
            raise
    
    async def _process_file_batch(
        self, 
        files: List[Dict[str, Any]], 
        band_id: int, 
        session: AsyncSession
    ) -> None:
        """Process a batch of files from Google Drive."""
        for file_data in files:
            try:
                filename = file_data.get("name", "")
                
                # Parse filename for musical information
                parsed = parse_filename(filename)
                
                # Check if chart or audio file already exists
                if parsed.file_type.value == "chart":
                    # Create or update chart record
                    # TODO: Implement proper upsert logic
                    pass
                elif parsed.file_type.value == "audio":
                    # Create or update audio record
                    # TODO: Implement proper upsert logic
                    pass
                
            except Exception as e:
                logger.warning(f"Error processing file {file_data}: {e}")
                continue
    
    async def _sync_sheets_data(
        self,
        sheets_service: GoogleSheetsService,
        spreadsheet_id: str,
        band_id: int,
        session: AsyncSession
    ) -> None:
        """Sync data from Google Sheets."""
        logger.info(f"Syncing Sheets data {spreadsheet_id} for band {band_id}")
        
        try:
            # Parse setlist data
            setlist_data = await sheets_service.parse_setlist_data(
                spreadsheet_id,
                band_timezone="UTC"  # TODO: Get from band configuration
            )
            
            # Parse gig data
            gig_data = await sheets_service.parse_gig_data(
                spreadsheet_id,
                band_timezone="UTC"  # TODO: Get from band configuration
            )
            
            # TODO: Update database with parsed data
            # This would involve creating/updating Setlist and Event records
            
            logger.info(
                f"Synced {len(setlist_data.get('items', []))} setlist items "
                f"and {len(gig_data)} gigs from Sheets"
            )
            
        except Exception as e:
            logger.error(f"Error syncing Sheets data {spreadsheet_id}: {e}")
            raise
    
    def _parse_webhook_data(self, webhook_data: Dict[str, Any]) -> Optional[SyncEvent]:
        """Parse webhook data into a SyncEvent."""
        try:
            # Google Drive webhook format
            if "resourceId" in webhook_data:
                resource_id = webhook_data["resourceId"]
                resource_state = webhook_data.get("resourceState", "")
                
                # Map resource state to event type
                event_type_map = {
                    "sync": SyncEventType.FILE_UPDATED,
                    "add": SyncEventType.FILE_CREATED,
                    "remove": SyncEventType.FILE_DELETED,
                    "update": SyncEventType.FILE_UPDATED,
                    "trash": SyncEventType.FILE_DELETED,
                }
                
                event_type = event_type_map.get(resource_state, SyncEventType.FILE_UPDATED)
                
                return SyncEvent(
                    event_type=event_type,
                    resource_id=resource_id,
                    resource_type="drive_file",
                    metadata=webhook_data
                )
            
            # Google Sheets webhook format
            elif "eventType" in webhook_data:
                resource_id = webhook_data.get("spreadsheetId", "")
                
                return SyncEvent(
                    event_type=SyncEventType.SHEET_UPDATED,
                    resource_id=resource_id,
                    resource_type="sheet",
                    metadata=webhook_data
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing webhook data: {e}")
            return None
    
    async def _call_event_handlers(self, event: SyncEvent) -> None:
        """Call registered event handlers for a sync event."""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def _periodic_health_check(self) -> None:
        """Periodic health check for the sync engine."""
        while self._running:
            try:
                # Log current status
                active_count = len(self._active_syncs)
                queue_size = self._sync_queue.qsize()
                
                if active_count > 0 or queue_size > 0:
                    logger.debug(
                        f"Sync engine status: {active_count} active, "
                        f"{queue_size} queued"
                    )
                
                # Sleep for health check interval
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old sync operations."""
        while self._running:
            try:
                # Clean up old sync operations (older than 7 days)
                # TODO: Implement cleanup query
                # cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
                # DELETE FROM sync_operations WHERE created_at < cutoff_date
                pass
                
                # Sleep for cleanup interval
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(3600)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync engine statistics."""
        return {
            **self.stats,
            "active_syncs": len(self._active_syncs),
            "queue_size": self._sync_queue.qsize(),
            "running": self._running,
            "last_sync_times": {
                band_id: ts.isoformat() 
                for band_id, ts in self._last_sync_times.items()
            }
        }
    
    def reset_stats(self) -> None:
        """Reset sync engine statistics."""
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "files_synced": 0,
            "sheets_synced": 0,
            "last_sync": None,
            "sync_errors": 0,
            "active_webhooks": 0,
        }


# Global sync engine instance
sync_engine = SyncEngine()


# Convenience functions for sync engine management

async def start_sync_engine(websocket_manager: Optional[WebSocketManager] = None) -> None:
    """Start the global sync engine."""
    if websocket_manager:
        sync_engine.websocket_manager = websocket_manager
    await sync_engine.start()


async def stop_sync_engine() -> None:
    """Stop the global sync engine."""
    await sync_engine.stop()


async def handle_webhook(webhook_data: Dict[str, Any]) -> None:
    """Handle webhook using the global sync engine."""
    await sync_engine.handle_webhook(webhook_data)


async def trigger_full_sync(band_id: int, credentials: Credentials) -> str:
    """Trigger full sync using the global sync engine."""
    return await sync_engine.trigger_full_sync(band_id, credentials)


async def trigger_delta_sync(band_id: int, credentials: Credentials) -> str:
    """Trigger delta sync using the global sync engine."""
    return await sync_engine.trigger_delta_sync(band_id, credentials)


def get_sync_stats() -> Dict[str, Any]:
    """Get sync engine statistics."""
    return sync_engine.get_stats()