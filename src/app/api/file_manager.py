from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import json
from typing import Optional

from src.app.configs.logger_config import get_logger
from src.app.utils.excel_schema import generate_schema, get_schema_summary

logger = get_logger("file-manager-service")

router = APIRouter(prefix="/api", tags=["file-manager"])

# Directory to store uploaded files and schemas
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

SCHEMA_DIR = Path("schemas")
SCHEMA_DIR.mkdir(exist_ok=True)

# Track current uploaded file
CURRENT_FILE_ID: Optional[str] = None
CURRENT_FILENAME: Optional[str] = None
CURRENT_SCHEMA: Optional[dict] = None


def check_file_on_startup():
    """Check for existing files on startup and load metadata."""
    global CURRENT_FILE_ID, CURRENT_FILENAME, CURRENT_SCHEMA
    
    logger.info("Checking for existing files on startup...")
    
    # Get all files in upload directory
    files = list(UPLOAD_DIR.glob("*.*"))
    
    if not files:
        logger.info("No existing files found")
        return
    
    # If multiple files exist, keep only the most recent
    if len(files) > 1:
        logger.warning(f"Found {len(files)} files, keeping only the most recent")
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        latest_file = files[0]
        
        # Delete older files
        for f in files[1:]:
            f.unlink()
            logger.info(f"Removed old file: {f.name}")
    else:
        latest_file = files[0]
    
    # Load file metadata
    file_id = latest_file.stem
    CURRENT_FILE_ID = file_id
    CURRENT_FILENAME = latest_file.name
    
    # Load cached schema if exists
    schema_file = SCHEMA_DIR / f"{file_id}.json"
    if schema_file.exists():
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                CURRENT_SCHEMA = json.load(f)
            logger.info(f"Loaded cached schema for file: {latest_file.name}")
        except Exception as e:
            logger.warning(f"Failed to load cached schema: {e}")
            CURRENT_SCHEMA = None
    
    logger.info(f"Initialized with existing file: {CURRENT_FILENAME} (ID: {file_id})")


@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload an Excel/CSV file, generate schema, and replace existing file."""
    logger.info(f"File upload request received: {file.filename}")
    try:
        allowed_extensions = {".xlsx", ".xls", ".csv"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            logger.warning(f"File upload rejected: Invalid file type {file_ext} for file {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        global CURRENT_FILE_ID, CURRENT_FILENAME, CURRENT_SCHEMA

        # Remove all old files and schemas
        old_files = list(UPLOAD_DIR.glob("*.*"))
        old_schemas = list(SCHEMA_DIR.glob("*.json"))
        
        if old_files or old_schemas:
            logger.info(f"Removing {len(old_files)} old file(s) and {len(old_schemas)} old schema(s)")
        
        for f in old_files:
            f.unlink()
        for s in old_schemas:
            s.unlink()

        # Save new file
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        logger.info(f"File saved: {file.filename} (ID: {file_id})")

        # Generate schema
        logger.info(f"Generating schema for file: {file.filename}")
        schema = generate_schema(str(file_path))
        schema_summary = get_schema_summary(schema)
        
        # Save schema to cache
        schema_file = SCHEMA_DIR / f"{file_id}.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        
        logger.info(f"Schema cached successfully: {schema.get('summary', {}).get('total_tables', 0)} tables")

        # Update global state
        CURRENT_FILE_ID = file_id
        CURRENT_FILENAME = file.filename
        CURRENT_SCHEMA = schema

        logger.info(f"File uploaded successfully: {file.filename} (ID: {file_id})")
        
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "schema": schema,
            "schema_summary": schema_summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/file-status")
async def file_status():
    """Get current uploaded file information."""
    logger.info("File status check requested")
    global CURRENT_FILE_ID, CURRENT_FILENAME
    try:
        if CURRENT_FILE_ID:
            for file in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
                logger.info(f"File status: File present - {CURRENT_FILENAME}")
                return {
                    "status": "success",
                    "has_file": True,
                    "file_id": CURRENT_FILE_ID,
                    "filename": CURRENT_FILENAME,
                    "file_path": str(file)
                }

        logger.info("File status: No file uploaded")
        return {"status": "success", "has_file": False}

    except Exception as e:
        logger.error(f"File status check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/file")
async def delete_file():
    """Delete the currently uploaded file and its cached schema."""
    logger.info("File deletion requested")
    global CURRENT_FILE_ID, CURRENT_FILENAME, CURRENT_SCHEMA
    try:
        if not CURRENT_FILE_ID:
            logger.warning("File deletion failed: No file uploaded")
            raise HTTPException(status_code=404, detail="No file uploaded")

        deleted_file = CURRENT_FILENAME
        deleted_id = CURRENT_FILE_ID
        
        # Remove file
        for f in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
            f.unlink()
            logger.info(f"Deleted file: {f.name}")
        
        # Remove cached schema
        schema_file = SCHEMA_DIR / f"{CURRENT_FILE_ID}.json"
        if schema_file.exists():
            schema_file.unlink()
            logger.info(f"Deleted cached schema: {schema_file.name}")

        # Clear global state
        CURRENT_FILE_ID = None
        CURRENT_FILENAME = None
        CURRENT_SCHEMA = None

        logger.info(f"File and schema deleted successfully: {deleted_file}")
        return {"status": "success", "message": "File and schema deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
