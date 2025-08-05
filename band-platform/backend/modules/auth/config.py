"""
Auth Module Configuration
"""

from typing import List, Optional
from pydantic import Field
from modules.core.module_config import BaseModuleConfig


class AuthModuleConfig(BaseModuleConfig):
    """Configuration for the Auth module"""
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default="your-secret-key-here",
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    
    # OAuth Settings
    google_client_id: Optional[str] = Field(
        default=None,
        description="Google OAuth client ID"
    )
    google_client_secret: Optional[str] = Field(
        default=None,
        description="Google OAuth client secret"
    )
    oauth_redirect_uri: str = Field(
        default="http://localhost:3000/auth/callback",
        description="OAuth redirect URI"
    )
    
    # Session Settings
    session_lifetime_hours: int = Field(
        default=24,
        description="Session lifetime in hours"
    )
    max_sessions_per_user: int = Field(
        default=5,
        description="Maximum concurrent sessions per user"
    )
    
    # Security Settings
    password_min_length: int = Field(
        default=8,
        description="Minimum password length"
    )
    require_email_verification: bool = Field(
        default=True,
        description="Require email verification for new users"
    )
    allowed_email_domains: List[str] = Field(
        default_factory=list,
        description="List of allowed email domains (empty = all allowed)"
    )
    
    # Rate Limiting
    login_attempts_limit: int = Field(
        default=5,
        description="Maximum login attempts before lockout"
    )
    login_lockout_minutes: int = Field(
        default=15,
        description="Lockout duration in minutes"
    )
    
    # Module specific
    module_name: str = Field(default="auth")
    required_modules: List[str] = Field(default_factory=lambda: ["core"])
    
    class Config:
        env_prefix = "AUTH_"  # Environment variable prefix