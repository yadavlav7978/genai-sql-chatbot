"""Tool for executing SQL queries against uploaded Excel/CSV files."""
import sqlite3
import pandas as pd
from pathlib import Path
import json

from src.app.configs.logger_config import get_logger
from src.app.utils.excel_schema import read_excel_file

logger = get_logger("execute_sql")


def execute_sql(query: str) -> str:
    """
    Execute a SQL query against Excel/CSV data.
    
    This function loads data from an Excel or CSV file into an in-memory SQLite database,
    executes the provided SQL query, and returns the results as a JSON string.
    
    The function automatically finds the uploaded file in the uploads directory.
    
    Args:
        query (str): The SQL query to execute (should be a SELECT statement)
        
    Returns:
        str: JSON string containing the query results with the following structure:
             {
                 "success": bool,
                 "data": List[Dict[str, Any]],  # List of rows as dictionaries
                 "row_count": int,
                 "columns": List[str],
                 "error": str (only if success is False)
             }
             
    Example:
        >>> result = execute_sql("SELECT * FROM Sheet1 LIMIT 10")
        >>> print(result)
        {"success": true, "data": [...], "row_count": 10, "columns": ["col1", "col2"]}
    """
    try:
        # Auto-detect the file from the uploads directory
        file_path = None
        upload_dir = Path("uploads")
        if upload_dir.exists():
            files = list(upload_dir.glob("*.*"))
            # Filter for valid Excel/CSV files
            valid_files = [f for f in files if f.suffix.lower() in ['.xlsx', '.xls', '.csv']]
            
            if valid_files:
                # Use the most recent file
                file_path = str(max(valid_files, key=lambda f: f.stat().st_mtime))
                logger.info(f"Auto-detected file: {file_path}")
            else:
                error_msg = "No Excel/CSV file found in uploads directory"
                logger.error(error_msg)
                return json.dumps({
                    "success": False,
                    "error": error_msg,
                    "data": [],
                    "row_count": 0,
                    "columns": []
                })
        else:
            error_msg = "Uploads directory not found"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "data": [],
                "row_count": 0,
                "columns": []
            })
        
        # Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "data": [],
                "row_count": 0,
                "columns": []
            })
        
        logger.info(f"Executing SQL query on file: {file_path}")
        logger.debug(f"Query: {query}")
        
        # Read the Excel/CSV file
        sheets_data = read_excel_file(file_path)
        
        # Create an in-memory SQLite database
        conn = sqlite3.connect(":memory:")
        
        # Load each sheet/table into the database
        for sheet_name, df in sheets_data.items():
            # Clean column names (remove extra spaces, replace spaces with underscores)
            df.columns = df.columns.str.strip().str.replace(' ', '_', regex=False)
            
            # Write DataFrame to SQLite
            df.to_sql(sheet_name, conn, index=False, if_exists='replace')
            logger.debug(f"Loaded table '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns")
        
        # Execute the query
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch results
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Convert rows to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                # Handle None/NULL values
                if value is None:
                    row_dict[col_name] = None
                else:
                    row_dict[col_name] = value
            data.append(row_dict)
        
        # Close connection
        conn.close()
        
        result = {
            "success": True,
            "data": data,
            "row_count": len(data),
            "columns": columns
        }
        
        logger.info(f"Query executed successfully. Returned {len(data)} rows with {len(columns)} columns")
        
        return json.dumps(result, indent=2)
        
    except sqlite3.Error as e:
        error_msg = f"SQL execution error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "data": [],
            "row_count": 0,
            "columns": []
        })
        
    except Exception as e:
        error_msg = f"Unexpected error during SQL execution: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "data": [],
            "row_count": 0,
            "columns": []
        })

# Example usage for testing
if __name__ == "__main__":
    # Test the function - now auto-detects uploaded file
    test_query = "SELECT * FROM Sheet1 LIMIT 5"
    
    result = execute_sql(test_query)
    print(result)
