import logging
from typing import Dict

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.connection import get_db_session_dependency
from ..models.user import User, UserRole
from ..services.content_parser import INSTRUMENT_KEY_MAPPING

logger = logging.getLogger(__name__)


async def get_current_user(
    session: AsyncSession = Depends(get_db_session_dependency),
) -> User:
    """Retrieve the current authenticated user."""
    result = await session.execute(
        select(User).options(
            selectinload(User.user_folder),
            selectinload(User.band),
        ).where(User.id == 1)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return user


async def get_drive_credentials():
    """Placeholder for obtaining Google Drive credentials."""
    return None


async def list_available_instruments() -> Dict[str, Dict[str, str]]:
    """List all available instruments organized by key."""
    instruments_by_key: Dict[str, list] = {}
    for instrument, key in INSTRUMENT_KEY_MAPPING.items():
        instruments_by_key.setdefault(key, [])
        display_name = instrument.replace("_", " ").title()
        instruments_by_key[key].append(
            {"name": instrument, "display_name": display_name, "key": key}
        )
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
            "F": "F transposing instruments",
        },
    }


async def list_available_roles() -> Dict[str, Dict[str, str]]:
    """List all available user roles."""
    roles_info = {
        UserRole.MUSICIAN: {
            "name": "Musician",
            "description": "Regular band member with access to their instrument-specific content",
            "permissions": [
                "View own folders",
                "Sync own folders",
                "Update own instruments",
            ],
        },
        UserRole.BAND_LEADER: {
            "name": "Band Leader",
            "description": "Band leader with administrative privileges for the band",
            "permissions": [
                "All musician permissions",
                "View all band members' folders",
                "Manage band members' roles and instruments",
                "Manage band Google Drive integration",
            ],
        },
        UserRole.ADMIN: {
            "name": "Administrator",
            "description": "Platform administrator with full access",
            "permissions": [
                "All band leader permissions",
                "Manage multiple bands",
                "View platform statistics",
                "Manage system settings",
            ],
        },
    }
    return {
        "roles": roles_info,
        "role_hierarchy": [UserRole.MUSICIAN, UserRole.BAND_LEADER, UserRole.ADMIN],
    }
