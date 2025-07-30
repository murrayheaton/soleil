"""
Google Drive folder organization service for role-based file access.

This service creates and manages user-specific folder structures that organize
files based on user roles and instrument assignments.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from .google_drive import GoogleDriveService
from .content_parser import parse_filename, is_chart_accessible_by_user
from ..models.user import User
from ..models.folder_structure import UserFolder, FolderSyncLog, SyncStatus

logger = logging.getLogger(__name__)


class FolderOrganizationError(Exception):
    """Exception raised for folder organization errors."""
    pass


class FolderOrganizer(GoogleDriveService):
    """
    Service for organizing Google Drive files into role-based folder structures.
    
    This service extends GoogleDriveService to provide folder creation and
    organization capabilities for individual users based on their instruments.
    """
    
    def __init__(self, credentials=None, db_session: Optional[AsyncSession] = None):
        """
        Initialize the folder organizer.
        
        Args:
            credentials: Google OAuth credentials.
            db_session: Database session for tracking operations.
        """
        super().__init__(credentials)
        self.db_session = db_session
        
        # Organization statistics
        self.org_stats = {
            "folders_created": 0,
            "shortcuts_created": 0,
            "files_organized": 0,
            "users_processed": 0,
            "errors": 0,
        }
    
    async def create_user_folder_structure(
        self, 
        user: User, 
        source_folder_id: str,
        folder_name: Optional[str] = None
    ) -> str:
        """
        Create a complete folder structure for a user based on their instruments.
        
        Args:
            user: User to create folders for.
            source_folder_id: ID of the admin's source folder.
            folder_name: Optional custom folder name (defaults to "{user.name}'s Files").
            
        Returns:
            Google Drive folder ID of the created user root folder.
            
        Raises:
            FolderOrganizationError: If folder creation fails.
        """
        try:
            logger.info(f"Creating folder structure for user {user.id} ({user.name})")
            
            # Create sync log entry
            sync_log = await self._create_sync_log(
                user.id, 
                "create",
                datetime.utcnow()
            )
            
            async with self._get_service() as service:
                # Create root folder for user
                folder_name = folder_name or f"{user.name}'s Files"
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': []  # Root level - will be shared with user
                }
                
                # Create the folder
                def create_folder():
                    return service.files().create(body=folder_metadata).execute()
                
                folder_response = await self._make_request(create_folder)
                folder_id = folder_response['id']
                
                logger.info(f"Created root folder {folder_id} for user {user.name}")
                
                # Share folder with user
                await self._share_folder_with_user(folder_id, user.email)
                
                # Update statistics
                self.org_stats["folders_created"] += 1
                
                # Complete sync log
                await self._complete_sync_log(
                    sync_log,
                    "success",
                    folders_created=1
                )
                
                return folder_id
                
        except Exception as e:
            logger.error(f"Error creating folder structure for user {user.id}: {e}")
            
            # Update sync log with error
            if 'sync_log' in locals():
                await self._complete_sync_log(
                    sync_log,
                    "error", 
                    error_message=str(e)
                )
                
            self.org_stats["errors"] += 1
            raise FolderOrganizationError(f"Failed to create user folder structure: {e}")
    
    async def organize_files_by_song(
        self, 
        user_folder_id: str, 
        files: List[Dict[str, Any]], 
        user_instruments: List[str],
        user_id: int
    ) -> Dict[str, str]:
        """
        Organize files into song folders with shortcuts for role-appropriate files.
        
        Args:
            user_folder_id: Google Drive ID of user's root folder.
            files: List of file metadata from source folder.
            user_instruments: List of instruments the user plays.
            user_id: Database ID of the user.
            
        Returns:
            Dictionary mapping song titles to their folder IDs.
            
        Raises:
            FolderOrganizationError: If organization fails.
        """
        try:
            logger.info(f"Organizing {len(files)} files by song for user {user_id}")
            
            # Create sync log
            sync_log = await self._create_sync_log(
                user_id,
                "organize",
                datetime.utcnow()
            )
            
            # Group files by song title, filtering by accessibility
            songs = defaultdict(list)
            accessible_files = []
            
            for file_data in files:
                try:
                    # Parse filename to extract musical information
                    parsed = parse_filename(file_data['name'])
                    
                    # Check if user can access this file
                    if (parsed.file_type.value == "audio" or  # Audio files for everyone
                        is_chart_accessible_by_user(parsed.key, user_instruments)):
                        
                        songs[parsed.song_title].append({
                            'file_data': file_data,
                            'parsed': parsed
                        })
                        accessible_files.append(file_data)
                        
                except Exception as e:
                    logger.warning(f"Error parsing file {file_data['name']}: {e}")
                    continue
            
            logger.info(f"Found {len(accessible_files)} accessible files in {len(songs)} songs")
            
            # Create song folders and shortcuts
            song_folders = {}
            total_shortcuts = 0
            
            async with self._get_service() as service:
                for song_title, song_files in songs.items():
                    try:
                        # Create song folder
                        folder_id = await self._create_song_folder(
                            service, user_folder_id, song_title
                        )
                        
                        # Create shortcuts for all files in this song
                        shortcuts_created = await self._create_shortcuts_in_folder(
                            service, folder_id, song_files
                        )
                        
                        song_folders[song_title] = folder_id
                        total_shortcuts += shortcuts_created
                        
                        logger.debug(f"Created folder for '{song_title}' with {shortcuts_created} shortcuts")
                        
                    except Exception as e:
                        logger.error(f"Error organizing song '{song_title}': {e}")
                        continue
            
            # Update statistics
            self.org_stats["folders_created"] += len(song_folders)
            self.org_stats["shortcuts_created"] += total_shortcuts
            self.org_stats["files_organized"] += len(accessible_files)
            
            # Complete sync log
            await self._complete_sync_log(
                sync_log,
                "success",
                files_processed=len(accessible_files),
                shortcuts_created=total_shortcuts,
                folders_created=len(song_folders)
            )
            
            logger.info(f"Successfully organized files into {len(song_folders)} song folders")
            return song_folders
            
        except Exception as e:
            logger.error(f"Error organizing files by song: {e}")
            
            if 'sync_log' in locals():
                await self._complete_sync_log(
                    sync_log,
                    "error",
                    error_message=str(e)
                )
                
            self.org_stats["errors"] += 1
            raise FolderOrganizationError(f"Failed to organize files by song: {e}")
    
    async def create_shortcuts_for_user(
        self, 
        user: User, 
        source_files: List[Dict[str, Any]]
    ) -> int:
        """
        Create shortcuts for files accessible by a specific user.
        
        Args:
            user: User to create shortcuts for.
            source_files: List of files from the source folder.
            
        Returns:
            Number of shortcuts created.
            
        Raises:
            FolderOrganizationError: If shortcut creation fails.
        """
        try:
            if not user.user_folder:
                raise FolderOrganizationError(f"User {user.id} has no folder structure")
            
            logger.info(f"Creating shortcuts for user {user.id} from {len(source_files)} files")
            
            # Organize files by song for this user
            await self.organize_files_by_song(
                user.user_folder.google_folder_id,
                source_files,
                user.instruments,
                user.id
            )
            
            # Count total shortcuts (from org_stats updated in organize_files_by_song)
            shortcuts_created = self.org_stats["shortcuts_created"]
            
            logger.info(f"Created {shortcuts_created} shortcuts for user {user.name}")
            return shortcuts_created
            
        except Exception as e:
            logger.error(f"Error creating shortcuts for user {user.id}: {e}")
            self.org_stats["errors"] += 1
            raise FolderOrganizationError(f"Failed to create shortcuts: {e}")
    
    async def _create_song_folder(
        self, 
        service, 
        parent_folder_id: str, 
        song_title: str
    ) -> str:
        """
        Create a folder for a specific song.
        
        Args:
            service: Google Drive service instance.
            parent_folder_id: ID of the parent folder.
            song_title: Title of the song.
            
        Returns:
            Google Drive folder ID of the created song folder.
        """
        folder_metadata = {
            'name': song_title,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        
        def create_folder():
            return service.files().create(body=folder_metadata).execute()
        
        response = await self._make_request(create_folder)
        folder_id = response['id']
        
        logger.debug(f"Created song folder '{song_title}' with ID {folder_id}")
        return folder_id
    
    async def _create_shortcuts_in_folder(
        self, 
        service, 
        folder_id: str, 
        song_files: List[Dict[str, Any]]
    ) -> int:
        """
        Create shortcuts to files within a song folder.
        
        Args:
            service: Google Drive service instance.
            folder_id: ID of the song folder.
            song_files: List of file data and parsed information.
            
        Returns:
            Number of shortcuts created.
        """
        shortcuts_created = 0
        batch_size = 50  # Limit batch size to avoid API limits
        
        # Process files in batches
        for i in range(0, len(song_files), batch_size):
            batch = song_files[i:i + batch_size]
            
            for file_info in batch:
                try:
                    file_data = file_info['file_data']
                    parsed = file_info['parsed']
                    
                    # Create shortcut metadata
                    shortcut_name = self._generate_shortcut_name(file_data['name'], parsed)
                    shortcut_metadata = {
                        'name': shortcut_name,
                        'mimeType': 'application/vnd.google-apps.shortcut',
                        'parents': [folder_id],
                        'shortcutDetails': {
                            'targetId': file_data['id']
                        }
                    }
                    
                    def create_shortcut():
                        return service.files().create(body=shortcut_metadata).execute()
                    
                    await self._make_request(create_shortcut)
                    shortcuts_created += 1
                    
                    logger.debug(f"Created shortcut '{shortcut_name}' -> {file_data['id']}")
                    
                except Exception as e:
                    logger.warning(f"Error creating shortcut for {file_data['name']}: {e}")
                    continue
            
            # Small delay between batches to respect rate limits
            if i + batch_size < len(song_files):
                await asyncio.sleep(0.1)
        
        logger.debug(f"Created {shortcuts_created} shortcuts in folder {folder_id}")
        return shortcuts_created
    
    async def _share_folder_with_user(self, folder_id: str, user_email: str) -> None:
        """
        Share a folder with a specific user.
        
        Args:
            folder_id: Google Drive folder ID.
            user_email: Email address of the user to share with.
        """
        async with self._get_service() as service:
            permission_metadata = {
                'type': 'user',
                'role': 'reader',  # Users get read access to their organized folders
                'emailAddress': user_email
            }
            
            def create_permission():
                return service.permissions().create(
                    fileId=folder_id,
                    body=permission_metadata,
                    sendNotificationEmail=False  # Don't spam users with notifications
                ).execute()
            
            await self._make_request(create_permission)
            logger.debug(f"Shared folder {folder_id} with {user_email}")
    
    def _generate_shortcut_name(self, original_name: str, parsed_info) -> str:
        """
        Generate a clean name for a shortcut.
        
        Args:
            original_name: Original filename.
            parsed_info: Parsed file information.
            
        Returns:
            Clean shortcut name.
        """
        # For audio files, use the original name
        if parsed_info.file_type.value == "audio":
            return original_name
        
        # For charts, create a descriptive name
        if parsed_info.key:
            return f"{parsed_info.key} Chart.{parsed_info.extension.lstrip('.')}"
        else:
            return original_name
    
    async def _create_sync_log(
        self, 
        user_id: int, 
        operation: str, 
        started_at: datetime
    ) -> Optional[FolderSyncLog]:
        """
        Create a sync log entry.
        
        Args:
            user_id: Database ID of the user.
            operation: Type of operation being performed.
            started_at: When the operation started.
            
        Returns:
            FolderSyncLog instance if database session available.
        """
        if not self.db_session:
            return None
        
        sync_log = FolderSyncLog(
            user_id=user_id,
            operation=operation,
            status="in_progress",
            started_at=started_at
        )
        
        self.db_session.add(sync_log)
        await self.db_session.commit()
        await self.db_session.refresh(sync_log)
        
        return sync_log
    
    async def _complete_sync_log(
        self,
        sync_log: Optional[FolderSyncLog],
        status: str,
        files_processed: int = 0,
        shortcuts_created: int = 0,
        shortcuts_deleted: int = 0,
        folders_created: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """
        Complete a sync log entry with results.
        
        Args:
            sync_log: The sync log to update.
            status: Final status ('success' or 'error').
            files_processed: Number of files processed.
            shortcuts_created: Number of shortcuts created.
            shortcuts_deleted: Number of shortcuts deleted.
            folders_created: Number of folders created.
            error_message: Error message if status is 'error'.
        """
        if not sync_log or not self.db_session:
            return
        
        completed_at = datetime.utcnow()
        duration = (completed_at - sync_log.started_at).total_seconds()
        
        sync_log.status = status
        sync_log.completed_at = completed_at
        sync_log.duration_seconds = int(duration)
        sync_log.files_processed = files_processed
        sync_log.shortcuts_created = shortcuts_created
        sync_log.shortcuts_deleted = shortcuts_deleted
        sync_log.folders_created = folders_created
        sync_log.error_message = error_message
        
        if status == "error":
            sync_log.error_count = 1
        
        await self.db_session.commit()
    
    def get_organization_stats(self) -> Dict[str, Any]:
        """Get organization statistics."""
        return self.org_stats.copy()
    
    def reset_organization_stats(self) -> None:
        """Reset organization statistics."""
        self.org_stats = {
            "folders_created": 0,
            "shortcuts_created": 0,
            "files_organized": 0,
            "users_processed": 0,
            "errors": 0,
        }


# Utility functions for folder organization

async def create_user_folder_if_needed(
    user: User,
    organizer: FolderOrganizer,
    db_session: AsyncSession
) -> str:
    """
    Create a user folder structure if it doesn't exist.
    
    Args:
        user: User to create folders for.
        organizer: FolderOrganizer instance.
        db_session: Database session.
        
    Returns:
        Google Drive folder ID of user's root folder.
    """
    # Check if user already has a folder structure
    if user.user_folder and user.user_folder.google_folder_id:
        logger.info(f"User {user.id} already has folder structure")
        return user.user_folder.google_folder_id
    
    # Get source folder from user's band
    if not user.band or not user.band.google_drive_folder_id:
        raise FolderOrganizationError(f"User {user.id} has no band or band has no Google Drive folder")
    
    source_folder_id = user.band.google_drive_folder_id
    
    # Create folder structure
    folder_id = await organizer.create_user_folder_structure(user, source_folder_id)
    
    # Create or update database record
    if user.user_folder:
        user.user_folder.google_folder_id = folder_id
        user.user_folder.source_folder_id = source_folder_id
        user.user_folder.sync_status = SyncStatus.PENDING
    else:
        user_folder = UserFolder(
            user_id=user.id,
            google_folder_id=folder_id,
            source_folder_id=source_folder_id,
            sync_status=SyncStatus.PENDING
        )
        db_session.add(user_folder)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return folder_id


async def estimate_sync_time(file_count: int, song_count: int) -> int:
    """
    Estimate sync time in seconds based on file and song counts.
    
    Args:
        file_count: Number of files to process.
        song_count: Number of songs to organize.
        
    Returns:
        Estimated time in seconds.
    """
    # Base time for folder creation (2 seconds per song folder)
    folder_time = song_count * 2
    
    # Time for shortcut creation (0.5 seconds per file)
    shortcut_time = file_count * 0.5
    
    # Buffer for API rate limiting and batch processing (20% overhead)
    total_time = int((folder_time + shortcut_time) * 1.2)
    
    # Minimum 5 seconds, maximum 300 seconds (5 minutes)
    return max(5, min(total_time, 300))