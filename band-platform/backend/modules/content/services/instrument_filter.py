"""
Instrument-based content filtering service.

This module provides intelligent filtering of content based on user instruments
and the key mapping logic for transposing instruments.
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# TODO: Re-enable when auth module is available
# from ...auth.models import User
# from ..models import Chart, Audio
from .content_parser import get_keys_for_instruments, is_chart_accessible_by_user

logger = logging.getLogger(__name__)


class InstrumentFilter:
    """
    Service for filtering content based on user instruments.
    
    Provides intelligent filtering of charts and audio files based on
    the user's instrument assignments and transposition requirements.
    """
    
    def __init__(self):
        """Initialize the instrument filter service."""
        self.stats = {
            "filtered_queries": 0,
            "charts_filtered": 0,
            "audio_filtered": 0,
        }
    
    async def get_content_for_user(
        self,
        user_id: int,
        session: AsyncSession,
        content_type: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """
        Get all content accessible by a user based on their instruments.
        
        Args:
            user_id: The user ID.
            session: Database session.
            content_type: Optional filter for content type ('chart' or 'audio').
            
        Returns:
            Dict with 'charts' and 'audio' lists.
        """
        # TODO: Re-enable when auth module is available
        # try:
        #     # Get user with instruments
        #     user_stmt = select(User).where(User.id == user_id)
        #     result = await session.execute(user_stmt)
        #     user = result.scalar_one_or_none()
        #     
        #     if not user:
        #         logger.warning(f"User {user_id} not found")
        #         return {"charts": [], "audio": []}
        #     
        #     # Get user's instrument keys
        #     user_keys = get_keys_for_instruments(user.instruments or [])
        #     
        #     content = {"charts": [], "audio": []}
        #     
        #     # Get charts if requested
        #     if content_type is None or content_type == "chart":
        #         charts = await self._get_filtered_charts(
        #             session, user.band_id, user_keys
        #         )
        #         content["charts"] = charts
        #         self.stats["charts_filtered"] += len(charts)
        #     
        #     # Get audio if requested
        #     if content_type is None or content_type == "audio":
        #         audio_files = await self._get_audio_files(
        #             session, user.band_id
        #         )
        #         content["audio"] = audio_files
        #         self.stats["audio_filtered"] += len(audio_files)
        #     
        #     self.stats["filtered_queries"] += 1
        #     logger.info(f"Filtered content for user {user_id}: "
        #                f"{len(content['charts'])} charts, "
        #                f"{len(content['audio'])} audio files")
        #     
        #     return content
        #     
        # except Exception as e:
        #     logger.error(f"Error filtering content for user {user_id}: {e}")
        #     raise
        
        # Temporary implementation
        logger.warning(f"get_content_for_user temporarily disabled - auth module not available")
        return {"charts": [], "audio": []}
    
    async def _get_filtered_charts(
        self,
        session: AsyncSession,
        band_id: int,
        user_keys: List[str]
    ) -> List[Any]:
        """
        Get charts filtered by user's instrument keys.
        
        Args:
            session: Database session.
            band_id: The band ID.
            user_keys: List of keys the user can read.
            
        Returns:
            List of accessible charts.
        """
        # TODO: Re-enable when auth and models are available
        # Build query for charts
        # stmt = select(Chart).where(
        #     Chart.band_id == band_id,
        #     Chart.is_active == True
        # )
        
        # result = await session.execute(stmt)
        # all_charts = result.scalars().all()
        
        # Filter charts by key
        # accessible_charts = []
        # for chart in all_charts:
        #     if chart.key in user_keys or chart.key == "C":
        #         accessible_charts.append(chart)
        #     elif chart.is_placeholder:
        #         # Include placeholders for all instruments
        #         accessible_charts.append(chart)
        
        # return accessible_charts
        return []  # Temporary
    
    async def _get_audio_files(
        self,
        session: AsyncSession,
        band_id: int
    ) -> List[Any]:
        """
        Get all audio files for a band.
        
        Audio files are accessible to all band members regardless of instrument.
        
        Args:
            session: Database session.
            band_id: The band ID.
            
        Returns:
            List of audio files.
        """
        # TODO: Re-enable when auth and models are available
        # stmt = select(Audio).where(
        #     Audio.band_id == band_id,
        #     Audio.is_active == True
        # )
        # 
        # result = await session.execute(stmt)
        # return result.scalars().all()
        return []  # Temporary
    
    def filter_charts_by_instruments(
        self,
        charts: List[Dict[str, Any]],
        instruments: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of chart dictionaries by instruments.
        
        This is a utility method for filtering chart data without database access.
        
        Args:
            charts: List of chart dictionaries with 'key' field.
            instruments: List of user instruments.
            
        Returns:
            Filtered list of charts.
        """
        user_keys = get_keys_for_instruments(instruments)
        
        filtered_charts = []
        for chart in charts:
            chart_key = chart.get("key")
            if chart_key in user_keys or chart_key == "C":
                filtered_charts.append(chart)
            elif chart.get("is_placeholder", False):
                filtered_charts.append(chart)
        
        return filtered_charts
    
    def group_content_by_song(
        self,
        charts: List[Dict[str, Any]],
        audio_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group charts and audio files by song.
        
        Args:
            charts: List of chart dictionaries.
            audio_files: List of audio file dictionaries.
            
        Returns:
            List of song dictionaries with grouped content.
        """
        songs = {}
        
        # Group charts by song title
        for chart in charts:
            title = chart.get("song_title", "Unknown")
            if title not in songs:
                songs[title] = {
                    "song_title": title,
                    "charts": [],
                    "audio": []
                }
            songs[title]["charts"].append(chart)
        
        # Add audio files to songs
        for audio in audio_files:
            title = audio.get("song_title", "Unknown")
            if title not in songs:
                songs[title] = {
                    "song_title": title,
                    "charts": [],
                    "audio": []
                }
            songs[title]["audio"].append(audio)
        
        # Convert to list and sort by title
        song_list = list(songs.values())
        song_list.sort(key=lambda x: x["song_title"])
        
        return song_list
    
    def get_stats(self) -> Dict[str, int]:
        """Get filtering statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset filtering statistics."""
        self.stats = {
            "filtered_queries": 0,
            "charts_filtered": 0,
            "audio_filtered": 0,
        }