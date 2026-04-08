"""Pipeline tools for Product Pipeline CSV operations."""

import csv
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from main.tools.file_storage import (
    get_pipeline_path,
    get_archive_path,
    PIPELINE_DIR,
)


def create_pipeline_entry(
    source_url: str,
    source_platform: str,
    estimated_cost: float,
    suggested_price: float,
    notes: str = "",
    priority: str = "medium",
    pipeline_file: str = "sourcing.csv"
) -> dict:
    """
    Add a new product to the Pipeline CSV during research phase.
    
    Args:
        source_url: AliExpress/Alibaba product URL
        source_platform: aliexpress | alibaba | accio | 1688
        estimated_cost: Expected cost price
        suggested_price: Target sell price
        notes: Research notes, competitor analysis
        priority: high | medium | low
        pipeline_file: Name of the pipeline CSV file
        
    Returns:
        The created entry as a dictionary
    """
    entry = {
        "id": f"PIPE-{uuid.uuid4().hex[:8].upper()}",
        "source_url": source_url,
        "source_platform": source_platform,
        "estimated_cost": str(estimated_cost),
        "suggested_price": str(suggested_price),
        "notes": notes,
        "priority": priority,
        "status": "researching",
        "dsers_import_id": "",
        "created_at": datetime.now().isoformat(),
        "evaluated_at": "",
    }
    
    filepath = get_pipeline_path(pipeline_file)
    file_exists = filepath.exists()
    
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)
    
    return entry


def read_pipeline(pipeline_file: str = "sourcing.csv") -> list[dict]:
    """
    Read all entries from Pipeline CSV.
    
    Args:
        pipeline_file: Name of the pipeline CSV file
        
    Returns:
        List of pipeline entries
    """
    filepath = get_pipeline_path(pipeline_file)
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def update_pipeline_status(
    pipe_id: str,
    status: str,
    dsers_import_id: str = "",
    pipeline_file: str = "sourcing.csv"
) -> dict:
    """
    Update status of a pipeline entry.
    
    Args:
        pipe_id: The pipeline entry ID (e.g., "PIPE-A1B2C3D4")
        status: researching | ready_to_import | imported | rejected
        dsers_import_id: DSers import ID (when status='imported')
        pipeline_file: Name of the pipeline CSV file
        
    Returns:
        Updated entry or None if not found
    """
    filepath = get_pipeline_path(pipeline_file)
    if not filepath.exists():
        return None
    
    entries = read_pipeline(pipeline_file)
    updated_entry = None
    
    for entry in entries:
        if entry["id"] == pipe_id:
            entry["status"] = status
            entry["evaluated_at"] = datetime.now().isoformat()
            if dsers_import_id:
                entry["dsers_import_id"] = dsers_import_id
            updated_entry = entry
            break
    
    if updated_entry:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)
    
    return updated_entry


def get_ready_to_import(pipeline_file: str = "sourcing.csv") -> list[dict]:
    """Get all products ready to import to DSers."""
    entries = read_pipeline(pipeline_file)
    return [e for e in entries if e.get("status") == "ready_to_import"]


def archive_old_pipelines(days: int = 7) -> list[str]:
    """
    Archive Pipeline CSVs older than specified days.
    Auto-cleanup to keep workspace tidy.
    
    Args:
        days: Age threshold for archiving (default: 7 days)
        
    Returns:
        List of archived file paths
    """
    archived = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for csv_file in PIPELINE_DIR.glob("*.csv"):
        # Get file modification time
        mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
        
        if mtime < cutoff:
            # Archive the file
            archive_path = get_archive_path(csv_file.name)
            csv_file.rename(archive_path)
            archived.append(str(archive_path))
    
    return archived


def get_pipeline_by_dsers_id(dsers_import_id: str, pipeline_file: str = "sourcing.csv") -> Optional[dict]:
    """Find pipeline entry by DSers import ID."""
    entries = read_pipeline(pipeline_file)
    for entry in entries:
        if entry.get("dsers_import_id") == dsers_import_id:
            return entry
    return None
