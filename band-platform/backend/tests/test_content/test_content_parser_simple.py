"""
Simple tests for content parser service that match actual implementation.
"""
import pytest
from modules.content.services.content_parser import (
    ContentParser, 
    parse_filename,
    get_keys_for_instruments,
    is_chart_accessible_by_user
)


class TestContentParserBasic:
    """Basic tests for ContentParser."""
    
    def test_parse_filename_basic(self):
        """Test basic filename parsing."""
        parser = ContentParser()
        result = parser.parse_filename("All of Me - Bb.pdf")
        
        assert result.song_title == "All of Me"
        assert result.key == "Bb"
        assert result.file_type == "chart"
    
    def test_parse_filename_audio(self):
        """Test audio file parsing."""
        parser = ContentParser()
        result = parser.parse_filename("Test Song.mp3")
        
        assert result.song_title == "Test Song"
        assert result.key is None
        assert result.file_type == "audio"
    
    def test_get_keys_for_instruments(self):
        """Test instrument key mapping."""
        # Single instrument
        assert get_keys_for_instruments(["trumpet"]) == ["Bb"]
        assert get_keys_for_instruments(["alto_sax"]) == ["Eb"]
        assert get_keys_for_instruments(["piano"]) == ["C"]
        
        # Multiple instruments
        keys = get_keys_for_instruments(["trumpet", "alto_sax"])
        assert set(keys) == {"Bb", "Eb"}
        
        # Empty list returns concert pitch
        assert get_keys_for_instruments([]) == ["C"]
    
    def test_is_chart_accessible_by_user(self):
        """Test chart accessibility."""
        # Matching key
        assert is_chart_accessible_by_user("Bb", ["trumpet"]) == True
        assert is_chart_accessible_by_user("Eb", ["alto_sax"]) == True
        
        # Non-matching key
        assert is_chart_accessible_by_user("Eb", ["trumpet"]) == False
        
        # Concert key charts need to be handled by instrument_filter
        # The base function only checks if key matches user's instruments
        assert is_chart_accessible_by_user("C", ["piano"]) == True
        assert is_chart_accessible_by_user("C", ["trumpet"]) == False
    
    def test_parser_stats(self):
        """Test statistics tracking."""
        parser = ContentParser()
        
        # Initial stats
        stats = parser.get_stats()
        assert stats["parsed"] == 0
        assert stats["failed"] == 0
        assert stats["by_type"]["chart"] == 0
        
        # Parse a file
        parser.parse_filename("Test.pdf")
        stats = parser.get_stats()
        assert stats["parsed"] == 1
        assert stats["by_type"]["chart"] == 1
        
        # Reset stats
        parser.reset_stats()
        stats = parser.get_stats()
        assert stats["parsed"] == 0