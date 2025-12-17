"""
File Manager API Endpoints

Purpose
-------
Provides a clean and minimal interface for uploading, tracking, validating, and deleting Excel/CSV
files used by the SQL chatbot. It keeps the file registry, metadata, and database tables in sync.

Core responsibilities
---------------------
- Upload files → generate schema → load into DB → store metadata.
- Return status and detailed info about uploaded files.
- Delete a single file or clear all files safely.
- Reconstruct registry and rebuild database on startup.
"""

# =============================== IMPORTS ===============================
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import json
from typing import Optional, Dict, List
import re

from src.app.configs.logger_config import get_logger
from src.app.utils.schema_generator import generate_schema, generate_schema_summary
from src.app.utils.database_manager import (
    load_file_to_db,
    remove_table_from_db,
    rebuild_database,
    compute_file_hash,
    get_all_table_names
)

# =============================== LOGGER ===============================
logger = get_logger("File-Manager-Api-Service")

# =============================== ROUTER ===============================
router = APIRouter(prefix="/api", tags=["file-manager"])

# =============================== DIRECTORIES ===============================
UPLOAD_DIR = Path("uploads")
SCHEMA_DIR = Path("schemas")
METADATA_DIR = Path("metadata")

UPLOAD_DIR.mkdir(exist_ok=True)
SCHEMA_DIR.mkdir(exist_ok=True)
METADATA_DIR.mkdir(exist_ok=True)

logger.info(f"Upload folder is ready at this path: {UPLOAD_DIR.resolve()}")
logger.info(f"Schema folder is ready at this path: {SCHEMA_DIR.resolve()}")
logger.info(f"Metadata folder is ready at this path: {METADATA_DIR.resolve()}")

# =============================== CONSTANTS ===============================
MAX_FILES = 10  # Maximum number of files allowed

# =============================== GLOBAL STATE - FILE REGISTRY ===============================
FILE_REGISTRY: Dict[str, Dict] = {}

# =============================== HELPER FUNCTIONS ===============================
def derive_table_name(filename: str, existing_names: List[str]) -> str:
    """Derive a SQL-safe table name from filename."""
    base_name = Path(filename).stem
    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
    table_name = re.sub(r'_+', '_', table_name).strip('_').lower()

    if table_name and table_name[0].isdigit():
        table_name = "t_" + table_name
    if not table_name:
        table_name = "table"

    original = table_name
    counter = 1
    while table_name in existing_names:
        table_name = f"{original}_{counter}"
        counter += 1
    return table_name


def check_duplicate_content(file_hash: str) -> Optional[str]:
    """Return filename if duplicate content exists."""
    for file_id, info in FILE_REGISTRY.items():
        if info.get("file_hash") == file_hash:
            return info.get("original_filename")
    return None

# =============================== STARTUP CHECK ===============================
def check_files_on_startup():
    """Reconstruct registry + rebuild DB if files exist on disk."""
    global FILE_REGISTRY

    logger.info("Checking for uploaded files on startup...")
    files = list(UPLOAD_DIR.glob("*.*"))

    if not files:
        logger.info("No uploaded files found during startup.")
        return

    logger.info(f"Found {len(files)} file(s). Rebuilding file registry...")

    for file_path in files:
        file_id = file_path.stem
        metadata_file = METADATA_DIR / f"{file_id}.json"

        if not metadata_file.exists():
            logger.warning(f"No metadata found for {file_path.name}, skipping...")
            continue

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            schema_file = SCHEMA_DIR / f"{file_id}.json"
            schema = None
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)

            FILE_REGISTRY[file_id] = {
                "file_id": file_id,
                "original_filename": metadata.get("original_filename"),
                "table_name": metadata.get("table_name"),
                "file_path": str(file_path),
                "file_hash": metadata.get("file_hash", ""),
                "schema": schema,
                "uploaded_at": metadata.get("uploaded_at")
            }

            logger.info(
                f"Loaded file: {metadata.get('original_filename')} "
                f"(table: {metadata.get('table_name')})"
            )

        except Exception as e:
            logger.error(f"Failed to load metadata for {file_id}: {e}", exc_info=True)

    if FILE_REGISTRY:
        try:
            logger.info(f"Rebuilding database with {len(FILE_REGISTRY)} file(s)...")
            rebuild_database(FILE_REGISTRY)
            logger.info("Database rebuild complete.")
        except Exception as e:
            logger.error(f"Failed to rebuild database: {e}", exc_info=True)

    logger.info(f"Startup completed with {len(FILE_REGISTRY)} file(s) in registry.")

# =============================== 1. FILE UPLOAD ===============================
@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload an Excel/CSV file → generate schema → load to DB → update registry."""
    logger.info(f"Upload request received for file: {file.filename}")

    try:
        # File limit check
        if len(FILE_REGISTRY) >= MAX_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_FILES} files allowed. Please delete some files first."
            )

        # Validate extension
        allowed_ext = {".xlsx", ".xls", ".csv"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_ext:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_ext)}"
            )

        # Save temp
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        with open(file_path, "wb") as f:
            while chunk := await file.read(8192):
                f.write(chunk)

        # Duplicate detection
        file_hash = compute_file_hash(str(file_path))
        dup = check_duplicate_content(file_hash)
        if dup:
            file_path.unlink()
            raise HTTPException(
                status_code=400,
                detail=f"This file content already exists as '{dup}'."
            )

        # Table name
        existing = [info["table_name"] for info in FILE_REGISTRY.values()]
        table_name = derive_table_name(file.filename, existing)

        # Schema generation
        schema = generate_schema(str(file_path))
        schema_summary = generate_schema_summary(schema)


        if schema_summary:
            logger.info(f"Schema summary created succesfuly for uploaded file {file.filename}")
        else:
            logger.error(f"Failed to generate schema summary for uploaded file {file.filename}")
            raise HTTPException(status_code=500, detail="Failed to generate schema summary")
            

        temp_schema_file = SCHEMA_DIR / f"{file_id}.tmp"
        with open(temp_schema_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
        schema_file = SCHEMA_DIR / f"{file_id}.json"
        temp_schema_file.replace(schema_file)

        # Metadata save
        metadata = {
            "original_filename": file.filename,
            "file_id": file_id,
            "table_name": table_name,
            "file_hash": file_hash,
            "uploaded_at": str(file_path.stat().st_mtime)
        }
        temp_metadata_file = METADATA_DIR / f"{file_id}.tmp"
        with open(temp_metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        metadata_file = METADATA_DIR / f"{file_id}.json"
        temp_metadata_file.replace(metadata_file)

        # Load to DB
        try:
            row_count, col_count = load_file_to_db(str(file_path), table_name)
        except Exception as e:
            file_path.unlink()
            schema_file.unlink()
            metadata_file.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to load file: {e}")

        # Update registry
        FILE_REGISTRY[file_id] = {
            "file_id": file_id,
            "original_filename": file.filename,
            "table_name": table_name,
            "file_path": str(file_path),
            "file_hash": file_hash,
            "schema": schema,
            "uploaded_at": metadata["uploaded_at"]
        }

        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "table_name": table_name,
            "schema": schema,
            "schema_summary": schema_summary,
            "total_files": len(FILE_REGISTRY),
            "max_files": MAX_FILES
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

# =============================== 2. FILE STATUS ===============================
@router.get("/file-status")
async def file_status():
    """Quick summary of uploaded files."""

    logger.info("File status check request received.")

    if not FILE_REGISTRY:
        return {
            "status": "success",
            "has_files": False,
            "files": [],
            "total_files": 0,
            "max_files": MAX_FILES
        }

    files = [
        {
            "file_id": info["file_id"],
            "filename": info["original_filename"],
            "table_name": info["table_name"],
            "file_path": info["file_path"],
            "schema": info.get("schema"),
            "uploaded_at": info["uploaded_at"],
        }
        for info in FILE_REGISTRY.values()
    ]

    return {
        "status": "success",
        "has_files": True,
        "files": files,
        "total_files": len(files),
        "max_files": MAX_FILES
    }


# =============================== 4. DELETE A SINGLE FILE ===============================
@router.delete("/file/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and clean DB, metadata, schema, registry."""
    
    logger.info(f"File deletion request received for ID: {file_id}")

    if file_id not in FILE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"File ID '{file_id}' not found")

    data = FILE_REGISTRY[file_id]
    table_name = data["table_name"]

    # DB cleanup
    try:
        remove_table_from_db(table_name)
    except Exception as e:
        logger.error(f"Failed to drop table {table_name}: {e}")

    # Delete physical files
    path = Path(data["file_path"])
    if path.exists():
        path.unlink()

    schema_file = SCHEMA_DIR / f"{file_id}.json"
    if schema_file.exists():
        schema_file.unlink()

    metadata_file = METADATA_DIR / f"{file_id}.json"
    if metadata_file.exists():
        metadata_file.unlink()

    del FILE_REGISTRY[file_id]

    return {
        "status": "success",
        "message": f"File '{data['original_filename']}' deleted successfully",
        "file_id": file_id,
        "total_files": len(FILE_REGISTRY),
        "max_files": MAX_FILES
    }

# =============================== 5. DELETE ALL FILES ===============================
@router.delete("/files/all")
async def delete_all_files():
    """Delete all uploaded files and clear registry."""
    
    logger.info("File deletion request received for all files")

    if not FILE_REGISTRY:
        return {"status": "success", "message": "No files to delete", "deleted_count": 0}

    ids = list(FILE_REGISTRY.keys())
    for fid in ids:
        await delete_file(fid)

    return {
        "status": "success",
        "message": f"Successfully deleted {len(ids)} file(s)",
        "deleted_count": len(ids)
    }
