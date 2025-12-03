"""
Schema Router

This file exposes API endpoints to work with schema information.
It does NOT generate schema itself. It only:

- Returns the stored schema for the uploaded file
- Regenerates schema if the stored one is missing
- Handles user requests related to schema
- Sends back schema data as API responses

The actual schema generation logic lives in 'excel_schema.py'.
"""


# =============================== IMPORTS ===============================
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from src.app.utils.excel_schema import generate_schema, get_schema_summary
from src.app.configs.logger_config import get_logger
from src.app.api.file_manager import CURRENT_FILE_ID, CURRENT_SCHEMA, UPLOAD_DIR

# =============================== LOGGER ===============================
logger = get_logger("Schema-Api-Service")

# =============================== ROUTER ===============================
router = APIRouter(prefix="/api/schema", tags=["schema"])


# =============================== GET CURRENT SCHEMA ===============================
@router.get("/current")
async def get_schema():
    """Return the schema for the uploaded file (using stored schema if available)."""

    logger.info("Schema request received for the uploaded file.")

    try:
        # Check if file exists
        if not CURRENT_FILE_ID:
            logger.warning("Schema request stopped. No file has been uploaded.")
            raise HTTPException(status_code=404, detail="No file uploaded")

        # Return stored schema if available
        if CURRENT_SCHEMA:
            logger.info(f"Returning existing schema for file ID: {CURRENT_FILE_ID}")
            schema_summary = get_schema_summary(CURRENT_SCHEMA)

            return JSONResponse({
                "status": "success",
                "schema": CURRENT_SCHEMA,
                "schema_summary": schema_summary,
                "cached": True
            })

        # If stored schema missing → regenerate
        logger.warning("Stored schema not found. Regenerating schema...")

        file_path = None
        for file in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
            file_path = file
            break

        if not file_path or not file_path.exists():
            logger.warning(f"Schema generation failed. File not found for ID: {CURRENT_FILE_ID}")
            raise HTTPException(status_code=404, detail="File not found")

        logger.info(f"Generating new schema for file: {file_path.name}")
        schema = generate_schema(str(file_path))
        schema_summary = get_schema_summary(schema)

        logger.info("Schema generated successfully.")

        return JSONResponse({
            "status": "success",
            "schema": schema,
            "schema_summary": schema_summary,
            "cached": False
        })

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Schema request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {e}")


# =============================== ANALYZE FILE ===============================
@router.post("/analyze")
async def analyze_file(file_path: str):
    """Analyze a file and return its schema."""

    logger.info(f"Schema analysis requested for file: {file_path}")

    try:
        path_obj = Path(file_path)

        # Check if file exists
        if not path_obj.exists():
            logger.warning(f"Schema analysis failed. File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")

        logger.info(f"Analyzing file: {path_obj.name}")
        schema = generate_schema(str(path_obj))
        schema_summary = get_schema_summary(schema)

        logger.info(f"Schema analysis completed for file: {path_obj.name}")

        return JSONResponse({
            "status": "success",
            "schema": schema,
            "schema_summary": schema_summary
        })

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Schema analysis failed for {file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {e}")
