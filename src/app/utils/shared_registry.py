"""
Shared Registry Utility

This module provides a function to reconstruct the FILE_REGISTRY from disk metadata.
This is needed because the MCP server runs in a separate process and cannot access
the in-memory FILE_REGISTRY from the main FastAPI application.
"""

import json
from pathlib import Path
from typing import Dict
from src.app.configs.logger_config import get_logger

logger = get_logger("Shared-Registry")

# Directory paths (same as file_manager.py)
UPLOAD_DIR = Path("uploads")
SCHEMA_DIR = Path("schemas")
METADATA_DIR = Path("metadata")


def get_file_registry_from_disk() -> Dict[str, Dict]:
    """
    Reconstruct FILE_REGISTRY by reading metadata files from disk.
    
    This function allows the MCP server (running in a separate process)
    to access file information without needing the in-memory registry
    from the FastAPI process.
    
    Returns:
        Dict: File registry with same structure as in-memory FILE_REGISTRY
    """
    file_registry = {}
    
    # Ensure directories exist
    UPLOAD_DIR.mkdir(exist_ok=True)
    SCHEMA_DIR.mkdir(exist_ok=True)
    METADATA_DIR.mkdir(exist_ok=True)
    
    # Find all uploaded files
    files = list(UPLOAD_DIR.glob("*.*"))
    
    if not files:
        logger.debug("No uploaded files found on disk")
        return {}
    
    logger.debug(f"Found {len(files)} file(s) on disk, reconstructing registry...")
    
    for file_path in files:
        file_id = file_path.stem
        metadata_file = METADATA_DIR / f"{file_id}.json"
        
        if not metadata_file.exists():
            logger.warning(f"No metadata found for {file_path.name}, skipping...")
            continue
        
        try:
            # Load metadata
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Load schema if available
            schema_file = SCHEMA_DIR / f"{file_id}.json"
            schema = None
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            
            # Build registry entry
            file_registry[file_id] = {
                "file_id": file_id,
                "original_filename": metadata.get("original_filename"),
                "table_name": metadata.get("table_name"),
                "file_path": str(file_path),
                "file_hash": metadata.get("file_hash", ""),
                "schema": schema,
                "uploaded_at": metadata.get("uploaded_at")
            }
            
            logger.debug(
                f"Loaded: {metadata.get('original_filename')} "
                f"(table: {metadata.get('table_name')})"
            )
            
        except json.JSONDecodeError:
            logger.warning(f"Metadata file for {file_id} is empty or corrupted (likely being written), skipping...")
        except Exception as e:
            logger.error(f"Failed to load metadata for {file_id}: {e}", exc_info=True)
    
    logger.info(f"Registry reconstructed with {len(file_registry)} file(s)")
    return file_registry
