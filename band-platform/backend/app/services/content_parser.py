"""
Content parser service for file naming conventions and instrument-key mapping.

This module handles parsing of Google Drive file names to extract musical information
and implements the instrument-to-key mapping logic following the PRP requirements.
"""

import re
import logging
from typing import Dict, List, Optional, NamedTuple
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Detected file types based on extensions."""
    CHART = "chart"
    AUDIO = "audio"
    OTHER = "other"


class ParsedFile(NamedTuple):
    """Structured representation of a parsed file."""
    original_filename: str
    song_title: str
    key: Optional[str]
    file_type: FileType
    extension: str
    composer: Optional[str] = None
    arranger: Optional[str] = None
    chart_type: Optional[str] = None
    tempo: Optional[str] = None
    metadata: Dict[str, str] = {}


# Instrument to transposition key mapping as defined in PRP
INSTRUMENT_KEY_MAPPING: Dict[str, str] = {
    # Brass instruments in Bb
    "trumpet": "Bb",
    "cornet": "Bb",
    "flugelhorn": "Bb",
    "tenor_saxophone": "Bb",
    "tenor_sax": "Bb",
    "soprano_saxophone": "Bb",
    "soprano_sax": "Bb",
    "clarinet": "Bb",
    "bass_clarinet": "Bb",
    
    # Brass and woodwinds in Eb
    "alto_saxophone": "Eb",
    "alto_sax": "Eb",
    "baritone_saxophone": "Eb",
    "baritone_sax": "Eb",
    "bari_sax": "Eb",
    "alto_clarinet": "Eb",
    
    # Brass instruments in F
    "french_horn": "F",
    "horn": "F",
    
    # Concert pitch instruments (C)
    "trombone": "C",
    "bass_trombone": "C",
    "tuba": "C",
    "euphonium": "C",
    "baritone": "C",
    "piano": "C",
    "keyboard": "C",
    "guitar": "C",
    "bass": "C",
    "electric_bass": "C",
    "upright_bass": "C",
    "drums": "C",
    "percussion": "C",
    "vibraphone": "C",
    "marimba": "C",
    "xylophone": "C",
    "flute": "C",
    "piccolo": "C",
    "oboe": "C",
    "bassoon": "C",
    "violin": "C",
    "viola": "C",
    "cello": "C",
    "string_bass": "C",
    "voice": "C",
    "vocals": "C",
    "lead_vocals": "C",
    "background_vocals": "C",
}

# File extension mappings
CHART_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".tiff", ".bmp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}

# Musical keys for validation
VALID_KEYS = {
    "C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", 
    "G", "G#", "Ab", "A", "A#", "Bb", "B",
    "Cm", "C#m", "Dbm", "Dm", "D#m", "Ebm", "Em", "Fm", 
    "F#m", "Gbm", "Gm", "G#m", "Abm", "Am", "A#m", "Bbm", "Bm"
}

# Chart type patterns
CHART_TYPE_PATTERNS = {
    "lead_sheet": ["lead", "melody", "vocal"],
    "rhythm": ["rhythm", "comp", "comping", "chord"],
    "full_arrangement": ["full", "arrangement", "score"],
    "bass": ["bass", "bassline"],
    "drum": ["drum", "percussion"]
}


class ContentParser:
    """
    Content parser for extracting musical information from filenames.
    
    This class handles the core logic for parsing Google Drive file names
    according to the band platform naming conventions.
    """
    
    # Regex patterns for filename parsing
    PATTERNS = {
        # Standard pattern: "Song Title - Key.ext"
        "standard": re.compile(
            r"^(?P<title>.+?)\s*-\s*(?P<key>[A-G][b#]?m?)\s*(?:\.(?P<ext>\w+))?$",
            re.IGNORECASE
        ),
        
        # With composer: "Song Title - Composer - Key.ext"
        "with_composer": re.compile(
            r"^(?P<title>.+?)\s*-\s*(?P<composer>.+?)\s*-\s*(?P<key>[A-G][b#]?m?)\s*(?:\.(?P<ext>\w+))?$",
            re.IGNORECASE
        ),
        
        # Reference audio pattern: "Song Title - Reference.ext"
        "reference": re.compile(
            r"^(?P<title>.+?)\s*-\s*(?P<type>reference|ref|demo|backing)\s*(?:\.(?P<ext>\w+))?$",
            re.IGNORECASE
        ),
        
        # Chart type pattern: "Song Title - Type - Key.ext"
        "with_type": re.compile(
            r"^(?P<title>.+?)\s*-\s*(?P<chart_type>\w+)\s*-\s*(?P<key>[A-G][b#]?m?)\s*(?:\.(?P<ext>\w+))?$",
            re.IGNORECASE
        ),
        
        # Tempo pattern: "Song Title - Key - Tempo.ext"
        "with_tempo": re.compile(
            r"^(?P<title>.+?)\s*-\s*(?P<key>[A-G][b#]?m?)\s*-\s*(?P<tempo>\d+\s*bpm|\w+\s+\w+)\s*(?:\.(?P<ext>\w+))?$",
            re.IGNORECASE
        ),
    }
    
    def __init__(self):
        """Initialize the content parser."""
        self.stats = {
            "parsed": 0,
            "failed": 0,
            "by_type": {"chart": 0, "audio": 0, "other": 0}
        }
    
    def parse_filename(self, filename: str) -> ParsedFile:
        """
        Parse a filename to extract musical information.
        
        Args:
            filename: The filename to parse.
            
        Returns:
            ParsedFile: Structured information extracted from the filename.
        """
        original_filename = filename
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        name_without_ext = file_path.stem
        
        # Determine file type
        file_type = self._determine_file_type(extension)
        
        # Try each pattern in order of complexity (most specific first)
        parsed_data = None
        pattern_order = ["with_composer", "with_type", "with_tempo", "standard", "reference"]
        
        for pattern_name in pattern_order:
            if pattern_name in self.PATTERNS:
                pattern = self.PATTERNS[pattern_name]
                match = pattern.match(name_without_ext)
                if match:
                    parsed_data = match.groupdict()
                    parsed_data["pattern_used"] = pattern_name
                    break
        
        if not parsed_data:
            # Fallback: treat entire name as title
            parsed_data = {
                "title": name_without_ext,
                "key": None,
                "pattern_used": "fallback"
            }
        
        # Clean and validate extracted data
        song_title = self._clean_title(parsed_data.get("title", ""))
        key = self._validate_key(parsed_data.get("key"))
        composer = self._clean_name(parsed_data.get("composer"))
        arranger = self._clean_name(parsed_data.get("arranger"))
        chart_type = self._determine_chart_type(
            parsed_data.get("chart_type"),
            song_title,
            filename
        )
        tempo = self._clean_tempo(parsed_data.get("tempo"))
        
        # Build metadata
        metadata = {
            "pattern_used": parsed_data.get("pattern_used", "unknown"),
            "original_extension": extension,
        }
        
        # Add any additional parsed fields to metadata
        for key_name, value in parsed_data.items():
            if key_name not in ["title", "key", "composer", "arranger", "chart_type", "tempo", "ext"]:
                metadata[key_name] = str(value) if value else None
        
        # Update statistics
        self.stats["parsed"] += 1
        self.stats["by_type"][file_type] += 1
        
        result = ParsedFile(
            original_filename=original_filename,
            song_title=song_title,
            key=key,
            file_type=file_type,
            extension=extension,
            composer=composer,
            arranger=arranger,
            chart_type=chart_type,
            tempo=tempo,
            metadata=metadata
        )
        
        logger.debug(f"Parsed '{filename}' -> {result}")
        return result
    
    def _determine_file_type(self, extension: str) -> FileType:
        """
        Determine file type based on extension.
        
        Args:
            extension: File extension (including dot).
            
        Returns:
            FileType: The determined file type.
        """
        if extension in CHART_EXTENSIONS:
            return FileType.CHART
        elif extension in AUDIO_EXTENSIONS:
            return FileType.AUDIO
        else:
            return FileType.OTHER
    
    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize song title.
        
        Args:
            title: Raw title string.
            
        Returns:
            str: Cleaned title.
        """
        if not title:
            return "Unknown Title"
        
        # Remove extra whitespace and normalize
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove common prefixes/suffixes that might be parsing artifacts
        title = re.sub(r'^[-\s]+|[-\s]+$', '', title)
        
        return title if title else "Unknown Title"
    
    def _clean_name(self, name: Optional[str]) -> Optional[str]:
        """
        Clean composer/arranger names.
        
        Args:
            name: Raw name string.
            
        Returns:
            str or None: Cleaned name or None if empty.
        """
        if not name:
            return None
        
        name = re.sub(r'\s+', ' ', name.strip())
        return name if name else None
    
    def _validate_key(self, key: Optional[str]) -> Optional[str]:
        """
        Validate and normalize musical key.
        
        Args:
            key: Raw key string.
            
        Returns:
            str or None: Validated key or None if invalid.
        """
        if not key:
            return None
        
        # Normalize key format
        key = key.strip()
        
        # Handle common variations
        key_mapping = {
            "bb": "Bb", "a#": "A#", "db": "Db", "c#": "C#",
            "eb": "Eb", "d#": "D#", "gb": "Gb", "f#": "F#",
            "ab": "Ab", "g#": "G#",
            # Minor keys
            "bbm": "Bbm", "a#m": "A#m", "dbm": "Dbm", "c#m": "C#m",
            "ebm": "Ebm", "d#m": "D#m", "gbm": "Gbm", "f#m": "F#m",
            "abm": "Abm", "g#m": "G#m",
        }
        
        normalized_key = key_mapping.get(key.lower(), key)
        
        return normalized_key if normalized_key in VALID_KEYS else None
    
    def _determine_chart_type(self, chart_type: Optional[str], title: str, filename: str) -> Optional[str]:
        """
        Determine chart type from explicit type or filename patterns.
        
        Args:
            chart_type: Explicitly parsed chart type.
            title: Song title.
            filename: Full filename.
            
        Returns:
            str or None: Determined chart type.
        """
        if chart_type:
            chart_type_lower = chart_type.lower()
            for type_name, patterns in CHART_TYPE_PATTERNS.items():
                if any(pattern in chart_type_lower for pattern in patterns):
                    return type_name
        
        # Check title and filename for chart type indicators
        text_to_check = f"{title} {filename}".lower()
        for type_name, patterns in CHART_TYPE_PATTERNS.items():
            if any(pattern in text_to_check for pattern in patterns):
                return type_name
        
        return None
    
    def _clean_tempo(self, tempo: Optional[str]) -> Optional[str]:
        """
        Clean and normalize tempo information.
        
        Args:
            tempo: Raw tempo string.
            
        Returns:
            str or None: Cleaned tempo or None if invalid.
        """
        if not tempo:
            return None
        
        tempo = tempo.strip()
        
        # Normalize BPM format
        tempo = re.sub(r'(\d+)\s*bpm', r'\1 BPM', tempo, flags=re.IGNORECASE)
        
        return tempo if tempo else None
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get parsing statistics.
        
        Returns:
            dict: Current parsing statistics.
        """
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset parsing statistics."""
        self.stats = {
            "parsed": 0,
            "failed": 0,
            "by_type": {"chart": 0, "audio": 0, "other": 0}
        }


# Utility functions for instrument-key mapping

def get_keys_for_instruments(instruments: List[str]) -> List[str]:
    """
    Get the transposition keys for a list of instruments.
    
    Args:
        instruments: List of instrument names.
        
    Returns:
        List of keys that match the instruments (e.g., ["Bb", "C"]).
    """
    if not instruments:
        return ["C"]  # Default to concert pitch
    
    keys = set()
    for instrument in instruments:
        # Normalize instrument name
        normalized = instrument.lower().replace(" ", "_").replace("-", "_")
        key = INSTRUMENT_KEY_MAPPING.get(normalized, "C")
        keys.add(key)
    
    return sorted(list(keys))


def get_instruments_for_key(key: str) -> List[str]:
    """
    Get instruments that use a specific transposition key.
    
    Args:
        key: Musical key (e.g., "Bb", "Eb", "C").
        
    Returns:
        List of instrument names that use this key.
    """
    instruments = []
    for instrument, instrument_key in INSTRUMENT_KEY_MAPPING.items():
        if instrument_key == key:
            # Convert back to display format
            display_name = instrument.replace("_", " ").title()
            instruments.append(display_name)
    
    return sorted(instruments)


def is_chart_accessible_by_user(chart_key: str, user_instruments: List[str]) -> bool:
    """
    Check if a chart is accessible by a user based on their instruments.
    
    Args:
        chart_key: The key of the chart.
        user_instruments: List of instruments the user plays.
        
    Returns:
        True if the user can access this chart based on their instruments.
    """
    user_keys = get_keys_for_instruments(user_instruments)
    return chart_key in user_keys


def suggest_key_for_instruments(instruments: List[str]) -> str:
    """
    Suggest the most appropriate key for a set of instruments.
    
    Args:
        instruments: List of instrument names.
        
    Returns:
        The most commonly used key for these instruments.
    """
    if not instruments:
        return "C"
    
    keys = get_keys_for_instruments(instruments)
    
    # If all instruments use the same key, return it
    if len(keys) == 1:
        return keys[0]
    
    # Priority order: C (concert pitch), then Bb, then Eb, then others
    priority_order = ["C", "Bb", "Eb", "F"]
    
    for key in priority_order:
        if key in keys:
            return key
    
    return keys[0] if keys else "C"


# Global parser instance
content_parser = ContentParser()


# Convenience functions using the global parser instance
def parse_filename(filename: str) -> ParsedFile:
    """Parse a filename using the global parser instance."""
    return content_parser.parse_filename(filename)


def get_parsing_stats() -> Dict[str, any]:
    """Get parsing statistics from the global parser instance."""
    return content_parser.get_stats()


def reset_parsing_stats() -> None:
    """Reset parsing statistics for the global parser instance."""
    content_parser.reset_stats()