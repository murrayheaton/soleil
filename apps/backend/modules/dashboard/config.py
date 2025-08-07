"""
Dashboard Module Configuration
"""

from typing import List, Dict
from pydantic import Field
from modules.core.module_config import BaseModuleConfig


class DashboardModuleConfig(BaseModuleConfig):
    """Configuration for the Dashboard module"""
    
    # Module Settings
    available_modules: List[str] = Field(
        default_factory=lambda: [
            "gigs",
            "repertoire",
            "offers",
            "practice",
            "calendar",
            "stats"
        ],
        description="List of available dashboard modules"
    )
    default_modules: List[str] = Field(
        default_factory=lambda: ["gigs", "repertoire", "calendar"],
        description="Default modules for new users"
    )
    max_modules_per_user: int = Field(
        default=6,
        description="Maximum modules a user can have"
    )
    
    # Layout Configuration
    grid_columns: int = Field(
        default=12,
        description="Number of grid columns"
    )
    grid_row_height: int = Field(
        default=50,
        description="Grid row height in pixels"
    )
    module_min_width: int = Field(
        default=3,
        description="Minimum module width in grid units"
    )
    module_min_height: int = Field(
        default=4,
        description="Minimum module height in grid units"
    )
    
    # Data Refresh
    auto_refresh: bool = Field(
        default=True,
        description="Enable auto-refresh of dashboard data"
    )
    refresh_interval_seconds: int = Field(
        default=60,
        description="Auto-refresh interval in seconds"
    )
    
    # Module Configurations
    module_configs: Dict[str, Dict] = Field(
        default_factory=lambda: {
            "gigs": {
                "show_past_days": 7,
                "show_future_days": 30,
                "enable_quick_add": True
            },
            "repertoire": {
                "items_per_page": 20,
                "show_recent_additions": True,
                "enable_search": True
            },
            "stats": {
                "time_period": "monthly",
                "show_charts": True,
                "metrics": ["practice_time", "gigs_played", "new_songs"]
            }
        },
        description="Configuration for individual dashboard modules"
    )
    
    # Caching
    enable_dashboard_cache: bool = Field(
        default=True,
        description="Enable dashboard data caching"
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Dashboard cache TTL in seconds"
    )
    
    # Permissions
    allow_customization: bool = Field(
        default=True,
        description="Allow users to customize their dashboard"
    )
    admin_only_modules: List[str] = Field(
        default_factory=lambda: ["admin_stats", "user_management"],
        description="Modules only available to admins"
    )
    
    # Module specific
    module_name: str = Field(default="dashboard")
    required_modules: List[str] = Field(
        default_factory=lambda: ["core", "auth"]
    )