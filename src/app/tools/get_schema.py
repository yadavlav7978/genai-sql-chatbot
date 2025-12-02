"""Tool for retrieving database schema information."""
import json
from pathlib import Path

from src.app.configs.logger_config import get_logger

logger = get_logger("get_schema")


def get_schema() -> str:
    """
    Retrieve the current database schema from uploaded Excel/CSV file.
    
    This function fetches the schema information for the currently uploaded file,
    which includes details about tables, columns, data types, and sample values.
    
    Returns:
        str: JSON string containing the schema information with the following structure:
             {
                 "success": bool,
                 "schema": {
                     "file_name": str,
                     "file_type": str,
                     "tables": [
                         {
                             "name": str,
                             "row_count": int,
                             "column_count": int,
                             "columns": [
                                 {
                                     "name": str,
                                     "type": str (INTEGER, TEXT, REAL, BOOLEAN, etc.),
                                     "nullable": bool,
                                     "sample_values": List[str]
                                 }
                             ]
                         }
                     ]
                 },
                 "error": str (only if success is False)
             }
             
    Example:
        >>> schema = get_schema()
        >>> print(schema)
        {"success": true, "schema": {...}}
    """
    try:
        # Import here to avoid circular imports
        from src.app.api.file_manager import CURRENT_SCHEMA, CURRENT_FILE_ID
        
        if not CURRENT_FILE_ID:
            error_msg = "No file has been uploaded. Please upload an Excel or CSV file first."
            logger.warning(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "schema": None
            })
        
        if not CURRENT_SCHEMA:
            # Try to load from cached schema file
            schema_dir = Path("schemas")
            schema_file = schema_dir / f"{CURRENT_FILE_ID}.json"
            
            if schema_file.exists():
                try:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                    logger.info(f"Loaded cached schema from {schema_file.name}")
                except Exception as e:
                    error_msg = f"Failed to load cached schema: {str(e)}"
                    logger.error(error_msg)
                    return json.dumps({
                        "success": False,
                        "error": error_msg,
                        "schema": None
                    })
            else:
                error_msg = "Schema not found. Please re-upload the file."
                logger.error(error_msg)
                return json.dumps({
                    "success": False,
                    "error": error_msg,
                    "schema": None
                })
        else:
            schema = CURRENT_SCHEMA
        
        logger.info(f"Retrieved schema for file: {schema.get('file_name', 'Unknown')}")
        
        return json.dumps({
            "success": True,
            "schema": schema
        }, indent=2)
        
    except Exception as e:
        error_msg = f"Unexpected error retrieving schema: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "schema": None
        })


# Example usage for testing
if __name__ == "__main__":
    result = get_schema()
    print(result)
