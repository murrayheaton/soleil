"""
File type detection utilities.

Provides functions for identifying and categorizing file types.
"""
from pathlib import Path
from typing import Optional

# File extension mappings
CHART_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".tiff", ".bmp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm"}
DOCUMENT_EXTENSIONS = {".doc", ".docx", ".txt", ".rtf", ".odt"}


def get_file_type(filename: str) -> str:
    """
    Determine file type based on extension.
    
    Args:
        filename: The filename to check.
        
    Returns:
        File type: 'chart', 'audio', 'video', 'document', or 'other'.
    """
    ext = Path(filename).suffix.lower()
    
    if ext in CHART_EXTENSIONS:
        return "chart"
    elif ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    elif ext in DOCUMENT_EXTENSIONS:
        return "document"
    else:
        return "other"


def is_chart_file(filename: str) -> bool:
    """
    Check if a file is a chart/sheet music file.
    
    Args:
        filename: The filename to check.
        
    Returns:
        True if the file is a chart file.
    """
    return get_file_type(filename) == "chart"


def is_audio_file(filename: str) -> bool:
    """
    Check if a file is an audio file.
    
    Args:
        filename: The filename to check.
        
    Returns:
        True if the file is an audio file.
    """
    return get_file_type(filename) == "audio"


def get_mime_type(filename: str) -> Optional[str]:
    """
    Get MIME type for a file based on extension.
    
    Args:
        filename: The filename to check.
        
    Returns:
        MIME type string or None if unknown.
    """
    ext = Path(filename).suffix.lower()
    
    mime_types = {
        # Charts
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
        # Audio
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/m4a",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".wma": "audio/x-ms-wma",
        # Video
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".wmv": "video/x-ms-wmv",
        ".flv": "video/x-flv",
        ".webm": "video/webm",
        # Documents
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".rtf": "application/rtf",
        ".odt": "application/vnd.oasis.opendocument.text",
    }
    
    return mime_types.get(ext)