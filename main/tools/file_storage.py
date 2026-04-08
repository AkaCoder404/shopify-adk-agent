"""File storage utilities for managing workspace directories."""

import os
import shutil
import urllib.request
from pathlib import Path
from typing import Optional


# Base workspace path
WORKSPACE_ROOT = Path(__file__).parent.parent.parent / "workspace"

# CSV directories
CSV_DIR = WORKSPACE_ROOT / "csv"
PIPELINE_DIR = CSV_DIR / "pipeline"
SYNC_DIR = CSV_DIR / "sync"
ARCHIVE_DIR = CSV_DIR / "archive"
EXPORTS_DIR = CSV_DIR / "exports"

# Image directories
IMAGES_DIR = WORKSPACE_ROOT / "images"
GENERATED_DIR = IMAGES_DIR / "generated"
CONTENT_DIR = IMAGES_DIR / "content"

# Temp directory
TEMP_DIR = WORKSPACE_ROOT / "temp"


def ensure_directories():
    """Ensure all workspace directories exist."""
    dirs = [
        PIPELINE_DIR,
        SYNC_DIR,
        ARCHIVE_DIR,
        EXPORTS_DIR,
        GENERATED_DIR,
        CONTENT_DIR,
        TEMP_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# Pipeline CSV paths
def get_pipeline_path(filename: str) -> Path:
    """Get path for a Pipeline CSV file."""
    return PIPELINE_DIR / filename


def get_archive_path(filename: str) -> Path:
    """Get path for an archived Pipeline CSV file."""
    return ARCHIVE_DIR / filename


# Sync State CSV paths
def get_sync_state_path(filename: str) -> Path:
    """Get path for a Sync State CSV file."""
    return SYNC_DIR / filename


# Export CSV paths
def get_export_path(filename: str) -> Path:
    """Get path for an export CSV file."""
    return EXPORTS_DIR / filename


# Image paths
def get_generated_image_path(filename: str) -> Path:
    """Get path for a generated image."""
    return GENERATED_DIR / filename


def get_content_path(filename: str) -> Path:
    """Get path for generated content JSON."""
    return CONTENT_DIR / filename


# Temp paths
def get_temp_path(filename: str) -> Path:
    """Get path for a temporary file."""
    return TEMP_DIR / filename


# Utility functions
def download_file(url: str, destination: Path) -> Path:
    """
    Download a file from URL to destination.
    
    Args:
        url: URL to download from
        destination: Path to save file
        
    Returns:
        Path to downloaded file
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, destination)
    return destination


def cleanup_temp():
    """Clean up temporary files."""
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)


def save_content_json(dsers_product_id: str, content: dict) -> str:
    """
    Save generated content as JSON file.
    
    Args:
        dsers_product_id: DSers product ID
        content: Dictionary with generated content (title, description, etc.)
        
    Returns:
        Path to saved JSON file
    """
    import json
    
    filename = f"{dsers_product_id}_content.json"
    filepath = get_content_path(filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2)
    
    return str(filepath)


def load_content_json(content_path: str) -> Optional[dict]:
    """
    Load generated content from JSON file.
    
    Args:
        content_path: Path to JSON file
        
    Returns:
        Content dictionary or None if not found
    """
    import json
    
    path = Path(content_path)
    if not path.exists():
        return None
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Ensure directories exist on module import
ensure_directories()
