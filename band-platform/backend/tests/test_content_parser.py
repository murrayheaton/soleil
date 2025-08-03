"""
Unit tests for the content parser service.

This module tests the file naming convention parsing and instrument-key mapping logic
following the PRP requirements with comprehensive test coverage.
"""

import pytest
from app.services.content_parser import (
    ContentParser, 
    parse_filename,
    get_keys_for_instruments,
    get_instruments_for_key,
    is_chart_accessible_by_user,
    suggest_key_for_instruments,
    FileType,
    INSTRUMENT_KEY_MAPPING
)


class TestContentParser:
    """Test cases for the ContentParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ContentParser()
    
    def test_parse_standard_format(self):
        """Test parsing standard format: 'Song Title - Key.ext'"""
        result = parse_filename("All of Me - Bb.pdf")
        
        assert result.song_title == "All of Me"
        assert result.key == "Bb"
        assert result.file_type == FileType.CHART
        assert result.extension == ".pdf"
        assert result.composer is None
        assert result.arranger is None
    
    def test_parse_with_composer(self):
        """Test parsing with composer: 'Song Title - Composer - Key.ext'"""
        result = parse_filename("Spain - Chick Corea - Eb.pdf")
        
        assert result.song_title == "Spain"
        assert result.composer == "Chick Corea"
        assert result.key == "Eb"
        assert result.file_type == FileType.CHART
    
    def test_parse_reference_audio(self):
        """Test parsing reference audio: 'Song Title - Reference.ext'"""
        result = parse_filename("All of Me - Reference.mp3")
        
        assert result.song_title == "All of Me"
        assert result.key is None
        assert result.file_type == FileType.AUDIO
        assert result.extension == ".mp3"
        assert "reference" in result.metadata.get("type", "").lower()
    
    def test_parse_with_chart_type(self):
        """Test parsing with chart type: 'Song Title - Type - Key.ext'"""
        result = parse_filename("Summertime - Rhythm - C.pdf")
        
        assert result.song_title == "Summertime"
        assert result.chart_type == "rhythm"
        assert result.key == "C"
        assert result.file_type == FileType.CHART
    
    def test_parse_with_tempo(self):
        """Test parsing with tempo: 'Song Title - Key - Tempo.ext'"""
        result = parse_filename("Take Five - Eb - Medium Swing.pdf")
        
        assert result.song_title == "Take Five"
        assert result.key == "Eb"
        assert result.tempo == "Medium Swing"
        assert result.file_type == FileType.CHART
    
    def test_parse_complex_filename(self):
        """Test parsing complex filename with multiple hyphens."""
        result = parse_filename("All of Me - Jazz Standard - Duke Ellington - Bb.pdf")
        
        # Should handle multiple hyphens gracefully
        assert result.song_title is not None
        assert result.key == "Bb"
        assert result.file_type == FileType.CHART
    
    def test_parse_fallback_no_pattern(self):
        """Test fallback when no pattern matches."""
        result = parse_filename("SomeRandomFile.txt")
        
        assert result.song_title == "SomeRandomFile"
        assert result.key is None
        assert result.file_type == FileType.OTHER
        assert result.extension == ".txt"
    
    def test_parse_audio_file_types(self):
        """Test detection of audio file types."""
        audio_files = [
            "Song - Reference.mp3",
            "Song - Demo.wav", 
            "Song - Backing.m4a",
            "Song - Reference.aac"
        ]
        
        for filename in audio_files:
            result = parse_filename(filename)
            assert result.file_type == FileType.AUDIO
    
    def test_parse_chart_file_types(self):
        """Test detection of chart file types."""
        chart_files = [
            "Song - Bb.pdf",
            "Song - C.png",
            "Song - Eb.jpg"
        ]
        
        for filename in chart_files:
            result = parse_filename(filename)
            assert result.file_type == FileType.CHART
    
    def test_key_validation(self):
        """Test musical key validation."""
        valid_keys = ["C", "Bb", "F#", "Ebm", "C#m"]
        invalid_keys = ["H", "Zb", "X#m", "Cb"]
        
        for key in valid_keys:
            result = parse_filename(f"Song - {key}.pdf")
            assert result.key == key
        
        for key in invalid_keys:
            result = parse_filename(f"Song - {key}.pdf")
            assert result.key is None  # Invalid keys should be None
    
    def test_title_cleaning(self):
        """Test song title cleaning and normalization."""
        test_cases = [
            ("  All of Me  ", "All of Me"),
            ("Song   With   Spaces", "Song With Spaces"),
            ("- Song Title -", "Song Title"),
            ("", "Unknown Title")
        ]
        
        for input_title, expected in test_cases:
            # Create a filename that will extract the title
            result = parse_filename(f"{input_title} - C.pdf")
            assert result.song_title == expected
    
    def test_statistics_tracking(self):
        """Test that parser tracks statistics correctly."""
        parser = ContentParser()
        
        # Get fresh initial stats
        initial_parsed = parser.stats["parsed"]
        initial_chart = parser.stats["by_type"]["chart"]
        initial_audio = parser.stats["by_type"]["audio"]
        initial_other = parser.stats["by_type"]["other"]
        
        # Parse some files
        parser.parse_filename("Song1 - Bb.pdf")
        parser.parse_filename("Song2 - Reference.mp3") 
        parser.parse_filename("Random.txt")
        
        # Check final stats
        assert parser.stats["parsed"] == initial_parsed + 3
        assert parser.stats["by_type"]["chart"] == initial_chart + 1
        assert parser.stats["by_type"]["audio"] == initial_audio + 1
        assert parser.stats["by_type"]["other"] == initial_other + 1


class TestInstrumentKeyMapping:
    """Test cases for instrument-key mapping functionality."""
    
    def test_get_keys_for_instruments(self):
        """Test getting keys for list of instruments."""
        # Single instrument
        assert get_keys_for_instruments(["trumpet"]) == ["Bb"]
        assert get_keys_for_instruments(["piano"]) == ["C"]
        assert get_keys_for_instruments(["alto_saxophone"]) == ["Eb"]
        
        # Multiple instruments, same key
        assert get_keys_for_instruments(["trumpet", "tenor_sax"]) == ["Bb"]
        
        # Multiple instruments, different keys
        keys = get_keys_for_instruments(["trumpet", "piano"])
        assert set(keys) == {"Bb", "C"}
        assert keys == sorted(keys)  # Should be sorted
    
    def test_get_keys_for_empty_instruments(self):
        """Test getting keys for empty instrument list."""
        assert get_keys_for_instruments([]) == ["C"]  # Default to concert pitch
        assert get_keys_for_instruments(None) == ["C"]
    
    def test_get_keys_for_unknown_instruments(self):
        """Test getting keys for unknown instruments."""
        assert get_keys_for_instruments(["unknown_instrument"]) == ["C"]  # Default
        assert get_keys_for_instruments(["trumpet", "unknown"]) == ["Bb", "C"]
    
    def test_get_instruments_for_key(self):
        """Test getting instruments that use a specific key."""
        bb_instruments = get_instruments_for_key("Bb")
        assert "Trumpet" in bb_instruments
        assert "Tenor Sax" in bb_instruments
        
        c_instruments = get_instruments_for_key("C")
        assert "Piano" in c_instruments
        assert "Trombone" in c_instruments
        
        eb_instruments = get_instruments_for_key("Eb")
        assert "Alto Sax" in eb_instruments
        assert "Baritone Sax" in eb_instruments
    
    def test_get_instruments_for_invalid_key(self):
        """Test getting instruments for invalid key."""
        assert get_instruments_for_key("Invalid") == []
    
    def test_is_chart_accessible_by_user(self):
        """Test chart accessibility based on user instruments."""
        # Trumpet player should access Bb charts
        assert is_chart_accessible_by_user("Bb", ["trumpet"]) == True
        assert is_chart_accessible_by_user("C", ["trumpet"]) == False
        
        # Piano player should access C charts
        assert is_chart_accessible_by_user("C", ["piano"]) == True
        assert is_chart_accessible_by_user("Bb", ["piano"]) == False
        
        # Multi-instrument player
        assert is_chart_accessible_by_user("Bb", ["trumpet", "piano"]) == True
        assert is_chart_accessible_by_user("C", ["trumpet", "piano"]) == True
        assert is_chart_accessible_by_user("F", ["trumpet", "piano"]) == False
    
    def test_suggest_key_for_instruments(self):
        """Test key suggestion for instrument combinations."""
        # Single instrument
        assert suggest_key_for_instruments(["trumpet"]) == "Bb"
        assert suggest_key_for_instruments(["piano"]) == "C"
        
        # Multiple instruments with same key
        assert suggest_key_for_instruments(["trumpet", "tenor_sax"]) == "Bb"
        
        # Multiple instruments with different keys - should prefer C
        assert suggest_key_for_instruments(["trumpet", "piano"]) == "C"
        
        # No instruments
        assert suggest_key_for_instruments([]) == "C"
    
    def test_instrument_mapping_completeness(self):
        """Test that instrument mapping covers expected instruments."""
        # Check that common band instruments are included
        required_instruments = [
            "trumpet", "trombone", "alto_sax", "tenor_sax", "baritone_sax",
            "piano", "guitar", "bass", "drums", "voice"
        ]
        
        for instrument in required_instruments:
            assert instrument in INSTRUMENT_KEY_MAPPING, f"Missing instrument: {instrument}"
            assert INSTRUMENT_KEY_MAPPING[instrument] in ["C", "Bb", "Eb", "F"]


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_filename(self):
        """Test parsing empty filename."""
        result = parse_filename("")
        assert result.song_title == "Unknown Title"
        assert result.file_type == FileType.OTHER
    
    def test_filename_with_special_characters(self):
        """Test filenames with special characters."""
        result = parse_filename("Song's Title (Live) - Bb.pdf")
        assert result.song_title == "Song's Title (Live)"
        assert result.key == "Bb"
    
    def test_case_insensitive_key_parsing(self):
        """Test that key parsing is case insensitive."""
        test_cases = [
            ("Song - bb.pdf", "Bb"),
            ("Song - BB.pdf", "Bb"),
            ("Song - Bb.pdf", "Bb"),
            ("Song - ebm.pdf", "Ebm"),
            ("Song - EBM.pdf", "Ebm")
        ]
        
        for filename, expected_key in test_cases:
            result = parse_filename(filename)
            assert result.key == expected_key
    
    def test_unicode_filename(self):
        """Test parsing filenames with unicode characters."""
        result = parse_filename("Café París - Bb.pdf")
        assert result.song_title == "Café París"
        assert result.key == "Bb"
    
    def test_very_long_filename(self):
        """Test parsing very long filenames."""
        long_title = "A" * 200
        result = parse_filename(f"{long_title} - C.pdf")
        assert result.song_title == long_title
        assert result.key == "C"
    
    def test_filename_without_extension(self):
        """Test parsing filename without extension."""
        result = parse_filename("Song - Bb")
        assert result.song_title == "Song"
        assert result.key == "Bb"
        assert result.extension == ""
    
    def test_multiple_dots_in_filename(self):
        """Test filename with multiple dots."""
        result = parse_filename("Song.Title.Version.2 - Bb.pdf")
        assert result.song_title == "Song.Title.Version.2"
        assert result.key == "Bb"
        assert result.extension == ".pdf"


class TestValidationRequirements:
    """Test specific validation requirements from the PRP."""
    
    def test_instrument_key_mapping_requirements(self):
        """Test that instrument-key mapping meets PRP requirements."""
        # PRP specifies these mappings:
        assert INSTRUMENT_KEY_MAPPING["trumpet"] == "Bb"
        assert INSTRUMENT_KEY_MAPPING["alto_sax"] == "Eb"  
        assert INSTRUMENT_KEY_MAPPING["tenor_sax"] == "Bb"
        assert INSTRUMENT_KEY_MAPPING["baritone_sax"] == "Eb"
        assert INSTRUMENT_KEY_MAPPING["french_horn"] == "F"
        assert INSTRUMENT_KEY_MAPPING["trombone"] == "C"
        assert INSTRUMENT_KEY_MAPPING["piano"] == "C"
        assert INSTRUMENT_KEY_MAPPING["bass"] == "C"
        assert INSTRUMENT_KEY_MAPPING["guitar"] == "C"
    
    def test_file_naming_convention_requirements(self):
        """Test that parser handles PRP file naming conventions."""
        # PRP specifies: Charts: `[Song Title] - [Key].pdf`
        result = parse_filename("All of Me - Bb.pdf")
        assert result.song_title == "All of Me"
        assert result.key == "Bb"
        assert result.file_type == FileType.CHART
        
        # PRP specifies: Audio: `[Song Title] - Reference.mp3`
        result = parse_filename("All of Me - Reference.mp3")
        assert result.song_title == "All of Me"
        assert result.file_type == FileType.AUDIO
    
    def test_role_based_filtering_logic(self):
        """Test role-based filtering as specified in PRP."""
        # PRP requirement: trumpet players automatically get Bb charts
        trumpet_user = ["trumpet", "flugelhorn"]  # Both Bb instruments
        
        assert is_chart_accessible_by_user("Bb", trumpet_user) == True
        assert is_chart_accessible_by_user("Eb", trumpet_user) == False
        assert is_chart_accessible_by_user("C", trumpet_user) == False
        
        # Multi-instrument user should get multiple keys
        multi_user = ["trumpet", "piano"]  # Bb and C instruments
        assert is_chart_accessible_by_user("Bb", multi_user) == True
        assert is_chart_accessible_by_user("C", multi_user) == True
        assert is_chart_accessible_by_user("Eb", multi_user) == False
    
    def test_parsing_error_handling(self):
        """Test that parsing handles errors gracefully."""
        # Should not raise exceptions on any input
        problematic_files = [
            None,  # This would cause an error in real usage
            "",
            "---",
            "File with no pattern at all",
            "Multiple - Hyphens - In - Name - Without - Key.pdf",
            "Invalid/Path\\Characters - Bb.pdf"
        ]
        
        for filename in problematic_files:
            if filename is not None:  # Skip None test
                try:
                    result = parse_filename(filename)
                    # Should always return a ParsedFile object
                    assert hasattr(result, 'song_title')
                    assert hasattr(result, 'file_type')
                except Exception as e:
                    pytest.fail(f"Parser should handle '{filename}' gracefully, but raised: {e}")


# Integration test fixtures
@pytest.fixture
def sample_files():
    """Sample files for integration testing."""
    return [
        "All of Me - Bb.pdf",
        "Spain - Chick Corea - Eb.pdf", 
        "Take Five - Reference.mp3",
        "Summertime - Rhythm - C.pdf",
        "Random File.txt",
        "Blue Moon - Vocals - C.pdf",
        "Giant Steps - John Coltrane - Bb.pdf"
    ]


def test_batch_parsing_integration(sample_files):
    """Integration test for parsing multiple files."""
    parser = ContentParser()
    results = []
    
    for filename in sample_files:
        result = parser.parse_filename(filename)
        results.append(result)
    
    # Check that we got results for all files
    assert len(results) == len(sample_files)
    
    # Check that charts and audio were properly identified
    charts = [r for r in results if r.file_type == FileType.CHART]
    audio = [r for r in results if r.file_type == FileType.AUDIO]
    other = [r for r in results if r.file_type == FileType.OTHER]
    
    assert len(charts) > 0
    assert len(audio) > 0
    assert len(other) > 0
    
    # Verify statistics
    stats = parser.get_stats()
    assert stats["parsed"] == len(sample_files)
    assert stats["by_type"]["chart"] == len(charts)
    assert stats["by_type"]["audio"] == len(audio)
    assert stats["by_type"]["other"] == len(other)