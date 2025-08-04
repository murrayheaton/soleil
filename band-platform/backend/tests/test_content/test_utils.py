"""
Tests for content module utilities.

Tests file type detection, naming conventions, and metadata extraction.
"""
import pytest
from datetime import datetime

from modules.content.utils.file_types import (
    get_file_type, is_chart_file, is_audio_file,
    CHART_EXTENSIONS, AUDIO_EXTENSIONS
)
from modules.content.utils.naming import (
    format_song_title, clean_filename, generate_filename
)
from modules.content.utils.metadata import (
    extract_file_metadata, format_file_size, 
    estimate_duration_from_size
)


class TestFileTypes:
    """Test file type detection utilities."""
    
    def test_get_file_type_charts(self):
        """Test detecting chart file types."""
        assert get_file_type("song.pdf") == "chart"
        assert get_file_type("song.PDF") == "chart"
        assert get_file_type("path/to/song.pdf") == "chart"
    
    def test_get_file_type_audio(self):
        """Test detecting audio file types."""
        assert get_file_type("song.mp3") == "audio"
        assert get_file_type("song.MP3") == "audio"
        assert get_file_type("song.wav") == "audio"
        assert get_file_type("song.m4a") == "audio"
    
    def test_get_file_type_unknown(self):
        """Test unknown file types."""
        assert get_file_type("file.json") == "other"
        assert get_file_type("file.xml") == "other"
        assert get_file_type("file") == "other"
        assert get_file_type("") == "other"
    
    def test_is_chart_file(self):
        """Test chart file detection."""
        assert is_chart_file("song.pdf") == True
        assert is_chart_file("song.mp3") == False
        assert is_chart_file("song.txt") == False
    
    def test_is_audio_file(self):
        """Test audio file detection."""
        assert is_audio_file("song.mp3") == True
        assert is_audio_file("song.wav") == True
        assert is_audio_file("song.pdf") == False
    
    def test_all_extensions_covered(self):
        """Test that all defined extensions are recognized."""
        for ext in CHART_EXTENSIONS:
            assert get_file_type(f"file{ext}") == "chart"
        
        for ext in AUDIO_EXTENSIONS:
            assert get_file_type(f"file{ext}") == "audio"


class TestNaming:
    """Test naming convention utilities."""
    
    def test_format_song_title_basic(self):
        """Test basic song title formatting."""
        assert format_song_title("all of me") == "All of Me"
        assert format_song_title("FLY ME TO THE MOON") == "Fly Me to the Moon"
        assert format_song_title("blue bossa") == "Blue Bossa"
    
    def test_format_song_title_special_words(self):
        """Test formatting with special words."""
        assert format_song_title("dont stop believin") == "Don't Stop Believin"
        assert format_song_title("ive got rhythm") == "I've Got Rhythm"
        assert format_song_title("cant help myself") == "Can't Help Myself"
    
    def test_format_song_title_edge_cases(self):
        """Test edge cases in title formatting."""
        assert format_song_title("") == ""
        assert format_song_title("a") == "A"
        assert format_song_title("the way you look tonight") == "The Way You Look Tonight"
    
    def test_clean_filename(self):
        """Test filename cleaning."""
        assert clean_filename("Song:Title") == "SongTitle"
        assert clean_filename("Song/Title") == "SongTitle"
        assert clean_filename("Song?Title") == "SongTitle"
        assert clean_filename("Song  Title") == "Song Title"
        assert clean_filename("...Song...") == "Song"
    
    def test_generate_filename(self):
        """Test filename generation."""
        assert generate_filename("All of Me", "Bb") == "All of Me - Bb.pdf"
        assert generate_filename("Blue Bossa", "Eb", "Lead Sheet") == "Blue Bossa - Lead Sheet - Eb.pdf"
        assert generate_filename("Test Song") == "Test Song.pdf"
        assert generate_filename("Test", extension=".mp3") == "Test.mp3"


class TestMetadata:
    """Test metadata extraction utilities."""
    
    def test_extract_file_metadata(self):
        """Test extracting metadata from file info."""
        file_info = {
            "name": "All of Me - Bb.pdf",
            "size": 1024 * 1024,  # 1MB
            "modifiedTime": "2024-01-15T10:30:00.000Z",
            "mimeType": "application/pdf"
        }
        
        metadata = extract_file_metadata(file_info)
        assert metadata["filename"] == "All of Me - Bb.pdf"
        assert metadata["size_bytes"] == 1024 * 1024
        assert metadata["size_formatted"] == "1.00 MB"
        assert metadata["mime_type"] == "application/pdf"
        assert isinstance(metadata["modified_time"], datetime)
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(500) == "500.00 B"
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 5.5) == "5.50 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_file_size(0) == "0.00 B"
    
    def test_estimate_duration_from_size(self):
        """Test estimating audio duration from file size."""
        # MP3 at ~128kbps
        mp3_size = 128 * 1024 / 8 * 60  # 1 minute
        duration = estimate_duration_from_size(mp3_size, "audio/mpeg")
        assert 55 <= duration <= 65  # Allow some variance
        
        # WAV is much larger
        wav_size = mp3_size * 10
        duration = estimate_duration_from_size(wav_size, "audio/wav")
        assert 55 <= duration <= 65  # Still ~1 minute
        
        # Unknown format returns None
        assert estimate_duration_from_size(1024, "application/pdf") is None
    
    def test_extract_metadata_missing_fields(self):
        """Test metadata extraction with missing fields."""
        file_info = {"name": "test.pdf"}
        metadata = extract_file_metadata(file_info)
        
        assert metadata["filename"] == "test.pdf"
        assert metadata["size_bytes"] == 0
        assert metadata["size_formatted"] == "0.00 B"
        assert metadata["mime_type"] == "unknown"
        assert metadata["modified_time"] is None