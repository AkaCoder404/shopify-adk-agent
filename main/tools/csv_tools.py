"""CSV tools for Sync State operations - lightweight ID mapping between DSers and Shopify."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from main.tools.file_storage import get_sync_state_path


def create_sync_entry(
    dsers_product_id: str,
    sync_file: str = "dsers_shopify_map.csv"
) -> dict:
    """
    Create a new Sync State entry after importing to DSers.
    
    Args:
        dsers_product_id: DSers import ID (e.g., "DS-12345678")
        sync_file: Name of the sync state CSV file
        
    Returns:
        The created entry as a dictionary
    """
    entry = {
        "dsers_product_id": dsers_product_id,
        "shopify_product_id": "",
        "shopify_variant_ids": json.dumps([]),
        "content_status": "needs_content",  # needs_content | content_pending | content_complete
        "ai_content_path": "",
        "last_pushed_at": "",
        "last_synced_at": datetime.now().isoformat(),
        "push_errors": "",
    }
    
    filepath = get_sync_state_path(sync_file)
    file_exists = filepath.exists()
    
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)
    
    return entry


def read_sync_state(sync_file: str = "dsers_shopify_map.csv") -> list[dict]:
    """
    Read all entries from Sync State CSV.
    
    Args:
        sync_file: Name of the sync state CSV file
        
    Returns:
        List of sync state entries
    """
    filepath = get_sync_state_path(sync_file)
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def update_sync_after_push(
    dsers_product_id: str,
    shopify_product_id: str,
    shopify_variant_ids: list[str],
    sync_file: str = "dsers_shopify_map.csv"
) -> Optional[dict]:
    """
    Update Sync State after pushing to Shopify.
    
    Args:
        dsers_product_id: DSers import ID
        shopify_product_id: Shopify product GID
        shopify_variant_ids: List of Shopify variant GIDs
        sync_file: Name of the sync state CSV file
        
    Returns:
        Updated entry or None if not found
    """
    filepath = get_sync_state_path(sync_file)
    entries = read_sync_state(sync_file)
    updated_entry = None
    
    for entry in entries:
        if entry["dsers_product_id"] == dsers_product_id:
            entry["shopify_product_id"] = shopify_product_id
            entry["shopify_variant_ids"] = json.dumps(shopify_variant_ids)
            entry["last_pushed_at"] = datetime.now().isoformat()
            entry["last_synced_at"] = datetime.now().isoformat()
            entry["push_errors"] = ""
            updated_entry = entry
            break
    
    if updated_entry:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)
    
    return updated_entry


def update_content_status(
    dsers_product_id: str,
    content_status: str,
    ai_content_path: str = "",
    sync_file: str = "dsers_shopify_map.csv"
) -> Optional[dict]:
    """
    Update content generation status.
    
    Args:
        dsers_product_id: DSers import ID
        content_status: needs_content | content_pending | content_complete
        ai_content_path: Path to generated content JSON file
        sync_file: Name of the sync state CSV file
        
    Returns:
        Updated entry or None if not found
    """
    filepath = get_sync_state_path(sync_file)
    entries = read_sync_state(sync_file)
    updated_entry = None
    
    for entry in entries:
        if entry["dsers_product_id"] == dsers_product_id:
            entry["content_status"] = content_status
            if ai_content_path:
                entry["ai_content_path"] = ai_content_path
            entry["last_synced_at"] = datetime.now().isoformat()
            updated_entry = entry
            break
    
    if updated_entry:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)
    
    return updated_entry


def get_by_content_status(status: str, sync_file: str = "dsers_shopify_map.csv") -> list[dict]:
    """Get all entries with specific content status."""
    entries = read_sync_state(sync_file)
    return [e for e in entries if e.get("content_status") == status]


def get_by_dsers_id(dsers_product_id: str, sync_file: str = "dsers_shopify_map.csv") -> Optional[dict]:
    """Find sync state entry by DSers product ID."""
    entries = read_sync_state(sync_file)
    for entry in entries:
        if entry["dsers_product_id"] == dsers_product_id:
            return entry
    return None


def get_by_shopify_id(shopify_product_id: str, sync_file: str = "dsers_shopify_map.csv") -> Optional[dict]:
    """Find sync state entry by Shopify product ID."""
    entries = read_sync_state(sync_file)
    for entry in entries:
        if entry["shopify_product_id"] == shopify_product_id:
            return entry
    return None


def get_shopify_variants(dsers_product_id: str, sync_file: str = "dsers_shopify_map.csv") -> list[str]:
    """Get Shopify variant IDs for a DSers product."""
    entry = get_by_dsers_id(dsers_product_id, sync_file)
    if entry and entry.get("shopify_variant_ids"):
        return json.loads(entry["shopify_variant_ids"])
    return []


def record_push_error(
    dsers_product_id: str,
    error_message: str,
    sync_file: str = "dsers_shopify_map.csv"
) -> Optional[dict]:
    """Record an error during push to Shopify."""
    filepath = get_sync_state_path(sync_file)
    entries = read_sync_state(sync_file)
    updated_entry = None
    
    for entry in entries:
        if entry["dsers_product_id"] == dsers_product_id:
            entry["push_errors"] = error_message
            entry["last_synced_at"] = datetime.now().isoformat()
            updated_entry = entry
            break
    
    if updated_entry:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)
    
    return updated_entry


# Legacy support - for non-DSers supplier CSV imports
def read_supplier_csv(source: str) -> list[dict]:
    """
    Read a supplier CSV file (for non-DSers suppliers).
    These are one-time imports, not tracked in Sync State.
    
    Args:
        source: Local file path to supplier CSV
        
    Returns:
        List of product dictionaries
    """
    import urllib.request
    from urllib.parse import urlparse
    import io
    
    parsed = urlparse(source)
    is_url = parsed.scheme in ('http', 'https')
    
    if is_url:
        with urllib.request.urlopen(source) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)


def write_export_csv(data: list[dict], filepath: str) -> str:
    """
    Write data to an export CSV file.
    
    Args:
        data: List of dictionaries to write
        filepath: Path to output CSV file
        
    Returns:
        Absolute path to written file
    """
    if not data:
        raise ValueError("Cannot write empty data to CSV")
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return str(path.absolute())
