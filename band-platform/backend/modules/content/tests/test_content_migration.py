"""
Test content module migration to ensure everything is working correctly.
"""


def test_content_module_imports():
    """Test that all content module components can be imported."""
    # Test service imports
    from modules.content.services import ContentParser, FolderOrganizer, InstrumentFilter
    
    # Test model imports
    from modules.content.models import (
        Chart
    )
    
    # Test API imports
    from modules.content.api import router
    
    # Test utility imports  
    
    # Verify imports are not None
    assert ContentParser is not None
    assert FolderOrganizer is not None
    assert InstrumentFilter is not None
    assert Chart is not None
    assert router is not None


def test_content_parser_functionality():
    """Test basic content parser functionality."""
    from modules.content.services import ContentParser
    
    parser = ContentParser()
    
    # Test parsing a standard chart filename
    result = parser.parse_filename("All of Me - Bb.pdf")
    assert result.song_title == "All of Me"
    assert result.key == "Bb"
    assert result.file_type.value == "chart"
    assert result.extension == ".pdf"
    
    # Test parsing an audio filename
    result = parser.parse_filename("Blue Moon.mp3")
    assert result.song_title == "Blue Moon"
    assert result.file_type.value == "audio"
    assert result.extension == ".mp3"


def test_instrument_key_mapping():
    """Test instrument to key mapping functionality."""
    from modules.content.services import get_keys_for_instruments
    
    # Test B♭ instruments
    keys = get_keys_for_instruments(["trumpet", "tenor_sax"])
    assert keys == ["Bb"]
    
    # Test E♭ instruments
    keys = get_keys_for_instruments(["alto_sax", "bari_sax"])
    assert keys == ["Eb"]
    
    # Test concert pitch instruments
    keys = get_keys_for_instruments(["piano", "guitar", "bass"])
    assert keys == ["C"]
    
    # Test mixed instruments
    keys = get_keys_for_instruments(["trumpet", "alto_sax", "piano"])
    assert set(keys) == {"Bb", "C", "Eb"}


def test_file_type_detection():
    """Test file type detection utility."""
    from modules.content.utils import get_file_type, is_chart_file, is_audio_file
    
    # Test chart files
    assert get_file_type("song.pdf") == "chart"
    assert is_chart_file("song.pdf") is True
    assert is_audio_file("song.pdf") is False
    
    # Test audio files
    assert get_file_type("song.mp3") == "audio"
    assert is_audio_file("song.mp3") is True
    assert is_chart_file("song.mp3") is False
    
    # Test other files
    assert get_file_type("readme.txt") == "document"
    assert get_file_type("unknown.xyz") == "other"


def test_naming_utilities():
    """Test naming convention utilities."""
    from modules.content.utils import format_song_title, clean_filename
    
    # Test song title formatting
    assert format_song_title("dont stop believin") == "Don't Stop Believin"
    assert format_song_title("fly me to the moon") == "Fly Me to the Moon"
    
    # Test filename cleaning
    assert clean_filename("Song: Title / Test?.pdf") == "Song Title  Test.pdf"
    assert clean_filename("   spaces   .pdf   ") == "spaces   .pdf"


def test_compatibility_imports():
    """Test that old import paths still work with deprecation warnings."""
    import warnings
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Import from old location
        from app.services.content_parser import ContentParser
        
        # Should have deprecation warning
        assert len(w) >= 1
        assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
        assert any("deprecated" in str(warning.message).lower() for warning in w)
        
        # Check that we can use the imported class
        parser = ContentParser()
        assert parser is not None