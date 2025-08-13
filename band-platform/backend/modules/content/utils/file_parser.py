"""
File parser utilities for extracting metadata from chart filenames.

This module parses chart filenames to extract musical information like
key, tempo, instruments, and difficulty level.
"""

import re
from typing import Dict, List, Optional


def parse_chart_filename(filename: str) -> Dict[str, any]:
    """
    Parse chart filename to extract musical metadata.
    
    Expected filename format:
    "Song Title - Artist - Instrument - Key - Tempo - Difficulty.pdf"
    
    Examples:
    - "Take Five - Dave Brubeck - Bb Trumpet - Eb minor - Medium Swing - Intermediate.pdf"
    - "All The Things You Are - Kern - Alto Sax - Ab major - 120 BPM - Advanced.pdf"
    - "Fly Me To The Moon - Sinatra - Lead Sheet - C major - Ballad - Easy.pdf"
    
    Args:
        filename: The filename to parse
        
    Returns:
        Dictionary containing parsed metadata
    """
    if not filename:
        return {}
    
    # Remove file extension
    name_without_ext = re.sub(r'\.[^.]+$', '', filename)
    
    # Split by common separators
    parts = re.split(r'\s*[-–—]\s*', name_without_ext)
    
    if len(parts) < 2:
        # If we can't parse it properly, return basic info
        return {
            'title': name_without_ext,
            'instruments': [],
            'key': None,
            'tempo': None,
            'time_signature': None,
            'difficulty': None
        }
    
    # Extract basic information
    title = parts[0].strip()
    artist = parts[1].strip() if len(parts) > 1 else None
    
    # Initialize result
    result = {
        'title': title,
        'artist': artist,
        'instruments': [],
        'key': None,
        'tempo': None,
        'time_signature': None,
        'difficulty': None
    }
    
    # Parse remaining parts for musical information
    remaining_parts = parts[2:] if len(parts) > 2 else []
    
    for part in remaining_parts:
        part = part.strip()
        if not part:
            continue
            
        # Try to identify what type of information this part contains
        
        # Check for instruments
        if _is_instrument(part):
            result['instruments'].append(part)
            
        # Check for musical key
        elif _is_musical_key(part):
            result['key'] = part
            
        # Check for tempo
        elif _is_tempo(part):
            result['tempo'] = part
            
        # Check for time signature
        elif _is_time_signature(part):
            result['time_signature'] = part
            
        # Check for difficulty
        elif _is_difficulty(part):
            result['difficulty'] = part
            
        # If we can't identify it, assume it's an instrument
        else:
            result['instruments'].append(part)
    
    # If no instruments were found, try to extract from the title
    if not result['instruments']:
        result['instruments'] = _extract_instruments_from_title(title)
    
    return result


def _is_instrument(text: str) -> bool:
    """Check if text represents a musical instrument."""
    instruments = [
        # Brass
        'trumpet', 'trombone', 'euphonium', 'tuba', 'french horn', 'cornet', 'flugelhorn',
        'alto horn', 'baritone horn', 'sousaphone',
        
        # Woodwinds
        'saxophone', 'sax', 'alto sax', 'tenor sax', 'baritone sax', 'soprano sax',
        'clarinet', 'bass clarinet', 'flute', 'piccolo', 'oboe', 'bassoon',
        'english horn', 'contrabassoon',
        
        # Strings
        'violin', 'viola', 'cello', 'double bass', 'bass', 'guitar', 'acoustic guitar',
        'electric guitar', 'bass guitar', 'ukulele', 'mandolin', 'banjo', 'harp',
        
        # Piano/Keyboard
        'piano', 'keyboard', 'organ', 'synthesizer', 'synth', 'rhodes', 'wurlitzer',
        
        # Drums/Percussion
        'drums', 'drum set', 'percussion', 'bongos', 'congas', 'timpani', 'xylophone',
        'vibraphone', 'marimba', 'glockenspiel',
        
        # Voice
        'voice', 'vocal', 'soprano', 'alto', 'tenor', 'bass', 'baritone',
        
        # Other
        'accordion', 'harmonica', 'harmony', 'melody', 'lead sheet', 'chord chart',
        'rhythm section', 'rhythm', 'backing track', 'accompaniment'
    ]
    
    text_lower = text.lower()
    return any(instrument in text_lower for instrument in instruments)


def _is_musical_key(text: str) -> bool:
    """Check if text represents a musical key."""
    # Common key patterns
    key_patterns = [
        r'^[A-G][#b]?\s*(major|minor|maj|min|m)$',  # C major, Bb minor, etc.
        r'^[A-G][#b]?\s*$',  # Just the note name
        r'^[A-G][#b]?\s*[A-G][#b]?\s*$',  # Two note names (for transpositions)
    ]
    
    text_clean = text.strip()
    return any(re.match(pattern, text_clean, re.IGNORECASE) for pattern in key_patterns)


def _is_tempo(text: str) -> bool:
    """Check if text represents a tempo marking."""
    tempo_patterns = [
        r'^\d+\s*BPM$',  # 120 BPM
        r'^\d+\s*beats?$',  # 120 beats
        r'^[A-Z][a-z]+$',  # Allegro, Andante, etc.
        r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Medium Swing, Fast Latin, etc.
    ]
    
    text_clean = text.strip()
    return any(re.match(pattern, text_clean) for pattern in tempo_patterns)


def _is_time_signature(text: str) -> bool:
    """Check if text represents a time signature."""
    # Common time signatures
    time_sigs = [
        r'^\d+/\d+$',  # 4/4, 3/4, 6/8, etc.
        r'^C$',  # Common time (4/4)
        r'^C\|$',  # Cut time (2/2)
    ]
    
    text_clean = text.strip()
    return any(re.match(pattern, text_clean) for pattern in time_sigs)


def _is_difficulty(text: str) -> bool:
    """Check if text represents a difficulty level."""
    difficulties = [
        'beginner', 'easy', 'intermediate', 'advanced', 'expert',
        'novice', 'student', 'professional', 'pro'
    ]
    
    text_lower = text.lower()
    return any(difficulty in text_lower for difficulty in difficulties)


def _extract_instruments_from_title(title: str) -> List[str]:
    """Try to extract instrument information from the title."""
    instruments = []
    
    # Look for common instrument patterns in the title
    title_lower = title.lower()
    
    # Check for specific instruments mentioned
    if 'trumpet' in title_lower:
        instruments.append('Trumpet')
    if 'sax' in title_lower:
        instruments.append('Saxophone')
    if 'piano' in title_lower:
        instruments.append('Piano')
    if 'guitar' in title_lower:
        instruments.append('Guitar')
    if 'drums' in title_lower:
        instruments.append('Drums')
    if 'bass' in title_lower and 'guitar' not in title_lower:
        instruments.append('Bass')
    if 'voice' in title_lower or 'vocal' in title_lower:
        instruments.append('Voice')
    
    # If no specific instruments found, add generic categories
    if not instruments:
        if 'lead sheet' in title_lower or 'chord chart' in title_lower:
            instruments.append('Lead Sheet')
        elif 'rhythm' in title_lower:
            instruments.append('Rhythm Section')
        else:
            instruments.append('All Instruments')
    
    return instruments


def parse_audio_filename(filename: str) -> Dict[str, any]:
    """
    Parse audio filename to extract metadata.
    
    Expected format:
    "Song Title - Artist - Type - Key - Tempo.mp3"
    
    Args:
        filename: The filename to parse
        
    Returns:
        Dictionary containing parsed metadata
    """
    # Reuse chart parser for now, audio files often follow similar naming
    return parse_chart_filename(filename)


def parse_setlist_filename(filename: str) -> Dict[str, any]:
    """
    Parse setlist filename to extract metadata.
    
    Expected format:
    "Venue - Date - Event Type - Band Name.xlsx"
    
    Args:
        filename: The filename to parse
        
    Returns:
        Dictionary containing parsed metadata
    """
    if not filename:
        return {}
    
    # Remove file extension
    name_without_ext = re.sub(r'\.[^.]+$', '', filename)
    
    # Split by common separators
    parts = re.split(r'\s*[-–—]\s*', name_without_ext)
    
    if len(parts) < 2:
        return {
            'title': name_without_ext,
            'venue': None,
            'date': None,
            'event_type': None,
            'band_name': None
        }
    
    result = {
        'title': name_without_ext,
        'venue': parts[0].strip() if len(parts) > 0 else None,
        'date': parts[1].strip() if len(parts) > 1 else None,
        'event_type': parts[2].strip() if len(parts) > 2 else None,
        'band_name': parts[3].strip() if len(parts) > 3 else None
    }
    
    return result
