"""
File synchronization service for real-time Google Drive sync.

This service handles synchronizing changes from the source folder to all
user folders, detecting file changes, and updating shortcuts accordingly.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .google_drive import GoogleDriveService
from .folder_organizer import FolderOrganizer, create_user_folder_if_needed, estimate_sync_time
from .content_parser import parse_filename, is_chart_accessible_by_user
from ..models.user import User
from ..models.folder_structure import UserFolder, SyncStatus

logger = logging.getLogger(__name__)


class SynchronizationError(Exception):
    """Exception raised for synchronization errors."""
    pass


class FileSynchronizer:
    """
    Service for synchronizing files between source and user folders.
    
    This service monitors changes in the source folder and updates all user
    folders accordingly, ensuring each user sees only the files appropriate
    for their instruments.
    """
    
    def __init__(
        self, 
        drive_service: GoogleDriveService,
        db_session: AsyncSession,
        organizer: Optional[FolderOrganizer] = None
    ):
        """
        Initialize the file synchronizer.
        
        Args:
            drive_service: Google Drive service instance.
            db_session: Database session for tracking sync operations.
            organizer: Optional folder organizer instance.
        """
        self.drive_service = drive_service
        self.db_session = db_session
        self.organizer = organizer or FolderOrganizer(
            credentials=drive_service.credentials,
            db_session=db_session
        )
        
        # Sync statistics
        self.sync_stats = {
            "users_synced": 0,
            "files_processed": 0,
            "shortcuts_created": 0,
            "shortcuts_deleted": 0,
            "folders_updated": 0,
            "errors": 0,
            "last_sync": None,
        }
    
    async def sync_source_to_user_folders(
        self, 
        source_folder_id: str,
        user_ids: Optional[List[int]] = None,
        force_full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize files from source folder to all user folders.
        
        Args:
            source_folder_id: Google Drive ID of the source folder.
            user_ids: Optional list of specific user IDs to sync.
            force_full_sync: If True, perform full sync regardless of last sync time.
            
        Returns:
            Dictionary with sync results and statistics.
            
        Raises:
            SynchronizationError: If synchronization fails.
        """
        sync_start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting sync from source folder {source_folder_id}")
            
            # Get files from source folder
            since_time = None if force_full_sync else self._get_last_sync_time()
            source_files = await self.drive_service.process_files_for_sync(
                source_folder_id, 
                since=since_time
            )
            
            logger.info(f"Found {len(source_files)} files to sync (since: {since_time})")
            
            # Get users who need sync
            users = await self._get_users_for_sync(user_ids)
            logger.info(f"Syncing to {len(users)} users")
            
            # Track sync results
            sync_results = {
                "users_processed": 0,
                "files_processed": len(source_files),
                "total_shortcuts_created": 0,
                "total_shortcuts_deleted": 0,
                "errors": [],
                "started_at": sync_start_time,
                "completed_at": None,
            }
            
            # Process each user
            for user in users:
                try:
                    user_result = await self._sync_user_folder(
                        user, source_files, source_folder_id
                    )
                    
                    sync_results["users_processed"] += 1
                    sync_results["total_shortcuts_created"] += user_result.get("shortcuts_created", 0)
                    sync_results["total_shortcuts_deleted"] += user_result.get("shortcuts_deleted", 0)
                    
                    logger.debug(f"Synced user {user.id}: {user_result}")
                    
                except Exception as e:
                    error_msg = f"Error syncing user {user.id}: {e}"
                    logger.error(error_msg)
                    sync_results["errors"].append(error_msg)
                    self.sync_stats["errors"] += 1
            
            # Update global sync statistics
            self.sync_stats["users_synced"] += sync_results["users_processed"]
            self.sync_stats["files_processed"] += len(source_files)
            self.sync_stats["shortcuts_created"] += sync_results["total_shortcuts_created"]
            self.sync_stats["shortcuts_deleted"] += sync_results["total_shortcuts_deleted"]
            self.sync_stats["last_sync"] = sync_start_time
            
            sync_results["completed_at"] = datetime.utcnow()
            sync_results["duration_seconds"] = (
                sync_results["completed_at"] - sync_start_time
            ).total_seconds()
            
            logger.info(f"Sync completed: {sync_results['users_processed']} users, "
                       f"{sync_results['total_shortcuts_created']} shortcuts created")
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            self.sync_stats["errors"] += 1
            raise SynchronizationError(f"Failed to sync source to user folders: {e}")
    
    async def sync_single_user(
        self, 
        user_id: int, 
        source_folder_id: str,
        force_reorganize: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize files for a single user.
        
        Args:
            user_id: Database ID of the user to sync.
            source_folder_id: Google Drive ID of the source folder.
            force_reorganize: If True, recreate the entire folder structure.
            
        Returns:
            Dictionary with sync results for this user.
            
        Raises:
            SynchronizationError: If sync fails.
        """
        try:
            logger.info(f"Starting single user sync for user {user_id}")
            
            # Get user with folder information
            result = await self.db_session.execute(
                select(User)
                .options(selectinload(User.user_folder))
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise SynchronizationError(f"User {user_id} not found")
            
            # Get source files
            source_files = await self.drive_service.process_files_for_sync(source_folder_id)
            
            # Sync this user
            return await self._sync_user_folder(
                user, source_files, source_folder_id, force_reorganize
            )
            
        except Exception as e:
            logger.error(f"Single user sync failed for user {user_id}: {e}")
            self.sync_stats["errors"] += 1
            raise SynchronizationError(f"Failed to sync user {user_id}: {e}")
    
    async def detect_file_changes(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Google Drive webhook notifications for file changes.
        
        Args:
            webhook_data: Webhook payload from Google Drive.
            
        Returns:
            Dictionary with change detection results.
            
        Raises:
            SynchronizationError: If change detection fails.
        """
        try:
            logger.info(f"Processing webhook notification: {webhook_data.get('resourceState', 'unknown')}")
            
            # Parse webhook data
            resource_id = webhook_data.get('resourceId')
            resource_state = webhook_data.get('resourceState', 'unknown')
            
            if resource_state not in ['update', 'add', 'remove']:
                logger.debug(f"Ignoring webhook state: {resource_state}")
                return {"status": "ignored", "reason": f"Unsupported state: {resource_state}"}
            
            # Get the folder ID from the webhook (this would be the source folder)
            # In a real implementation, we'd need to track which webhooks correspond to which folders
            # For now, we'll assume the webhook is for a source folder and trigger a general sync
            
            # Find users who have this as their source folder
            result = await self.db_session.execute(
                select(UserFolder).where(UserFolder.source_folder_id == resource_id)
            )
            user_folders = result.scalars().all()
            
            if not user_folders:
                logger.warning(f"No user folders found for source folder {resource_id}")
                return {"status": "no_users", "resource_id": resource_id}
            
            # Trigger sync for affected users
            user_ids = [uf.user_id for uf in user_folders]
            sync_result = await self.sync_source_to_user_folders(
                resource_id, 
                user_ids=user_ids
            )
            
            return {
                "status": "sync_triggered",
                "resource_id": resource_id,
                "affected_users": len(user_ids),
                "sync_result": sync_result
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.sync_stats["errors"] += 1
            raise SynchronizationError(f"Failed to process file changes: {e}")
    
    async def update_user_shortcuts(
        self, 
        user: User, 
        new_files: List[Dict[str, Any]],
        removed_files: List[str] = None
    ) -> Dict[str, Any]:
        """
        Update shortcuts for a user based on file changes.
        
        Args:
            user: User to update shortcuts for.
            new_files: List of new or modified files.
            removed_files: List of file IDs that were removed.
            
        Returns:
            Dictionary with update results.
        """
        try:
            logger.info(f"Updating shortcuts for user {user.id}")
            
            if not user.user_folder:
                logger.warning(f"User {user.id} has no folder structure, skipping")
                return {"shortcuts_created": 0, "shortcuts_deleted": 0, "status": "no_folder"}
            
            shortcuts_created = 0
            shortcuts_deleted = 0
            
            # Process new/modified files
            if new_files:
                # Filter files for this user's instruments
                accessible_files = []
                for file_data in new_files:
                    try:
                        parsed = parse_filename(file_data['filename'])
                        if (parsed.file_type.value == "audio" or 
                            is_chart_accessible_by_user(parsed.key, user.instruments)):
                            accessible_files.append(file_data)
                    except Exception as e:
                        logger.warning(f"Error parsing file {file_data.get('filename', 'unknown')}: {e}")
                
                # Create shortcuts for accessible files
                if accessible_files:
                    shortcuts_created = await self.organizer.create_shortcuts_for_user(
                        user, accessible_files
                    )
            
            # Process removed files (remove corresponding shortcuts)
            if removed_files:
                shortcuts_deleted = await self._remove_user_shortcuts(user, removed_files)
            
            # Update user folder sync status
            user.user_folder.last_sync = datetime.utcnow()
            user.user_folder.sync_status = SyncStatus.COMPLETED
            user.user_folder.file_count = user.user_folder.file_count + shortcuts_created - shortcuts_deleted
            
            await self.db_session.commit()
            
            return {
                "shortcuts_created": shortcuts_created,
                "shortcuts_deleted": shortcuts_deleted,
                "status": "updated"
            }
            
        except Exception as e:
            logger.error(f"Error updating shortcuts for user {user.id}: {e}")
            raise SynchronizationError(f"Failed to update user shortcuts: {e}")
    
    async def _sync_user_folder(
        self,
        user: User,
        source_files: List[Dict[str, Any]],
        source_folder_id: str,
        force_reorganize: bool = False
    ) -> Dict[str, Any]:
        """
        Synchronize a single user's folder with source files.
        
        Args:
            user: User to sync.
            source_files: Files from the source folder.
            source_folder_id: ID of the source folder.
            force_reorganize: If True, recreate folder structure.
            
        Returns:
            Dictionary with sync results for this user.
        """
        try:
            logger.debug(f"Syncing folder for user {user.id} ({user.name})")
            
            # Update user folder sync status
            if user.user_folder:
                user.user_folder.sync_status = SyncStatus.IN_PROGRESS
                await self.db_session.commit()
            
            # Ensure user has folder structure
            if not user.user_folder or force_reorganize:
                folder_id = await create_user_folder_if_needed(
                    user, self.organizer, self.db_session
                )
            else:
                folder_id = user.user_folder.google_folder_id
            
            # Create shortcuts for accessible files
            shortcuts_created = await self.organizer.create_shortcuts_for_user(
                user, source_files
            )
            
            # Update user folder record
            user.user_folder.last_sync = datetime.utcnow()
            user.user_folder.sync_status = SyncStatus.COMPLETED
            user.user_folder.sync_error = None
            user.user_folder.file_count = shortcuts_created
            
            await self.db_session.commit()
            
            return {
                "user_id": user.id,
                "folder_id": folder_id,
                "shortcuts_created": shortcuts_created,
                "shortcuts_deleted": 0,  # For now, we don't track deletions
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error syncing user {user.id}: {e}")
            
            # Update user folder with error status
            if user.user_folder:
                user.user_folder.sync_status = SyncStatus.ERROR
                user.user_folder.sync_error = str(e)
                await self.db_session.commit()
            
            raise SynchronizationError(f"Failed to sync user {user.id}: {e}")
    
    async def _get_users_for_sync(self, user_ids: Optional[List[int]] = None) -> List[User]:
        """
        Get users who need synchronization.
        
        Args:
            user_ids: Optional list of specific user IDs.
            
        Returns:
            List of User objects with folder information loaded.
        """
        query = (
            select(User)
            .options(
                selectinload(User.user_folder),
                selectinload(User.band)
            )
            .where(User.is_active)
        )
        
        if user_ids:
            query = query.where(User.id.in_(user_ids))
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def _remove_user_shortcuts(self, user: User, removed_file_ids: List[str]) -> int:
        """
        Remove shortcuts for files that no longer exist.
        
        Args:
            user: User to remove shortcuts for.
            removed_file_ids: List of Google Drive file IDs that were removed.
            
        Returns:
            Number of shortcuts removed.
        """
        # This is a simplified implementation
        # In a real system, we'd need to track which shortcuts correspond to which files
        logger.info(f"Would remove shortcuts for {len(removed_file_ids)} files for user {user.id}")
        return 0  # Placeholder
    
    def _get_last_sync_time(self) -> Optional[datetime]:
        """
        Get the last successful sync time across all users.
        
        Returns:
            Last sync timestamp or None for full sync.
        """
        if self.sync_stats["last_sync"]:
            return self.sync_stats["last_sync"]
        
        # Fallback: check database for most recent sync
        # This would require a query to find the most recent successful sync
        return None
    
    async def get_sync_status(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get synchronization status information.
        
        Args:
            user_id: Optional user ID to get specific status for.
            
        Returns:
            Dictionary with sync status information.
        """
        try:
            if user_id:
                # Get status for specific user
                result = await self.db_session.execute(
                    select(User)
                    .options(selectinload(User.user_folder))
                    .where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return {"error": f"User {user_id} not found"}
                
                if not user.user_folder:
                    return {
                        "user_id": user_id,
                        "sync_status": "not_initialized",
                        "message": "User has no folder structure"
                    }
                
                # Estimate sync time if needed
                estimated_time = None
                if user.user_folder.sync_status in [SyncStatus.PENDING, SyncStatus.IN_PROGRESS]:
                    estimated_time = await estimate_sync_time(
                        user.user_folder.file_count or 50,  # Default estimate
                        10  # Estimated song count
                    )
                
                return {
                    "user_id": user_id,
                    "sync_status": user.user_folder.sync_status,
                    "last_sync": user.user_folder.last_sync,
                    "file_count": user.user_folder.file_count,
                    "sync_error": user.user_folder.sync_error,
                    "estimated_sync_time": estimated_time
                }
            
            else:
                # Get global sync statistics
                return {
                    "global_stats": self.sync_stats.copy(),
                    "status": "active" if self.sync_stats["last_sync"] else "not_started"
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {"error": f"Failed to get sync status: {e}"}
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics."""
        return self.sync_stats.copy()
    
    def reset_sync_stats(self) -> None:
        """Reset synchronization statistics."""
        self.sync_stats = {
            "users_synced": 0,
            "files_processed": 0,
            "shortcuts_created": 0,
            "shortcuts_deleted": 0,
            "folders_updated": 0,
            "errors": 0,
            "last_sync": None,
        }


# Utility functions for background sync operations

async def schedule_sync_for_users(
    user_ids: List[int],
    source_folder_id: str,
    synchronizer: FileSynchronizer,
    delay_seconds: int = 0
) -> str:
    """
    Schedule a sync operation for specific users.
    
    Args:
        user_ids: List of user IDs to sync.
        source_folder_id: Google Drive source folder ID.
        synchronizer: FileSynchronizer instance.
        delay_seconds: Delay before starting sync.
        
    Returns:
        Job ID for tracking the sync operation.
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    async def run_sync():
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
        try:
            await synchronizer.sync_source_to_user_folders(
                source_folder_id,
                user_ids=user_ids
            )
            logger.info(f"Scheduled sync job {job_id} completed successfully")
        except Exception as e:
            logger.error(f"Scheduled sync job {job_id} failed: {e}")
    
    # Start the sync task in the background
    asyncio.create_task(run_sync())
    
    logger.info(f"Scheduled sync job {job_id} for {len(user_ids)} users")
    return job_id


async def cleanup_stale_folders(
    synchronizer: FileSynchronizer,
    max_age_hours: int = 24
) -> Dict[str, Any]:
    """
    Clean up stale folder structures and sync logs.
    
    Args:
        synchronizer: FileSynchronizer instance.
        max_age_hours: Maximum age in hours before considering folders stale.
        
    Returns:
        Dictionary with cleanup results.
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Find stale user folders
        result = await synchronizer.db_session.execute(
            select(UserFolder)
            .where(
                UserFolder.sync_status == SyncStatus.IN_PROGRESS,
                UserFolder.updated_at < cutoff_time
            )
        )
        stale_folders = result.scalars().all()
        
        # Reset stale folders to pending status
        folders_reset = 0
        for folder in stale_folders:
            folder.sync_status = SyncStatus.STALE
            folder.sync_error = f"Sync operation timed out after {max_age_hours} hours"
            folders_reset += 1
        
        await synchronizer.db_session.commit()
        
        logger.info(f"Reset {folders_reset} stale folder sync operations")
        
        return {
            "folders_reset": folders_reset,
            "cutoff_time": cutoff_time,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {"error": str(e), "status": "failed"}