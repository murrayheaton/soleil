"""
Metadata extraction utilities.

Provides functions for extracting metadata from files.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def extract_metadata(filepath: str) -> Dict[str, Any]:
    """
    Extract metadata from a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        Dict containing file metadata.
    """
    path = Path(filepath)
    
    if not path.exists():
        return {
            "exists": False,
            "error": "File not found"
        }
    
    stat = path.stat()
    
    metadata = {
        "exists": True,
        "filename": path.name,
        "size": stat.st_size,
        "size_human": format_file_size(stat.st_size),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": path.suffix.lower(),
        "mime_type": get_mime_type_from_extension(path.suffix),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
    }
    
    return metadata


def get_file_info(filename: str, file_id: Optional[str] = None, 
                  size: Optional[int] = None) -> Dict[str, Any]:
    """
    Get standardized file information.
    
    Args:
        filename: Name of the file.
        file_id: Optional file ID (e.g., from Google Drive).
        size: Optional file size in bytes.
        
    Returns:
        Dict with standardized file information.
    """
    from .naming import parse_filename
    from .file_types import get_file_type
    
    parsed = parse_filename(filename)
    file_type = get_file_type(filename)
    
    info = {
        "filename": filename,
        "file_id": file_id,
        "file_type": file_type,
        "title": parsed.get("title", "Unknown"),
        "key": parsed.get("key"),
        "extension": parsed.get("extension", ""),
        "size": size,
        "size_human": format_file_size(size) if size else None,
    }
    
    return info


def format_file_size(size_bytes: Optional[int]) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Human-readable size string.
    """
    if size_bytes is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def get_mime_type_from_extension(extension: str) -> Optional[str]:
    """
    Get MIME type from file extension.
    
    Args:
        extension: File extension (with or without dot).
        
    Returns:
        MIME type or None if unknown.
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    extension = extension.lower()
    
    mime_map = {
        # Documents
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.m4a': 'audio/m4a',
        '.aac': 'audio/aac',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg',
        # Video
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
    }
    
    return mime_map.get(extension)