"""
File naming convention utilities.

Provides functions for parsing and formatting file names.
"""
import re
from pathlib import Path
from typing import Dict, Optional


def parse_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    Parse a filename to extract musical information.
    
    Args:
        filename: The filename to parse.
        
    Returns:
        Dict with 'title', 'key', 'type', and 'extension'.
    """
    path = Path(filename)
    name_without_ext = path.stem
    extension = path.suffix
    
    # Try different patterns
    patterns = [
        # Song Title - Key
        r"^(?P<title>.+?)\s*[-_]\s*(?P<key>[A-G][b#]?m?)\s*$",
        # Song Title - Type - Key
        r"^(?P<title>.+?)\s*[-_]\s*(?P<type>\w+)\s*[-_]\s*(?P<key>[A-G][b#]?m?)\s*$",
        # Song Title - Type
        r"^(?P<title>.+?)\s*[-_]\s*(?P<type>reference|ref|demo|backing|chord|lyrics)\s*$",
    ]
    
    for pattern in patterns:
        match = re.match(pattern, name_without_ext, re.IGNORECASE)
        if match:
            result = match.groupdict()
            result['extension'] = extension
            return result
    
    # Fallback: entire name is title
    return {
        'title': name_without_ext,
        'key': None,
        'type': None,
        'extension': extension
    }


def clean_filename(filename: str) -> str:
    """
    Clean a filename to remove invalid characters.
    
    Args:
        filename: The filename to clean.
        
    Returns:
        Cleaned filename safe for file systems.
    """
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove leading/trailing spaces and dots
    cleaned = cleaned.strip(' .')
    
    return cleaned if cleaned else "unnamed"


def format_song_title(title: str) -> str:
    """
    Format a song title for display.
    
    Args:
        title: Raw song title.
        
    Returns:
        Formatted title with proper capitalization.
    """
    # Common patterns to fix
    replacements = {
        'dont': "Don't",
        'cant': "Can't",
        'wont': "Won't",
        'aint': "Ain't",
        'isnt': "Isn't",
        'wasnt': "Wasn't",
        'youre': "You're",
        'theyre': "They're",
        'its': "It's",
        'whats': "What's",
        'thats': "That's",
        'im': "I'm",
        'ive': "I've",
        'ill': "I'll",
        'id': "I'd",
    }
    
    # Title case
    formatted = title.title()
    
    # Apply replacements (case insensitive)
    for old, new in replacements.items():
        pattern = r'\b' + old + r'\b'
        formatted = re.sub(pattern, new, formatted, flags=re.IGNORECASE)
    
    # Fix articles and prepositions that shouldn't be capitalized
    small_words = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 
                   'if', 'in', 'of', 'on', 'or', 'the', 'to', 'with']
    
    words = formatted.split()
    for i, word in enumerate(words):
        if i > 0 and i < len(words) - 1 and word.lower() in small_words:
            words[i] = word.lower()
    
    return ' '.join(words)


def generate_filename(title: str, key: Optional[str] = None, 
                     file_type: Optional[str] = None, extension: str = ".pdf") -> str:
    """
    Generate a standardized filename.
    
    Args:
        title: Song title.
        key: Musical key (optional).
        file_type: File type descriptor (optional).
        extension: File extension.
        
    Returns:
        Standardized filename.
    """
    parts = [clean_filename(title)]
    
    if file_type:
        parts.append(file_type)
    
    if key:
        parts.append(key)
    
    filename = " - ".join(parts) + extension
    return filename