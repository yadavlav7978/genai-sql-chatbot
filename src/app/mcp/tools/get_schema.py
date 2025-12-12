"""
Get Schema Tool

Purpose
-------
This module provides a tool-level function used by agents (such as MCP tools) 
to retrieve a consolidated schema overview for all tables currently registered in the SQL chatbot system.

What this file does
-------------------
- Reads all table schemas from the file registry.
- Formats them into a consistent JSON structure.
- Generates a human-readable summary of all tables.
- Acts as a helper module for agents/tools — not an API route.
"""

# =============================== IMPORTS ===============================
import json

from src.app.configs.logger_config import get_logger

# =============================== LOGGER ===============================
logger = get_logger("MCPTool-Service-get-schema")


# =============================== GET SCHEMA FUNCTION ===============================
def get_schema_summary():
    """
    Retrieve schemas for all tables currently available in the database.

    Returns:
        str: JSON string containing table schemas and a summarized overview.
    """
    try:
        # Import the shared registry function that reads from disk
        from src.app.utils.shared_registry import get_file_registry_from_disk

        logger.info("Fetching schemas for all tables in the database.")
        
        # Get FILE_REGISTRY from disk metadata instead of in-memory registry
        FILE_REGISTRY = get_file_registry_from_disk()

        if not FILE_REGISTRY:
            logger.warning("No files uploaded. Schema is empty.")
            return json.dumps({
                "success": False,
                "error": "No files have been uploaded yet. Please upload Excel or CSV files first.",
                "schema": {},
                "summary": "No tables available in the database."
            })

        all_schemas = {}
        table_summaries = []

        for file_id, file_data in FILE_REGISTRY.items():
            table_name = file_data.get("table_name")
            original_filename = file_data.get("original_filename")
            schema = file_data.get("schema")

            if not schema:
                logger.warning(f"No schema found for table '{table_name}'")
                continue

            tables = schema.get("tables", [])

            if tables:
                table_info = tables[0]

                all_schemas[table_name] = {
                    "file_name": original_filename,
                    "table_name": table_name,
                    "row_count": table_info.get("row_count", 0),
                    "column_count": table_info.get("column_count", 0),
                    "columns": table_info.get("columns", [])
                }

                columns_str = ", ".join([col["name"] for col in table_info.get("columns", [])])
                table_summaries.append(
                    f"Table: {table_name} (from file: {original_filename})\n"
                    f"  Rows: {table_info.get('row_count', 0)}, Columns: {table_info.get('column_count', 0)}\n"
                    f"  Column Names: {columns_str}"
                )

        summary = f"Database contains {len(all_schemas)} table(s):\n\n" + "\n\n".join(table_summaries)

        result = {
            "success": True,
            "error": None,
            "schema": all_schemas,
            "summary": summary,
            "total_tables": len(all_schemas)
        }

        logger.info(f"Schema summary fetched successfully: {len(all_schemas)} table(s)")

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error fetching schema summary: {str(e)}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "schema": {},
            "summary": "Failed to retrieve schema."
        })