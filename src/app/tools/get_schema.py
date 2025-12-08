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
from src.app.api.file_manager import CURRENT_SCHEMA
from src.app.utils.excel_schema import get_schema_summary
# =============================== LOGGER ===============================
logger = get_logger("Tool-Service-get-schema")


# =============================== GET SCHEMA FUNCTION ===============================
def get_schema():
    try:
        from src.app.api.file_manager import CURRENT_SCHEMA
        from src.app.utils.excel_schema import get_schema_summary
        
        logger.info("Fetching schema summary for the agent context.")
        summary = get_schema_summary(CURRENT_SCHEMA)

        logger.info(f"Schema summary: {summary}")

        return json.dumps({"success": True, "error": None, "schema": summary})
    except Exception as e:
        logger.error(f"Error fetching schema summary: {str(e)}")
        return json.dumps({"success": False, "error": str(e), "schema": None})

    


