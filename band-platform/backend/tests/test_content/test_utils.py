"""
Tests for content module utilities.

Tests file type detection, naming conventions, and metadata extraction.
"""

from modules.content.utils.file_types import (
    get_file_type, is_chart_file, is_audio_file,
    CHART_EXTENSIONS, AUDIO_EXTENSIONS
)
from modules.content.utils.naming import (
    format_song_title, clean_filename, generate_filename
)
from modules.content.utils.metadata import (
    format_file_size, 
    get_file_info
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
        assert is_chart_file("song.pdf")
        assert not is_chart_file("song.mp3")
        assert not is_chart_file("song.txt")
    
    def test_is_audio_file(self):
        """Test audio file detection."""
        assert is_audio_file("song.mp3")
        assert is_audio_file("song.wav")
        assert not is_audio_file("song.pdf")
    
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
    
    def test_get_file_info(self):
        """Test getting file information."""
        info = get_file_info("All of Me - Bb.pdf", file_id="12345", size=1024*1024)
        
        assert info["filename"] == "All of Me - Bb.pdf"
        assert info["file_id"] == "12345"
        assert info["file_type"] == "chart"
        assert info["title"] == "All of Me"
        assert info["key"] == "Bb"
        assert info["extension"] == ".pdf"
        assert info["size"] == 1024 * 1024
        assert info["size_human"] == "1.0 MB"
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 5.5) == "5.5 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(0) == "0.0 B"
        assert format_file_size(None) == "Unknown"
    
    def test_get_file_info_minimal(self):
        """Test file info with minimal data."""
        info = get_file_info("test.mp3")
        
        assert info["filename"] == "test.mp3"
        assert info["file_id"] is None
        assert info["file_type"] == "audio"
        assert info["title"] == "test"
        assert info["key"] is None
        assert info["extension"] == ".mp3"
        assert info["size"] is None
        assert info["size_human"] is None