"""
Tests for content parser service.

Tests filename parsing, instrument key mapping, and content accessibility checks.
"""
import pytest
from typing import List, Dict, Any

from modules.content.services.content_parser import (
    ContentParser, 
    parse_filename,
    get_keys_for_instruments,
    is_chart_accessible_by_user,
    INSTRUMENT_KEY_MAPPING
)


class TestContentParser:
    """Test ContentParser class functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create a ContentParser instance."""
        return ContentParser()
    
    def test_parse_filename_standard_format(self, parser):
        """Test parsing standard filename format."""
        result = parser.parse_filename("All of Me - Bb.pdf")
        assert result.song_title == "All of Me"
        assert result.key == "Bb"
        assert result.file_type == "chart"
        assert result.is_placeholder == False
    
    def test_parse_filename_with_extra_info(self, parser):
        """Test parsing filename with additional info."""
        result = parser.parse_filename("Fly Me to the Moon - Eb - Vocals.pdf")
        assert result.song_title == "Fly Me to the Moon"
        assert result.key == "Eb"
        assert result.extra_info == "Vocals"
    
    def test_parse_filename_placeholder(self, parser):
        """Test parsing placeholder filename."""
        result = parser.parse_filename("Placeholder - Song Title.pdf")
        assert result.song_title == "Song Title"
        assert result.key == None
        assert result.is_placeholder == True
    
    def test_parse_filename_audio_file(self, parser):
        """Test parsing audio filename."""
        result = parser.parse_filename("All of Me - Reference.mp3")
        assert result.song_title == "All of Me"
        assert result.key == None
        assert result.file_type == "audio"
        assert result.extra_info == "Reference"
    
    def test_parse_filename_edge_cases(self, parser):
        """Test parsing edge case filenames."""
        # No extension
        result = parser.parse_filename("Test Song")
        assert result.song_title == "Test Song"
        assert result.file_type == "unknown"
        
        # Multiple dashes
        result = parser.parse_filename("Mary Had a Little Lamb - Bb - Easy Version.pdf")
        assert result.song_title == "Mary Had a Little Lamb"
        assert result.key == "Bb"
        assert result.extra_info == "Easy Version"
        
        # Concert key
        result = parser.parse_filename("Blue Bossa - C.pdf")
        assert result.song_title == "Blue Bossa"
        assert result.key == "C"
    
    def test_get_parsed_info_dict(self, parser):
        """Test getting parsed info as dictionary."""
        parsed = parser.parse_filename("All of Me - Bb.pdf")
        info = parser.get_parsed_info_dict(parsed)
        
        assert info["song_title"] == "All of Me"
        assert info["key"] == "Bb"
        assert info["file_type"] == "chart"
        assert info["is_placeholder"] == False
        assert info["extra_info"] is None


class TestInstrumentKeyMapping:
    """Test instrument key mapping functionality."""
    
    def test_get_keys_for_single_instrument(self):
        """Test getting key for single instrument."""
        assert get_keys_for_instruments(["trumpet"]) == ["Bb"]
        assert get_keys_for_instruments(["alto_sax"]) == ["Eb"]
        assert get_keys_for_instruments(["piano"]) == ["C"]
    
    def test_get_keys_for_multiple_instruments(self):
        """Test getting keys for multiple instruments."""
        keys = get_keys_for_instruments(["trumpet", "alto_sax", "piano"])
        assert set(keys) == {"Bb", "Eb", "C"}
        assert len(keys) == 3
    
    def test_get_keys_with_duplicates(self):
        """Test getting keys with duplicate instrument types."""
        keys = get_keys_for_instruments(["trumpet", "tenor_sax", "clarinet"])
        assert keys == ["Bb"]  # All Bb instruments
    
    def test_get_keys_unknown_instrument(self):
        """Test getting keys for unknown instrument."""
        keys = get_keys_for_instruments(["unknown_instrument"])
        assert keys == ["C"]  # Default to concert pitch
    
    def test_get_keys_empty_list(self):
        """Test getting keys for empty instrument list."""
        keys = get_keys_for_instruments([])
        assert keys == []
    
    def test_all_mapped_instruments(self):
        """Test that all instruments in mapping are valid."""
        for instrument, key in INSTRUMENT_KEY_MAPPING.items():
            assert key in ["Bb", "Eb", "C", "F"]
            keys = get_keys_for_instruments([instrument])
            assert keys == [key]


class TestChartAccessibility:
    """Test chart accessibility checks."""
    
    def test_chart_accessible_by_matching_key(self):
        """Test chart is accessible when user has matching key."""
        chart = {"key": "Bb", "is_placeholder": False}
        assert is_chart_accessible_by_user(chart, ["trumpet"]) == True
        assert is_chart_accessible_by_user(chart, ["alto_sax"]) == False
    
    def test_chart_accessible_concert_key(self):
        """Test concert key charts are accessible to all."""
        chart = {"key": "C", "is_placeholder": False}
        assert is_chart_accessible_by_user(chart, ["trumpet"]) == True
        assert is_chart_accessible_by_user(chart, ["alto_sax"]) == True
        assert is_chart_accessible_by_user(chart, ["piano"]) == True
    
    def test_placeholder_accessible_to_all(self):
        """Test placeholder charts are accessible to all."""
        chart = {"key": None, "is_placeholder": True}
        assert is_chart_accessible_by_user(chart, ["trumpet"]) == True
        assert is_chart_accessible_by_user(chart, ["alto_sax"]) == True
        assert is_chart_accessible_by_user(chart, []) == True
    
    def test_chart_accessible_multiple_instruments(self):
        """Test accessibility with multiple instruments."""
        chart = {"key": "Eb", "is_placeholder": False}
        assert is_chart_accessible_by_user(chart, ["trumpet", "alto_sax"]) == True
        assert is_chart_accessible_by_user(chart, ["trumpet", "tenor_sax"]) == False
    
    def test_chart_missing_key_field(self):
        """Test chart without key field."""
        chart = {"is_placeholder": False}
        assert is_chart_accessible_by_user(chart, ["trumpet"]) == False
    
    def test_chart_missing_placeholder_field(self):
        """Test chart without is_placeholder field."""
        chart = {"key": "Bb"}
        assert is_chart_accessible_by_user(chart, ["trumpet"]) == True
        assert is_chart_accessible_by_user(chart, ["alto_sax"]) == False


class TestContentParserStats:
    """Test ContentParser statistics tracking."""
    
    def test_stats_initialization(self):
        """Test stats are initialized correctly."""
        parser = ContentParser()
        stats = parser.get_stats()
        assert stats["files_parsed"] == 0
        assert stats["charts_found"] == 0
        assert stats["audio_found"] == 0
        assert stats["placeholders_found"] == 0
    
    def test_stats_tracking(self):
        """Test stats are tracked correctly."""
        parser = ContentParser()
        
        # Parse various file types
        parser.parse_filename("Song1 - Bb.pdf")
        parser.parse_filename("Song2 - Eb.pdf")
        parser.parse_filename("Song3.mp3")
        parser.parse_filename("Placeholder - Song4.pdf")
        
        stats = parser.get_stats()
        assert stats["files_parsed"] == 4
        assert stats["charts_found"] == 3
        assert stats["audio_found"] == 1
        assert stats["placeholders_found"] == 1
    
    def test_stats_reset(self):
        """Test resetting statistics."""
        parser = ContentParser()
        
        # Parse some files
        parser.parse_filename("Test.pdf")
        assert parser.get_stats()["files_parsed"] == 1
        
        # Reset stats
        parser.reset_stats()
        stats = parser.get_stats()
        assert stats["files_parsed"] == 0
        assert stats["charts_found"] == 0