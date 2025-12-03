"""Tool for executing SQL queries on uploaded Excel/CSV files."""

# =============================== IMPORTS ===============================
import json
import sqlite3
from pathlib import Path

import pandas as pd

from src.app.configs.logger_config import get_logger
from src.app.utils.excel_schema import read_excel_file

# =============================== LOGGER ===============================
logger = get_logger("Tool-Service-Execute-SQL")


# =============================== MAIN FUNCTION ===============================
def execute_sql(query: str) -> str:
    """
    Execute a SQL query on data from the uploaded Excel/CSV file.

    This function:
    - Finds the latest uploaded Excel/CSV file in the 'uploads' folder
    - Loads the data into an in-memory SQLite database
    - Runs the given SQL query
    - Returns the result as a JSON string
    """
    try:
        # Find the latest uploaded Excel/CSV file
        upload_dir = Path("uploads")
        file_path = None

        if upload_dir.exists():
            files = list(upload_dir.glob("*.*"))
            valid_files = [f for f in files if f.suffix.lower() in [".xlsx", ".xls", ".csv"]]

            if valid_files:
                latest_file = max(valid_files, key=lambda f: f.stat().st_mtime)
                file_path = str(latest_file)
                logger.info(f"Using uploaded file for SQL execution: {latest_file.name}")
            else:
                error_msg = "No Excel or CSV file found in the uploads folder."
                logger.error(error_msg)
                return json.dumps({
                    "success": False,
                    "error": error_msg,
                    "data": [],
                    "row_count": 0,
                    "columns": [],
                })
        else:
            error_msg = "Uploads folder not found."
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "data": [],
                "row_count": 0,
                "columns": [],
            })

        # Check that the file still exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "data": [],
                "row_count": 0,
                "columns": [],
            })

        logger.info(f"Starting SQL execution on file: {file_path_obj.name}")
        logger.debug(f"SQL query: {query}")

        # Read data from Excel/CSV
        sheets_data = read_excel_file(file_path)

        # Create in-memory SQLite database
        conn = sqlite3.connect(":memory:")

        # Load each sheet as a table
        for sheet_name, df in sheets_data.items():
            df.columns = df.columns.str.strip().str.replace(" ", "_", regex=False)
            df.to_sql(sheet_name, conn, index=False, if_exists="replace")
            logger.debug(
                f"Loaded table '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns"
            )

        # Run the query
        cursor = conn.cursor()
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
