"""
SOLEIL Content Parser - Integrated from working ContextSorter system.

This module provides robust filename parsing and chart organization based on
your proven file naming conventions and transposition mapping system.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Detected file types based on extensions."""
    CHART = "chart"
    AUDIO = "audio"
    OTHER = "other"


@dataclass
class ParsedFile:
    """Structured representation of a parsed file using SOLEIL conventions."""
    original_filename: str
    song_title: str
    key: Optional[str]
    file_type: FileType
    extension: str
    transposition: Optional[str] = None
    suffix: Optional[str] = None
    composer: Optional[str] = None
    arranger: Optional[str] = None
    chart_type: Optional[str] = None
    tempo: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# SOLEIL Transposition Tokens (from your working system)
TRANSPOSITION_TOKENS = {
    "Bb",        # B-flat instruments (tenor sax, trumpet, clarinet)
    "Eb",        # E-flat instruments (alto sax, baritone sax)
    "Concert",   # Concert pitch (piano, guitar, bass, violin)
    "BassClef",  # Bass clef instruments (trombone, tuba, bass)
    "Chords",    # Harmony/Rhythm section (guitar, piano, bass, drums)
    "Lyrics",    # Vocal charts for singers
}

# Instrument to transposition mapping
INSTRUMENT_KEY_MAPPING = {
    # Bb instruments (Trumpet, Tenor Sax)
    "trumpet": "Bb",
    "tpt": "Bb",
    "tp": "Bb",
    "tenor": "Bb",
    "tenor_sax": "Bb",
    "tenor_saxophone": "Bb",
    
    # Eb instruments (Alto Sax, Bari Sax)
    "alto": "Eb",
    "alto_sax": "Eb",
    "alto_saxophone": "Eb",
    "baritone_sax": "Eb",
    "baritone_saxophone": "Eb",
    "bari_sax": "Eb",
    "bari": "Eb",
    
    # Concert pitch (Violin)
    "violin": "Concert",
    "vln": "Concert",
    
    # Bass clef (Trombone)
    "trombone": "BassClef",
    "tbn": "BassClef",
    "tb": "BassClef",
    "bone": "BassClef",
    
    # Chords (Piano/Keys, Guitar, Bass, Drums)
    "piano": "Chords",
    "pno": "Chords",
    "keys": "Chords",
    "keyboard": "Chords",
    "guitar": "Chords",
    "gtr": "Chords",
    "bass": "Chords",
    "electric_bass": "Chords",
    "upright_bass": "Chords",
    "bass_guitar": "Chords",
    "drums": "Chords",
    "dr": "Chords",
    "percussion": "Chords",
    
    # Lyrics (Singers)
    "voice": "Lyrics",
    "vocals": "Lyrics",
    "vox": "Lyrics",
    "singer": "Lyrics",
    "singers": "Lyrics",
}

# File extensions
CHART_EXTENSIONS = {".pdf"}  # Charts are only PDFs
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}

# Validation patterns (from your working system)
VALIDATION_PATTERNS = {
    # Standard format: Title_Transposition.ext (simplified, no redundant _Chart suffix)
    "standard_pattern": r"^[A-Z][a-zA-Z0-9]*_(Bb|Eb|Concert|BassClef|Chords|Lyrics)\.[a-zA-Z0-9]+$",
    
    # Event doc format: YYYY-MM-DD_Suffix.ext  
    "event_pattern": r"^\d{4}-\d{2}-\d{2}_[A-Z][a-zA-Z0-9]*\.[a-zA-Z0-9]+$",
    
    # Non-transposed format: Title_Suffix.ext
    "no_transposition_pattern": r"^[A-Z][a-zA-Z0-9]*_[A-Z][a-zA-Z0-9]*\.[a-zA-Z0-9]+$",
    
    # Title case validation
    "title_case_pattern": r"^[A-Z][a-zA-Z0-9]*$"
}


class TitleCaseConverter:
    """Converts song titles to consistent TitleCase format (from your working system)."""
    
    @classmethod
    def convert(cls, title: str) -> str:
        """
        Convert title to TitleCase following music industry conventions.
        
        Args:
            title: Original title string
            
        Returns:
            TitleCase formatted string with no spaces or punctuation
        """
        if not title:
            return ""
        
        # Remove common separators and clean the title
        cleaned = re.sub(r'[-_\s\(\)\[\]]+', ' ', title)
        cleaned = re.sub(r'[^\w\s]', '', cleaned)  # Remove punctuation
        
        words = cleaned.split()
        result_words = []
        
        for word in words:
            word = word.lower()
            # For filenames, capitalize all words since we're joining without spaces
            word = word.capitalize()
            result_words.append(word)
        
        # Join without spaces for filename
        return ''.join(result_words)


class TranspositionMapper:
    """Maps instrument names to transposition tokens (from your working system)."""
    
    def __init__(self):
        self.mapping = INSTRUMENT_KEY_MAPPING
        
        # Create reverse mapping for detection
        self.detection_patterns = {}
        for instrument, transposition in self.mapping.items():
            # Create regex patterns for common instrument name variations
            pattern = self._create_instrument_pattern(instrument)
            self.detection_patterns[pattern] = transposition
    
    def _create_instrument_pattern(self, instrument: str) -> str:
        """Create regex pattern for instrument detection."""
        # Handle common variations
        variations = {
            'tenor': r'tenor|tn|t\.sax',
            'alto': r'alto|as|a\.sax',
            'trumpet': r'trumpet|tpt|tp',
            'trombone': r'trombone|tbn|tb',
            'bass': r'bass|bs|b\.',
            'piano': r'piano|pno|p\.',
            'guitar': r'guitar|gtr|g\.',
            'vocals': r'vocals?|vox|v\.',
        }
        
        return variations.get(instrument, instrument)
    
    def detect_transposition(self, filename: str) -> Optional[str]:
        """
        Detect transposition token from filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Detected transposition token or None
        """
        filename_lower = filename.lower()
        
        # Check for direct transposition tokens first
        direct_tokens = ['bb', 'eb', 'concert', 'bassclef']
        for token in direct_tokens:
            if token in filename_lower:
                return token.title() if token != 'bassclef' else 'BassClef'
        
        # Check for instrument names
        for pattern, transposition in self.detection_patterns.items():
            if re.search(pattern, filename_lower):
                return transposition
                
        return None


class SOLEILContentParser:
    """
    SOLEIL Content Parser - Integrated from working ContextSorter system.
    
    This class handles the core logic for parsing Google Drive file names
    according to your proven SOLEIL naming conventions.
    """
    
    def __init__(self):
        """Initialize the SOLEIL content parser."""
        self.title_converter = TitleCaseConverter()
        self.transposition_mapper = TranspositionMapper()
        self.stats = {
            "parsed": 0,
            "failed": 0,
            "by_type": {"chart": 0, "audio": 0, "other": 0}
        }
    
    def parse_filename(self, filename: str) -> ParsedFile:
        """
        Parse a filename to extract musical information using SOLEIL conventions.
        
        Expected format: SongName_Transposition.pdf
        
        Args:
            filename: The filename to parse.
            
        Returns:
            ParsedFile: Structured information extracted from the filename.
        """
        original_filename = filename
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        name_without_ext = file_path.stem
        
        # Determine file type (charts must be PDFs)
        file_type = self._determine_file_type(extension)
        
        # Parse the standard SOLEIL format: SongName_Transposition
        title, transposition = self._parse_standard_format(name_without_ext)
        
        # Clean and validate extracted data
        song_title = self.title_converter.convert(title)
        key = self._validate_key(transposition)
        chart_type = self._determine_chart_type(suffix, song_title, filename)
        tempo = self._extract_tempo(filename)
        
        # Build metadata
        metadata = {
            "original_format": "soleil" if self._is_valid_soleil_format(name_without_ext) else "non_standard",
            "original_extension": extension,
            "transposition": transposition,
            "suffix": suffix,
        }
        
        # Update statistics
        self.stats["parsed"] += 1
        self.stats["by_type"][file_type] += 1
        
        result = ParsedFile(
            original_filename=original_filename,
            song_title=song_title,
            key=key,
            file_type=file_type,
            extension=extension,
            transposition=transposition,
            suffix=suffix,
            chart_type=chart_type,
            tempo=tempo,
            metadata=metadata
        )
        
        logger.debug(f"Parsed '{filename}' -> {result}")
        return result
    
    def _is_valid_soleil_format(self, filename: str) -> bool:
        """Check if filename already follows SOLEIL format."""
        patterns = VALIDATION_PATTERNS
        
        return (
            re.match(patterns.get('standard_pattern', ''), filename + '.ext') is not None or
            re.match(patterns.get('event_pattern', ''), filename + '.ext') is not None or
            re.match(patterns.get('no_transposition_pattern', ''), filename + '.ext') is not None
        )
    
    def _parse_standard_format(self, filename: str) -> Tuple[str, Optional[str]]:
        """Parse filename following standard SOLEIL format: SongName_Transposition."""
        parts = filename.split('_')
        
        if len(parts) == 2:  # SongName_Transposition
            title = parts[0]
            transposition = parts[1] if parts[1] in TRANSPOSITION_TOKENS else None
            return title, transposition
        elif len(parts) == 1:  # Just SongName (no transposition)
            return parts[0], None
        else:
            # Multiple underscores - take everything before last underscore as title
            title = '_'.join(parts[:-1])
            transposition = parts[-1] if parts[-1] in TRANSPOSITION_TOKENS else None
            return title, transposition
    
    def _parse_non_standard_format(self, filename: str) -> Tuple[str, Optional[str], str]:
        """Parse non-standard filename to extract components."""
        # Remove common prefixes/suffixes and clean
        cleaned = re.sub(r'\([^)]*\)', '', filename)  # Remove parentheses
        cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)  # Remove brackets
        cleaned = cleaned.strip()
        
        # Extract title (everything before common separators)
        title_match = re.match(r'^([^-_]+)', cleaned)
        title = title_match.group(1).strip() if title_match else cleaned
        
        # Try to detect transposition from the filename
        transposition = self.transposition_mapper.detect_transposition(filename)
        
        # Determine suffix based on file type
        suffix = self._detect_suffix(filename)
        
        return title, transposition, suffix
    
    def _detect_suffix(self, filename: str) -> str:
        """Detect appropriate suffix based on filename content."""
        filename_lower = filename.lower()
        
        # Chart-related suffixes
        if any(word in filename_lower for word in ['chart', 'lead', 'score', 'sheet']):
            return 'Chart'
        elif any(word in filename_lower for word in ['chord', 'chords']):
            return 'Chords'
        elif any(word in filename_lower for word in ['lyric', 'lyrics']):
            return 'Lyrics'
        
        # Audio-related suffixes
        elif any(word in filename_lower for word in ['ref', 'reference', 'demo']):
            return 'Ref'
        elif any(word in filename_lower for word in ['cue', 'cues']):
            return 'Cues'
        elif any(word in filename_lower for word in ['spl', 'sp']):
            return 'SPL'
        elif any(word in filename_lower for word in ['backing', 'accompaniment']):
            return 'Backing'
        
        # Default to Chart for PDFs, Ref for audio
        return 'Chart' if filename.lower().endswith('.pdf') else 'Ref'
    
    def _determine_file_type(self, extension: str) -> FileType:
        """Determine file type based on extension."""
        if extension in CHART_EXTENSIONS:
            return FileType.CHART
        elif extension in AUDIO_EXTENSIONS:
            return FileType.AUDIO
        else:
            return FileType.OTHER
    
    def _validate_key(self, key: Optional[str]) -> Optional[str]:
        """Validate and normalize musical key."""
        if not key:
            return None
        
        # Normalize common variations
        key_mapping = {
            'bb': 'Bb', 'Bb': 'Bb', 'BB': 'Bb',
            'eb': 'Eb', 'Eb': 'Eb', 'EB': 'Eb',
            'concert': 'Concert', 'Concert': 'Concert', 'CONCERT': 'Concert',
            'bassclef': 'BassClef', 'BassClef': 'BassClef', 'BASSCLEF': 'BassClef',
            'chords': 'Chords', 'Chords': 'Chords', 'CHORDS': 'Chords',
            'lyrics': 'Lyrics', 'Lyrics': 'Lyrics', 'LYRICS': 'Lyrics',
        }
        
        return key_mapping.get(key, key)
    
    def _determine_chart_type(self, suffix: Optional[str], title: str, filename: str) -> Optional[str]:
        """Determine chart type based on suffix and filename patterns."""
        if not suffix:
            return None
        
        # Map suffixes to chart types
        suffix_to_type = {
            'Chart': 'full_arrangement',
            'Chords': 'chord_chart',
            'Lead': 'lead_sheet',
            'Score': 'full_arrangement',
            'Lyrics': 'lyrics',
        }
        
        return suffix_to_type.get(suffix, 'other')
    
    def _extract_tempo(self, filename: str) -> Optional[str]:
        """Extract tempo information from filename."""
        # Look for common tempo patterns
        tempo_patterns = [
            r'(\d+)\s*bpm',  # 120 BPM
            r'(\d+)\s*beats?',  # 120 beats
            r'(medium|fast|slow|ballad|swing|latin|rock|jazz)',  # Style-based
        ]
        
        for pattern in tempo_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        return self.stats.copy()


# Convenience function for backward compatibility
def parse_filename(filename: str) -> ParsedFile:
    """Parse filename using SOLEIL conventions."""
    parser = SOLEILContentParser()
    return parser.parse_filename(filename)


def get_instrument_key(instrument: str) -> Optional[str]:
    """Get appropriate key for instrument."""
    return INSTRUMENT_KEY_MAPPING.get(instrument.lower())


def is_chart_accessible_by_user(chart_key: str, user_instruments: List[str]) -> bool:
    """Check if a chart is accessible by a user based on their instruments."""
    if not chart_key or not user_instruments:
        return False
    
    # Get the keys that the user's instruments can play
    user_keys = set()
    for instrument in user_instruments:
        key = get_instrument_key(instrument)
        if key:
            user_keys.add(key)
    
    # Check if the chart key is accessible
    return chart_key in user_keys
