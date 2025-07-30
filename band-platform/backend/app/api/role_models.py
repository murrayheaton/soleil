from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from ..services.content_parser import INSTRUMENT_KEY_MAPPING
from ..models.user import UserRole


class InstrumentUpdate(BaseModel):
    """Schema for updating user instruments."""

    instruments: List[str] = Field(..., description="List of instrument names")
    primary_instrument: Optional[str] = Field(None, description="Primary instrument")
    reorganize_folders: bool = Field(
        default=True,
        description="Whether to reorganize folders after instrument change",
    )

    @validator("instruments")
    def validate_instruments(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one instrument must be specified")
        for instrument in v:
            normalized = instrument.lower().replace(" ", "_").replace("-", "_")
            if normalized not in INSTRUMENT_KEY_MAPPING:
                raise ValueError(f"Unknown instrument: {instrument}")
        return v

    @validator("primary_instrument")
    def validate_primary_instrument(cls, v: Optional[str], values) -> Optional[str]:
        if v and "instruments" in values:
            normalized_primary = v.lower().replace(" ", "_").replace("-", "_")
            normalized_instruments = [
                inst.lower().replace(" ", "_").replace("-", "_")
                for inst in values["instruments"]
            ]
            if normalized_primary not in normalized_instruments:
                raise ValueError("Primary instrument must be in the instruments list")
        return v


class RoleUpdate(BaseModel):
    """Schema for updating user role."""

    role: UserRole = Field(..., description="New user role")
    reorganize_folders: bool = Field(
        default=False,
        description="Whether to reorganize folders after role change",
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
