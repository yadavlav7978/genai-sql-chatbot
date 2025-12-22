
# =============================== IMPORTS ===============================
import json
import sqlite3

from src.app.configs.logger_config import get_logger
from src.app.utils.database_manager import get_db_connection, get_all_table_names

# =============================== LOGGER ===============================
logger = get_logger("MCPTool-Service-Execute-SQL")


# =============================== MAIN FUNCTION ===============================
def execute_sql_query(query: str) -> str:
    """
    Execute a SQL query on data from the persistent database.
    
    This function:
    - Connects to the persistent SQLite database
    - Runs the given SQL query
    - Returns the result as a JSON string
    
    Args:
        query: SQL SELECT query to execute
        
    Returns:
        str: JSON string with structure:
             {
               "success": bool,
               "data": list of dicts (rows),
               "row_count": int,
               "columns": list of column names,
               "error": str (if success is False)
             }
    """
    try:
        # Check if there are any tables in the database
        tables = get_all_table_names()
        
        if not tables:
            error_msg = "No tables found in database. Please upload at least one Excel or CSV file first."
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "data": [],
                "row_count": 0,
                "columns": [],
            })
        
        logger.info(f"Executing SQL query...")
        logger.debug(f"Available tables in database: {tables}")
        
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Build result rows as list of dicts
        data = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                row_dict[col_name] = value if value is not None else None
            data.append(row_dict)
        
        conn.close()
        
        result = {
            "success": True,
            "data": data,
            "row_count": len(data),
            "columns": columns,
        }
        
        logger.info(
            f"SQL query executed successfully. Rows returned: {len(data)}, Columns: {len(columns)}"
        )
        
        return json.dumps(result, indent=2)
    
    except sqlite3.Error as e:
        error_msg = f"SQL error while running query: {e}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "data": [],
            "row_count": 0,
            "columns": [],
        })
    
    except Exception as e:
        error_msg = f"Unexpected error during SQL execution: {e}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "data": [],
            "row_count": 0,
            "columns": [],
        })
