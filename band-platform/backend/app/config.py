"""
Configuration settings for the Band Platform application.

This module uses pydantic-settings for environment variable management
following the PRP requirements for Google API credentials and JWT settings.
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be configured via environment variables.
    Sensitive values like API keys should be set via environment variables.
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Configuration
    app_name: str = Field(default="Band Platform", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://band_user:band_pass@localhost:5432/band_platform",
        description="PostgreSQL database URL for async connections"
    )
    database_echo: bool = Field(default=False, description="Echo SQL statements")
    
    # JWT Configuration
    # Provide a default to avoid errors during test imports
    jwt_secret_key: str = Field(
        default="test_secret",
        description="JWT secret key for token signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, 
        description="JWT access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration in days"
    )
    
    # Google API Configuration
    google_client_id: str = Field(
        default="test_client_id",
        description="Google OAuth 2.0 Client ID",
    )
    google_client_secret: str = Field(
        default="test_client_secret",
        description="Google OAuth 2.0 Client Secret",
    )
    google_redirect_uri: str = Field(
        default="https://solepower.live/api/auth/google/callback",
        description="Google OAuth redirect URI"
    )
    
    # Google API Scopes
    google_drive_scope: str = Field(
        default="https://www.googleapis.com/auth/drive.readonly",
        description="Google Drive API scope"
    )
    google_sheets_scope: str = Field(
        default="https://www.googleapis.com/auth/spreadsheets.readonly",
        description="Google Sheets API scope"
    )
    google_calendar_scope: str = Field(
        default="https://www.googleapis.com/auth/calendar.readonly",
        description="Google Calendar API scope"
    )
    
    # Redis Configuration (for caching and session storage)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # File Storage Configuration
    file_storage_path: str = Field(
        default="storage",
        description="Local file storage path for cached files"
    )
    max_file_size_mb: int = Field(
        default=50,
        description="Maximum file size in MB for uploads"
    )
    
    # Sync Engine Configuration
    sync_enabled: bool = Field(default=True, description="Enable sync engine")
    sync_interval_minutes: int = Field(
        default=15,
        description="Sync interval in minutes for periodic sync"
    )
    webhook_secret: str = Field(
        default="",
        description="Webhook secret for Google API notifications"
    )
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Rate limit: requests per minute per user"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Development Configuration
    auto_reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    @property
    def google_scopes(self) -> list[str]:
        """
        Get all Google API scopes as a list.
        
        Returns:
            List of all configured Google API scopes.
        """
        return [
            self.google_drive_scope,
            self.google_sheets_scope,
            self.google_calendar_scope
        ]
    
    @property
    def database_config(self) -> dict[str, any]:
        """
        Get database configuration for SQLAlchemy.
        
        Returns:
            Dictionary with database configuration parameters.
        """
        return {
            "echo": self.database_echo,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
        }
    
    def get_google_credentials_config(self) -> dict[str, str]:
        """
        Get Google OAuth credentials configuration.
        
        Returns:
            Dictionary with Google OAuth configuration.
        """
        return {
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "redirect_uri": self.google_redirect_uri,
            "scopes": self.google_scopes
        }


def load_settings() -> Settings:
    """
    Load and validate application settings.
    
    Returns:
        Configured Settings instance.
        
    Raises:
        ValueError: If required settings are missing or invalid.
    """
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        
        # Provide helpful error messages for missing required fields
        if "jwt_secret_key" in str(e).lower():
            error_msg += "\nMake sure to set JWT_SECRET_KEY in your .env file"
        if "google_client_id" in str(e).lower():
            error_msg += "\nMake sure to set GOOGLE_CLIENT_ID in your .env file"
        if "google_client_secret" in str(e).lower():
            error_msg += "\nMake sure to set GOOGLE_CLIENT_SECRET in your .env file"
            
        raise ValueError(error_msg) from e


# Global settings instance
settings = load_settings()