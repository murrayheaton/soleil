"""
Tests for instrument filter service.

Tests content filtering based on user instruments and key mappings.
"""
import pytest

from modules.content.services.instrument_filter import InstrumentFilter


class TestInstrumentFilter:
    """Test InstrumentFilter functionality."""
    
    @pytest.fixture
    def filter_service(self):
        """Create an InstrumentFilter instance."""
        return InstrumentFilter()
    
    def test_filter_charts_by_instruments_basic(self, filter_service):
        """Test basic chart filtering by instruments."""
        charts = [
            {"id": 1, "song_title": "All of Me", "key": "Bb"},
            {"id": 2, "song_title": "Blue Bossa", "key": "Eb"},
            {"id": 3, "song_title": "Autumn Leaves", "key": "C"},
        ]
        
        # Trumpet player (Bb)
        filtered = filter_service.filter_charts_by_instruments(charts, ["trumpet"])
        assert len(filtered) == 2  # Bb and C charts
        assert any(c["key"] == "Bb" for c in filtered)
        assert any(c["key"] == "C" for c in filtered)
        assert not any(c["key"] == "Eb" for c in filtered)
    
    def test_filter_charts_multiple_instruments(self, filter_service):
        """Test filtering with multiple instruments."""
        charts = [
            {"id": 1, "song_title": "All of Me", "key": "Bb"},
            {"id": 2, "song_title": "Blue Bossa", "key": "Eb"},
            {"id": 3, "song_title": "Autumn Leaves", "key": "C"},
            {"id": 4, "song_title": "Misty", "key": "F"},
        ]
        
        # Trumpet (Bb) and Alto Sax (Eb) player
        filtered = filter_service.filter_charts_by_instruments(
            charts, ["trumpet", "alto_sax"]
        )
        assert len(filtered) == 3  # Bb, Eb, and C charts
        assert not any(c["key"] == "F" for c in filtered)
    
    def test_filter_charts_with_placeholders(self, filter_service):
        """Test that placeholders are always included."""
        charts = [
            {"id": 1, "song_title": "All of Me", "key": "Bb"},
            {"id": 2, "song_title": "Placeholder Song", "key": None, "is_placeholder": True},
            {"id": 3, "song_title": "Blue Bossa", "key": "Eb"},
        ]
        
        # Alto sax player (Eb) - should get Eb, C, and placeholders
        filtered = filter_service.filter_charts_by_instruments(charts, ["alto_sax"])
        assert len(filtered) == 2  # Eb chart and placeholder
        assert any(c["is_placeholder"] for c in filtered)
    
    def test_filter_charts_concert_pitch_instrument(self, filter_service):
        """Test filtering for concert pitch instruments."""
        charts = [
            {"id": 1, "song_title": "All of Me", "key": "Bb"},
            {"id": 2, "song_title": "Blue Bossa", "key": "Eb"},
            {"id": 3, "song_title": "Autumn Leaves", "key": "C"},
        ]
        
        # Piano player (C) - only gets C charts
        filtered = filter_service.filter_charts_by_instruments(charts, ["piano"])
        assert len(filtered) == 1
        assert filtered[0]["key"] == "C"
    
    def test_filter_charts_empty_instruments(self, filter_service):
        """Test filtering with no instruments."""
        charts = [
            {"id": 1, "song_title": "All of Me", "key": "Bb"},
            {"id": 2, "song_title": "Autumn Leaves", "key": "C"},
        ]
        
        filtered = filter_service.filter_charts_by_instruments(charts, [])
        # Empty instruments get concert pitch ("C") by default
        assert len(filtered) == 1
        assert filtered[0]["key"] == "C"
    
    def test_group_content_by_song(self, filter_service):
        """Test grouping charts and audio by song."""
        charts = [
            {"id": 1, "song_title": "All of Me", "key": "Bb"},
            {"id": 2, "song_title": "All of Me", "key": "Eb"},
            {"id": 3, "song_title": "Blue Bossa", "key": "C"},
        ]
        
        audio_files = [
            {"id": 4, "song_title": "All of Me", "type": "reference"},
            {"id": 5, "song_title": "Blue Bossa", "type": "backing"},
            {"id": 6, "song_title": "Autumn Leaves", "type": "reference"},
        ]
        
        grouped = filter_service.group_content_by_song(charts, audio_files)
        
        # Should have 3 songs
        assert len(grouped) == 3
        
        # Check "All of Me" has both charts and audio
        all_of_me = next(s for s in grouped if s["song_title"] == "All of Me")
        assert len(all_of_me["charts"]) == 2
        assert len(all_of_me["audio"]) == 1
        
        # Check "Blue Bossa" has both
        blue_bossa = next(s for s in grouped if s["song_title"] == "Blue Bossa")
        assert len(blue_bossa["charts"]) == 1
        assert len(blue_bossa["audio"]) == 1
        
        # Check "Autumn Leaves" has only audio
        autumn = next(s for s in grouped if s["song_title"] == "Autumn Leaves")
        assert len(autumn["charts"]) == 0
        assert len(autumn["audio"]) == 1
    
    def test_group_content_sorted(self, filter_service):
        """Test that grouped content is sorted by title."""
        charts = [
            {"song_title": "Zebra Song"},
            {"song_title": "All of Me"},
            {"song_title": "Blue Bossa"},
        ]
        
        grouped = filter_service.group_content_by_song(charts, [])
        titles = [s["song_title"] for s in grouped]
        
        assert titles == ["All of Me", "Blue Bossa", "Zebra Song"]
    
    def test_stats_tracking(self, filter_service):
        """Test statistics tracking."""
        initial_stats = filter_service.get_stats()
        assert initial_stats["filtered_queries"] == 0
        assert initial_stats["charts_filtered"] == 0
        assert initial_stats["audio_filtered"] == 0
        
        # Perform some filtering
        charts = [{"key": "Bb"}, {"key": "C"}]
        filter_service.filter_charts_by_instruments(charts, ["trumpet"])
        
        # Stats should not be updated by the utility method
        stats = filter_service.get_stats()
        assert stats["filtered_queries"] == 0  # Only updated by async methods
    
    def test_stats_reset(self, filter_service):
        """Test resetting statistics."""
        # Set some stats
        filter_service.stats["filtered_queries"] = 10
        filter_service.stats["charts_filtered"] = 20
        
        # Reset
        filter_service.reset_stats()
        stats = filter_service.get_stats()
        
        assert stats["filtered_queries"] == 0
        assert stats["charts_filtered"] == 0
        assert stats["audio_filtered"] == 0