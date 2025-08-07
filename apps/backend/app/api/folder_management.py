"""
Folder management API endpoints for Google Drive role-based organization.

This module provides REST API endpoints for managing user folder structures,
synchronization operations, and folder content access.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.connection import get_db_session_dependency
from ..models.user import User
from ..models.folder_structure import (
    UserFolder,
    UserSongFolder,
    FolderSyncLog,
    UserFolderSchema, 
    UserSongFolderSchema,
    FolderContentsResponse,
    SyncStatusResponse,
    SyncTriggerResponse,
    FolderSyncLogSchema
)
from ..services.folder_organizer import FolderOrganizer, create_user_folder_if_needed
from ..services.file_synchronizer import FileSynchronizer, schedule_sync_for_users
from ..services.google_drive import GoogleDriveService

logger = logging.getLogger(__name__)

router = APIRouter()


# TODO: Replace with actual authentication dependency
async def get_current_user(
    session: AsyncSession = Depends(get_db_session_dependency)
) -> User:
    """
    Placeholder for getting the current authenticated user.
    
    This should be replaced with actual JWT/OAuth authentication.
    """
    # For now, return a mock user for testing
    # In production, this would validate JWT token and return the actual user
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.user_folder),
            selectinload(User.band)
        )
        .where(User.id == 1)  # Mock user ID
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    return user


async def get_drive_credentials():
    """
    Get Google Drive credentials for the current user/band.
    
    This is a placeholder that should be replaced with actual credential management.
    """
    # TODO: Implement actual credential retrieval from database or OAuth flow
    return None


@router.post("/initialize", response_model=UserFolderSchema, tags=["Folder Management"])
async def initialize_user_folders(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Initialize folder structure for the current user.
    
    Creates a personalized folder structure in Google Drive organized by songs
    and filtered based on the user's instruments.
    
    Returns:
        UserFolderSchema: Information about the created folder structure.
        
    Raises:
        HTTPException: If initialization fails or user has no instruments.
    """
    try:
        logger.info(f"Initializing folders for user {current_user.id} ({current_user.name})")
        
        # Validate user has instruments assigned
        if not current_user.instruments:
            raise HTTPException(
                status_code=400, 
                detail="User must have instruments assigned before creating folders"
            )
        
        # Validate band has Google Drive integration
        if not current_user.band or not current_user.band.google_drive_folder_id:
            raise HTTPException(
                status_code=400,
                detail="Band must have Google Drive integration configured"
            )
        
        # Check if user already has folder structure
        if current_user.user_folder and current_user.user_folder.google_folder_id:
            logger.info(f"User {current_user.id} already has folder structure")
            return UserFolderSchema.from_orm(current_user.user_folder)
        
        # Get Google Drive credentials
        credentials = await get_drive_credentials()
        if not credentials:
            raise HTTPException(
                status_code=503,
                detail="Google Drive integration not available"
            )
        
        # Create folder organizer
        organizer = FolderOrganizer(credentials=credentials, db_session=session)
        
        # Create folder structure
        await create_user_folder_if_needed(
            current_user, organizer, session
        )
        
        # Schedule background sync to populate folders
        background_tasks.add_task(
            _background_sync_user,
            current_user.id,
            current_user.band.google_drive_folder_id,
            session
        )
        
        # Refresh user to get updated folder information
        await session.refresh(current_user)
        
        logger.info(f"Successfully initialized folders for user {current_user.id}")
        return UserFolderSchema.from_orm(current_user.user_folder)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing folders for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize folder structure: {str(e)}"
        )


@router.get("/status", response_model=SyncStatusResponse, tags=["Folder Management"])
async def get_folder_sync_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get synchronization status for the current user's folders.
    
    Returns:
        SyncStatusResponse: Current sync status and statistics.
    """
    try:
        # Get drive service for sync status
        credentials = await get_drive_credentials()
        drive_service = GoogleDriveService(credentials) if credentials else None
        
        if drive_service:
            synchronizer = FileSynchronizer(drive_service, session)
            status_info = await synchronizer.get_sync_status(current_user.id)
        else:
            # Fallback to database-only status
            if current_user.user_folder:
                status_info = {
                    "user_id": current_user.id,
                    "sync_status": current_user.user_folder.sync_status,
                    "last_sync": current_user.user_folder.last_sync,
                    "file_count": current_user.user_folder.file_count,
                    "sync_error": current_user.user_folder.sync_error,
                    "estimated_sync_time": None
                }
            else:
                status_info = {
                    "user_id": current_user.id,
                    "sync_status": "not_initialized",
                    "last_sync": None,
                    "file_count": 0,
                    "sync_error": None,
                    "estimated_sync_time": None
                }
        
        # Count song folders if available
        song_count = 0
        if current_user.user_folder:
            result = await session.execute(
                select(func.count())  # type: ignore
                .select_from(UserSongFolder)
                .where(UserSongFolder.user_folder_id == current_user.user_folder.id)
            )
            song_count = result.scalar() or 0
        
        return SyncStatusResponse(
            user_id=current_user.id,
            sync_status=status_info.get("sync_status", "unknown"),
            last_sync=status_info.get("last_sync"),
            file_count=status_info.get("file_count", 0),
            song_count=song_count,
            sync_error=status_info.get("sync_error"),
            estimated_sync_time=status_info.get("estimated_sync_time")
        )
        
    except Exception as e:
        logger.error(f"Error getting sync status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/sync", response_model=SyncTriggerResponse, tags=["Folder Management"])
async def trigger_folder_sync(
    background_tasks: BackgroundTasks,
    force_full_sync: bool = Query(False, description="Force a complete resync"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Trigger a manual synchronization of the user's folder structure.
    
    Args:
        force_full_sync: If True, perform a complete resync regardless of last sync time.
        
    Returns:
        SyncTriggerResponse: Information about the triggered sync operation.
    """
    try:
        logger.info(f"Triggering sync for user {current_user.id}, force_full={force_full_sync}")
        
        # Validate user has folder structure
        if not current_user.user_folder:
            raise HTTPException(
                status_code=400,
                detail="User has no folder structure. Initialize folders first."
            )
        
        # Validate band has Google Drive integration
        if not current_user.band or not current_user.band.google_drive_folder_id:
            raise HTTPException(
                status_code=400,
                detail="Band Google Drive integration not configured"
            )
        
        # Check if sync is already in progress
        if current_user.user_folder.sync_status == "in_progress":
            return SyncTriggerResponse(
                status="already_running",
                message="Sync operation is already in progress for this user",
                estimated_duration="30s"
            )
        
        # Get Google Drive credentials
        credentials = await get_drive_credentials()
        if not credentials:
            raise HTTPException(
                status_code=503,
                detail="Google Drive integration not available"
            )
        
        # Schedule background sync
        job_id = await schedule_sync_for_users(
            user_ids=[current_user.id],
            source_folder_id=current_user.band.google_drive_folder_id,
            synchronizer=FileSynchronizer(
                GoogleDriveService(credentials),
                session
            )
        )
        
        # Update user folder status
        current_user.user_folder.sync_status = "in_progress"
        await session.commit()
        
        logger.info(f"Scheduled sync job {job_id} for user {current_user.id}")
        
        return SyncTriggerResponse(
            status="sync_started",
            message=f"Folder synchronization started for {current_user.name}",
            estimated_duration="30s",
            job_id=job_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering sync for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger sync: {str(e)}"
        )


@router.get("/contents", response_model=FolderContentsResponse, tags=["Folder Management"])
async def get_folder_contents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get the contents of the user's organized folder structure.
    
    Returns a list of song folders and their file counts, showing the
    organization created based on the user's instrument access.
    
    Returns:
        FolderContentsResponse: User folder structure and contents.
    """
    try:
        # Validate user has folder structure
        if not current_user.user_folder:
            raise HTTPException(
                status_code=404,
                detail="User has no folder structure. Initialize folders first."
            )
        
        # Get song folders for this user
        result = await session.execute(
            select(UserSongFolder)
            .where(UserSongFolder.user_folder_id == current_user.user_folder.id)
            .order_by(UserSongFolder.song_title)
        )
        song_folders = result.scalars().all()
        
        # Calculate total files
        total_files = sum(sf.shortcut_count for sf in song_folders)
        
        return FolderContentsResponse(
            user_folder=UserFolderSchema.from_orm(current_user.user_folder),
            song_folders=[UserSongFolderSchema.from_orm(sf) for sf in song_folders],
            total_files=total_files,
            last_sync=current_user.user_folder.last_sync,
            sync_status=current_user.user_folder.sync_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder contents for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get folder contents: {str(e)}"
        )


@router.get("/contents/{user_id}", response_model=FolderContentsResponse, tags=["Folder Management"])
async def get_user_folder_contents(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get folder contents for a specific user (admin only).
    
    Args:
        user_id: ID of the user whose folders to retrieve.
        
    Returns:
        FolderContentsResponse: Specified user's folder structure and contents.
        
    Raises:
        HTTPException: If not authorized or user not found.
    """
    try:
        # Check if current user has admin privileges
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can view other users' folders"
            )
        
        # Get target user with folder information
        result = await session.execute(
            select(User)
            .options(selectinload(User.user_folder))
            .where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        if not target_user.user_folder:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} has no folder structure"
            )
        
        # Get song folders
        result = await session.execute(
            select(UserSongFolder)
            .where(UserSongFolder.user_folder_id == target_user.user_folder.id)
            .order_by(UserSongFolder.song_title)
        )
        song_folders = result.scalars().all()
        
        # Calculate total files
        total_files = sum(sf.shortcut_count for sf in song_folders)
        
        return FolderContentsResponse(
            user_folder=UserFolderSchema.from_orm(target_user.user_folder),
            song_folders=[UserSongFolderSchema.from_orm(sf) for sf in song_folders],
            total_files=total_files,
            last_sync=target_user.user_folder.last_sync,
            sync_status=target_user.user_folder.sync_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder contents for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get folder contents: {str(e)}"
        )


@router.get("/sync-logs", response_model=List[FolderSyncLogSchema], tags=["Folder Management"])
async def get_sync_logs(
    limit: int = Query(20, ge=1, le=100, description="Number of logs to return"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get recent synchronization logs for the current user.
    
    Args:
        limit: Maximum number of log entries to return.
        
    Returns:
        List of sync log entries for the user.
    """
    try:
        result = await session.execute(
            select(FolderSyncLog)
            .where(FolderSyncLog.user_id == current_user.id)
            .order_by(FolderSyncLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        
        return [FolderSyncLogSchema.from_orm(log) for log in logs]
        
    except Exception as e:
        logger.error(f"Error getting sync logs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync logs: {str(e)}"
        )


@router.delete("/reset", tags=["Folder Management"])
async def reset_user_folder_structure(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Reset and recreate the user's folder structure.
    
    This will delete the existing folder structure and create a new one
    based on the user's current instruments and available files.
    
    Returns:
        Success message with job information.
    """
    try:
        logger.info(f"Resetting folder structure for user {current_user.id}")
        
        if not current_user.user_folder:
            raise HTTPException(
                status_code=404,
                detail="User has no folder structure to reset"
            )
        
        # Mark folder for reset
        current_user.user_folder.sync_status = "pending"
        current_user.user_folder.sync_error = "Folder structure reset requested"
        
        # Clear song folders (they will be recreated)
        await session.execute(
            delete(UserSongFolder)
            .where(UserSongFolder.user_folder_id == current_user.user_folder.id)
        )
        
        await session.commit()
        
        # Schedule background reorganization
        if current_user.band and current_user.band.google_drive_folder_id:
            background_tasks.add_task(
                _background_sync_user,
                current_user.id,
                current_user.band.google_drive_folder_id,
                session,
                force_reorganize=True
            )
        
        return {
            "message": f"Folder structure reset initiated for {current_user.name}",
            "status": "reset_started",
            "estimated_completion": "60s"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting folders for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset folder structure: {str(e)}"
        )


# Background task functions

async def _background_sync_user(
    user_id: int,
    source_folder_id: str,
    session: AsyncSession,
    force_reorganize: bool = False
):
    """
    Background task to sync a user's folders.
    
    Args:
        user_id: ID of the user to sync.
        source_folder_id: Google Drive source folder ID.
        session: Database session.
        force_reorganize: If True, recreate folder structure.
    """
    try:
        logger.info(f"Starting background sync for user {user_id}")
        
        # Get Google Drive credentials
        credentials = await get_drive_credentials()
        if not credentials:
            logger.error("No Google Drive credentials available for background sync")
            return
        
        # Create services
        drive_service = GoogleDriveService(credentials)
        synchronizer = FileSynchronizer(drive_service, session)
        
        # Perform sync
        await synchronizer.sync_single_user(
            user_id, 
            source_folder_id,
            force_reorganize=force_reorganize
        )
        
        logger.info(f"Background sync completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Background sync failed for user {user_id}: {e}")
        
        # Update user folder with error status
        try:
            result = await session.execute(
                select(UserFolder).where(UserFolder.user_id == user_id)
            )
            user_folder = result.scalar_one_or_none()
            
            if user_folder:
                user_folder.sync_status = "error"
                user_folder.sync_error = str(e)
                await session.commit()
                
        except Exception as db_error:
            logger.error(f"Failed to update error status for user {user_id}: {db_error}")


