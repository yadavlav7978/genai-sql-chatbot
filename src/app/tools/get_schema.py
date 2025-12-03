# =============================== FILE PURPOSE ===============================
"""
This file contains a helper function to fetch the current schema.

It does not generate a new schema. Instead, it:
- Returns the schema already stored in memory
- If missing, tries to load it from the 'schemas' folder
- Returns the schema in JSON format
- Handles all related errors cleanly

This is used by agents or other internal services that need schema data.
"""

# =============================== IMPORTS ===============================
import json
from pathlib import Path

from src.app.configs.logger_config import get_logger

# =============================== LOGGER ===============================
logger = get_logger("Tool-Service-get-schema")


# =============================== GET SCHEMA FUNCTION ===============================
def get_schema() -> str:
    """Return the current schema for the uploaded file."""

    try:
        from src.app.api.file_manager import CURRENT_SCHEMA, CURRENT_FILE_ID
        # Check if a file is uploaded
        if not CURRENT_FILE_ID:
            msg = "No file uploaded. Please upload an Excel or CSV file."
            logger.warning(msg)
            return json.dumps({"success": False, "error": msg, "schema": None})

        # Use the schema already in memory if available
        if CURRENT_SCHEMA:
            schema = CURRENT_SCHEMA
            logger.info(f"Returning stored schema for file: {schema.get('file_name', 'Unknown')}")
        else:
            # Try loading schema from disk
            schema_path = Path("schemas") / f"{CURRENT_FILE_ID}.json"

            if not schema_path.exists():
                msg = "Schema not found on disk. Please upload the file again."
                logger.error(msg)
                return json.dumps({"success": False, "error": msg, "schema": None})

            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                logger.info(f"Loaded existing schema from file: {schema_path.name}")
            except Exception as e:
                msg = f"Could not read schema file: {e}"
                logger.error(msg)
                return json.dumps({"success": False, "error": msg, "schema": None})

        # Return schema as JSON
        return json.dumps({"success": True, "schema": schema}, indent=2)

    except Exception as e:
        msg = f"Unexpected error retrieving schema: {e}"
        logger.error(msg, exc_info=True)
        return json.dumps({"success": False, "error": msg, "schema": None})


