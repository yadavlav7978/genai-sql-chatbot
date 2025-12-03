# =============================== IMPORTS ===============================
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import json
from typing import Optional

from src.app.configs.logger_config import get_logger
from src.app.utils.excel_schema import generate_schema, get_schema_summary

# =============================== LOGGER ===============================
logger = get_logger("File-Manager-Api-Service")

# =============================== ROUTER ===============================
router = APIRouter(prefix="/api", tags=["file-manager"])

# =============================== DIRECTORIES ===============================
UPLOAD_DIR = Path("uploads")
SCHEMA_DIR = Path("schemas")

UPLOAD_DIR.mkdir(exist_ok=True)
SCHEMA_DIR.mkdir(exist_ok=True)

logger.info(f"Upload folder is ready at this path: {UPLOAD_DIR.resolve()}")
logger.info(f"Schema folder is ready at this path: {SCHEMA_DIR.resolve()}")

# =============================== GLOBAL STATE ===============================
CURRENT_FILE_ID: Optional[str] = None
CURRENT_FILENAME: Optional[str] = None
CURRENT_SCHEMA: Optional[dict] = None


# =============================== STARTUP CHECK ===============================
def check_file_on_startup():
    """Check for existing files and load metadata on startup."""
    global CURRENT_FILE_ID, CURRENT_FILENAME, CURRENT_SCHEMA

    logger.info("Checking for uploaded files on startup...")

    files = list(UPLOAD_DIR.glob("*.*"))
    if not files:
        logger.info("No uploaded files found during startup.")
        return

    # Sort files by last modified time
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest_file = files[0]

    # If more than 1 file exists → clean older ones
    if len(files) > 1:
        logger.warning(f"{len(files)} files found. Keeping the latest file and removing others.")
        for f in files[1:]:
            f.unlink()
            logger.info(f"Removed old file: {f.name}")

    CURRENT_FILE_ID = latest_file.stem
    CURRENT_FILENAME = latest_file.name

    # Load existing schema if present
    schema_file = SCHEMA_DIR / f"{CURRENT_FILE_ID}.json"
    if schema_file.exists():
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                CURRENT_SCHEMA = json.load(f)
            logger.info(f"Loaded existing schema for file: {CURRENT_FILENAME}")
        except Exception as e:
            logger.warning(f"Failed to load existing schema: {e}")
            CURRENT_SCHEMA = None

    logger.info(f"Startup completed with file: {CURRENT_FILENAME} (ID: {CURRENT_FILE_ID})")


# =============================== FILE UPLOAD ===============================
@router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload an Excel/CSV file, generate schema, and replace existing file."""
    logger.info(f"Upload request received for file: {file.filename}")

    try:
        allowed_extensions = {".xlsx", ".xls", ".csv"}
        file_ext = Path(file.filename).suffix.lower()

        # Validate file type
        if file_ext not in allowed_extensions:
            logger.warning(f"Upload rejected. File type '{file_ext}' is not supported.")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types are: {', '.join(allowed_extensions)}"
            )

        global CURRENT_FILE_ID, CURRENT_FILENAME, CURRENT_SCHEMA

        # Remove old files and schemas
        old_files = list(UPLOAD_DIR.glob("*.*"))
        old_schemas = list(SCHEMA_DIR.glob("*.json"))

        if old_files or old_schemas:
            logger.info(f"Removing {len(old_files)} old file(s) and {len(old_schemas)} existing schema(s).")

        for f in old_files:
            f.unlink()
            logger.info(f"Removed old file: {f.name}")

        for s in old_schemas:
            s.unlink()
            logger.info(f"Removed old schema: {s.name}")

        # Save new file
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        logger.info(f"Saving new file as: {file_path.name}")

        with open(file_path, "wb") as f:
            while chunk := await file.read(8192):
                f.write(chunk)

        logger.info(f"File saved successfully: {file.filename} (ID: {file_id})")

        # Generate schema
        logger.info("Generating schema for the uploaded file...")
        schema = generate_schema(str(file_path))
        schema_summary = get_schema_summary(schema)

        # Save schema
        schema_file = SCHEMA_DIR / f"{file_id}.json"
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        logger.info("Schema created and stored successfully.")

        # Update global state
        CURRENT_FILE_ID = file_id
        CURRENT_FILENAME = file.filename
        CURRENT_SCHEMA = schema

        logger.info(f"Upload completed. File '{file.filename}' stored with ID: {file_id}")

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
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


# =============================== FILE STATUS ===============================
@router.get("/file-status")
async def file_status():
    """Return status of the currently uploaded file."""
    logger.info("File status request received.")

    try:
        if CURRENT_FILE_ID:
            for file in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
                logger.info(f"File found: {CURRENT_FILENAME}")
                return {
                    "status": "success",
                    "has_file": True,
                    "file_id": CURRENT_FILE_ID,
                    "filename": CURRENT_FILENAME,
                    "file_path": str(file)
                }

        logger.info("No file has been uploaded yet.")
        return {"status": "success", "has_file": False}

    except Exception as e:
        logger.error(f"File status check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================== DELETE FILE ===============================
@router.delete("/file")
async def delete_file():
    """Delete uploaded file and its schema."""
    logger.info("File delete request received.")

    global CURRENT_FILE_ID, CURRENT_FILENAME, CURRENT_SCHEMA

    try:
        if not CURRENT_FILE_ID:
            logger.warning("Delete request failed. No file is uploaded.")
            raise HTTPException(status_code=404, detail="No file uploaded")

        deleted_file = CURRENT_FILENAME
        deleted_id = CURRENT_FILE_ID

        # Delete file
        for f in UPLOAD_DIR.glob(f"{deleted_id}.*"):
            f.unlink()
            logger.info(f"Deleted file: {f.name}")

        # Delete schema
        schema_file = SCHEMA_DIR / f"{deleted_id}.json"
        if schema_file.exists():
            schema_file.unlink()
            logger.info(f"Deleted schema: {schema_file.name}")

        # Reset global state
        CURRENT_FILE_ID = None
        CURRENT_FILENAME = None
        CURRENT_SCHEMA = None

        logger.info(f"File and schema deleted successfully: {deleted_file}")

        return {"status": "success", "message": "File and schema deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
