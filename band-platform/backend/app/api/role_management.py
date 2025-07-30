"""
Role management API endpoints for user instrument and role changes.

This module provides REST API endpoints for managing user roles, instruments,
and triggering folder reorganization when user access patterns change.
"""

import logging
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.connection import get_db_session_dependency
from ..models.user import User, UserRole, UserSchema
from ..models.folder_structure import SyncStatus
from ..services.content_parser import INSTRUMENT_KEY_MAPPING, get_keys_for_instruments
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


# Pydantic schemas for role management

class InstrumentUpdate(BaseModel):
    """Schema for updating user instruments."""
    instruments: List[str] = Field(..., description="List of instrument names")
    primary_instrument: Optional[str] = Field(None, description="Primary instrument")
    reorganize_folders: bool = Field(
        default=True, 
        description="Whether to reorganize folders after instrument change"
    )
    
    @validator('instruments')
    def validate_instruments(cls, v):
        """Validate that all instruments are recognized."""
        if not v:
            raise ValueError("At least one instrument must be specified")
        
        for instrument in v:
            normalized = instrument.lower().replace(" ", "_").replace("-", "_")
            if normalized not in INSTRUMENT_KEY_MAPPING:
                raise ValueError(f"Unknown instrument: {instrument}")
        
        return v
    
    @validator('primary_instrument')
    def validate_primary_instrument(cls, v, values):
        """Validate that primary instrument is in the instruments list."""
        if v and 'instruments' in values:
            normalized_primary = v.lower().replace(" ", "_").replace("-", "_")
            normalized_instruments = [
                inst.lower().replace(" ", "_").replace("-", "_") 
                for inst in values['instruments']
            ]
            
            if normalized_primary not in normalized_instruments:
                raise ValueError("Primary instrument must be in the instruments list")
        
        return v


class RoleUpdate(BaseModel):
    """Schema for updating user role."""
    role: UserRole = Field(..., description="New user role")
    reorganize_folders: bool = Field(
        default=False,
        description="Whether to reorganize folders after role change"
    )


class AccessibleFilesResponse(BaseModel):
    """Response schema for accessible files query."""
    user_id: int
    instruments: List[str]
    accessible_keys: List[str]
    total_files: int
    accessible_files: int
    files_by_key: Dict[str, int]
    files_by_type: Dict[str, int]


class InstrumentReorganizeResponse(BaseModel):
    """Response schema for instrument update with reorganization."""
    user_id: int
    old_instruments: List[str]
    new_instruments: List[str]
    old_keys: List[str]
    new_keys: List[str]
    reorganization_status: str
    estimated_completion: Optional[str] = None
    job_id: Optional[str] = None


@router.put("/users/{user_id}/instruments", response_model=InstrumentReorganizeResponse, tags=["Role Management"])
async def update_user_instruments(
    user_id: int,
    instrument_update: InstrumentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Update a user's instruments and optionally reorganize their folders.
    
    Args:
        user_id: ID of the user to update.
        instrument_update: New instrument configuration.
        
    Returns:
        InstrumentReorganizeResponse: Update results and reorganization status.
        
    Raises:
        HTTPException: If not authorized or user not found.
    """
    try:
        logger.info(f"Updating instruments for user {user_id}")
        
        # Check permissions - users can update their own instruments, admins can update anyone's
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own instruments"
            )
        
        # Get target user
        result = await session.execute(
            select(User)
            .options(
                selectinload(User.user_folder),
                selectinload(User.band)
            )
            .where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Store old configuration for response
        old_instruments = target_user.instruments.copy()
        old_keys = get_keys_for_instruments(old_instruments)
        
        # Update user instruments
        target_user.instruments = instrument_update.instruments
        target_user.primary_instrument = instrument_update.primary_instrument
        
        # Calculate new keys
        new_keys = get_keys_for_instruments(instrument_update.instruments)
        
        await session.commit()
        
        logger.info(f"Updated instruments for user {user_id}: {old_instruments} -> {instrument_update.instruments}")
        
        # Prepare response
        response = InstrumentReorganizeResponse(
            user_id=user_id,
            old_instruments=old_instruments,
            new_instruments=instrument_update.instruments,
            old_keys=old_keys,
            new_keys=new_keys,
            reorganization_status="not_requested"
        )
        
        # Trigger folder reorganization if requested
        if instrument_update.reorganize_folders and target_user.user_folder:
            if target_user.band and target_user.band.google_drive_folder_id:
                # Get Google Drive credentials
                credentials = await get_drive_credentials()
                if credentials:
                    # Schedule reorganization
                    job_id = await schedule_sync_for_users(
                        user_ids=[user_id],
                        source_folder_id=target_user.band.google_drive_folder_id,
                        synchronizer=FileSynchronizer(
                            GoogleDriveService(credentials),
                            session
                        ),
                        delay_seconds=2  # Small delay to ensure database changes are committed
                    )
                    
                    # Update folder status
                    target_user.user_folder.sync_status = SyncStatus.IN_PROGRESS
                    await session.commit()
                    
                    response.reorganization_status = "started"
                    response.estimated_completion = "60s"
                    response.job_id = job_id
                    
                    logger.info(f"Scheduled folder reorganization job {job_id} for user {user_id}")
                else:
                    response.reorganization_status = "failed"
                    logger.warning("No Google Drive credentials available for reorganization")
            else:
                response.reorganization_status = "no_drive_integration"
                logger.warning(f"User {user_id} has no band or Google Drive integration")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instruments for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update instruments: {str(e)}"
        )


@router.put("/users/{user_id}/role", response_model=UserSchema, tags=["Role Management"])
async def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Update a user's role in the band (admin only).
    
    Args:
        user_id: ID of the user to update.
        role_update: New role configuration.
        
    Returns:
        UserSchema: Updated user information.
        
    Raises:
        HTTPException: If not authorized or user not found.
    """
    try:
        logger.info(f"Updating role for user {user_id} to {role_update.role}")
        
        # Check permissions - only admins can change roles
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can change user roles"
            )
        
        # Get target user
        result = await session.execute(
            select(User)
            .options(
                selectinload(User.user_folder),
                selectinload(User.band)
            )
            .where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Store old role
        old_role = target_user.role
        
        # Update role
        target_user.role = role_update.role
        await session.commit()
        
        logger.info(f"Updated role for user {user_id}: {old_role} -> {role_update.role}")
        
        # Trigger folder reorganization if requested (role changes might affect access)
        if role_update.reorganize_folders and target_user.user_folder:
            if target_user.band and target_user.band.google_drive_folder_id:
                credentials = await get_drive_credentials()
                if credentials:
                    job_id = await schedule_sync_for_users(
                        user_ids=[user_id],
                        source_folder_id=target_user.band.google_drive_folder_id,
                        synchronizer=FileSynchronizer(
                            GoogleDriveService(credentials),
                            session
                        )
                    )
                    
                    target_user.user_folder.sync_status = SyncStatus.IN_PROGRESS
                    await session.commit()
                    
                    logger.info(f"Scheduled folder reorganization job {job_id} for role change")
        
        return UserSchema.from_orm(target_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update role: {str(e)}"
        )


@router.post("/users/{user_id}/reorganize", tags=["Role Management"])
async def trigger_folder_reorganization(
    user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Trigger folder reorganization for a user based on their current instruments.
    
    Args:
        user_id: ID of the user to reorganize folders for.
        
    Returns:
        Reorganization status and job information.
        
    Raises:
        HTTPException: If not authorized or user not found.
    """
    try:
        logger.info(f"Triggering folder reorganization for user {user_id}")
        
        # Check permissions
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="You can only reorganize your own folders"
            )
        
        # Get target user
        result = await session.execute(
            select(User)
            .options(
                selectinload(User.user_folder),
                selectinload(User.band)
            )
            .where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        if not target_user.user_folder:
            raise HTTPException(
                status_code=400,
                detail="User has no folder structure to reorganize"
            )
        
        if not target_user.band or not target_user.band.google_drive_folder_id:
            raise HTTPException(
                status_code=400,
                detail="User's band has no Google Drive integration"
            )
        
        # Check if reorganization is already in progress
        if target_user.user_folder.sync_status == SyncStatus.IN_PROGRESS:
            return {
                "status": "already_running",
                "message": "Folder reorganization is already in progress",
                "user_id": user_id
            }
        
        # Get Google Drive credentials
        credentials = await get_drive_credentials()
        if not credentials:
            raise HTTPException(
                status_code=503,
                detail="Google Drive integration not available"
            )
        
        # Schedule reorganization
        job_id = await schedule_sync_for_users(
            user_ids=[user_id],
            source_folder_id=target_user.band.google_drive_folder_id,
            synchronizer=FileSynchronizer(
                GoogleDriveService(credentials),
                session
            )
        )
        
        # Update folder status
        target_user.user_folder.sync_status = SyncStatus.IN_PROGRESS
        target_user.user_folder.sync_error = None
        await session.commit()
        
        logger.info(f"Scheduled reorganization job {job_id} for user {user_id}")
        
        return {
            "status": "reorganization_started",
            "message": f"Folder reorganization started for user {user_id}",
            "user_id": user_id,
            "job_id": job_id,
            "estimated_completion": "60s"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering reorganization for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger reorganization: {str(e)}"
        )


@router.get("/users/{user_id}/accessible-files", response_model=AccessibleFilesResponse, tags=["Role Management"])
async def get_user_accessible_files(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get information about files accessible to a user based on their instruments.
    
    Args:
        user_id: ID of the user to check accessibility for.
        
    Returns:
        AccessibleFilesResponse: File accessibility information.
        
    Raises:
        HTTPException: If not authorized or user not found.
    """
    try:
        # Check permissions
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own accessible files"
            )
        
        # Get target user
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get accessible keys for user's instruments
        accessible_keys = get_keys_for_instruments(target_user.instruments)
        
        # TODO: In a real implementation, we would query the actual files
        # from Google Drive or from a local database of synced files
        # For now, return mock data based on the user's accessible keys
        
        # Mock file counts by key and type
        files_by_key = {key: 10 + len(key) * 5 for key in accessible_keys}  # Mock data
        files_by_type = {
            "chart": sum(files_by_key.values()) if files_by_key else 0,
            "audio": 25,  # Audio files are accessible to everyone
            "other": 5
        }
        
        total_files = 100  # Mock total
        accessible_files = sum(files_by_key.values()) + files_by_type["audio"]
        
        return AccessibleFilesResponse(
            user_id=user_id,
            instruments=target_user.instruments,
            accessible_keys=accessible_keys,
            total_files=total_files,
            accessible_files=accessible_files,
            files_by_key=files_by_key,
            files_by_type=files_by_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accessible files for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get accessible files: {str(e)}"
        )


@router.get("/instruments", tags=["Role Management"])
async def list_available_instruments():
    """
    List all available instruments with their transposition keys.
    
    Returns:
        Dictionary of instruments organized by transposition key.
    """
    try:
        # Group instruments by key
        instruments_by_key = {}
        for instrument, key in INSTRUMENT_KEY_MAPPING.items():
            if key not in instruments_by_key:
                instruments_by_key[key] = []
            
            # Convert to display format
            display_name = instrument.replace("_", " ").title()
            instruments_by_key[key].append({
                "name": instrument,
                "display_name": display_name,
                "key": key
            })
        
        # Sort instruments within each key group
        for key in instruments_by_key:
            instruments_by_key[key].sort(key=lambda x: x["display_name"])
        
        return {
            "instruments_by_key": instruments_by_key,
            "all_keys": sorted(instruments_by_key.keys()),
            "total_instruments": len(INSTRUMENT_KEY_MAPPING),
            "key_descriptions": {
                "C": "Concert pitch instruments",
                "Bb": "B-flat transposing instruments", 
                "Eb": "E-flat transposing instruments",
                "F": "F transposing instruments"
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing instruments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list instruments: {str(e)}"
        )


@router.get("/roles", tags=["Role Management"])
async def list_available_roles():
    """
    List all available user roles and their descriptions.
    
    Returns:
        Dictionary of roles with descriptions and permissions.
    """
    try:
        roles_info = {
            UserRole.MUSICIAN: {
                "name": "Musician",
                "description": "Regular band member with access to their instrument-specific content",
                "permissions": [
                    "View own folders",
                    "Sync own folders",
                    "Update own instruments"
                ]
            },
            UserRole.BAND_LEADER: {
                "name": "Band Leader",
                "description": "Band leader with administrative privileges for the band",
                "permissions": [
                    "All musician permissions",
                    "View all band members' folders",
                    "Manage band members' roles and instruments",
                    "Manage band Google Drive integration"
                ]
            },
            UserRole.ADMIN: {
                "name": "Administrator",
                "description": "Platform administrator with full access",
                "permissions": [
                    "All band leader permissions",
                    "Manage multiple bands",
                    "View platform statistics",
                    "Manage system settings"
                ]
            }
        }
        
        return {
            "roles": roles_info,
            "role_hierarchy": [UserRole.MUSICIAN, UserRole.BAND_LEADER, UserRole.ADMIN]
        }
        
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list roles: {str(e)}"
        )