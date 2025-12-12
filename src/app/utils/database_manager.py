# =============================== FILE PURPOSE ===============================
"""
Database Manager - Centralized SQLite database management for multi-table support.

This module provides:
- Persistent SQLite database connection
- Loading Excel/CSV files as tables
- Removing tables from database
- Database cleanup and rebuilding
- Table listing and management
"""

# =============================== IMPORTS ===============================
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.app.configs.logger_config import get_logger
from src.app.utils.schema_generator import read_excel_file

# =============================== LOGGER ===============================
logger = get_logger("Utils-Service-Database-Manager")

# =============================== CONSTANTS ===============================
DB_DIR = Path("database")
DB_FILE = DB_DIR / "chatbot.db"

# Create database directory if it doesn't exist
DB_DIR.mkdir(exist_ok=True)
logger.info(f"Database directory ready at: {DB_DIR.resolve()}")


# =============================== DATABASE CONNECTION ===============================
def get_db_connection() -> sqlite3.Connection:
    """
    Get connection to persistent SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(str(DB_FILE))
        logger.debug(f"Connected to database: {DB_FILE}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise


# =============================== FILE CONTENT HASH ===============================
def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of file content to detect duplicates.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: Hexadecimal hash string
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()
        logger.debug(f"Computed hash for {file_path}: {file_hash[:16]}...")
        return file_hash
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}", exc_info=True)
        raise


# =============================== LOAD FILE TO DATABASE ===============================
def load_file_to_db(file_path: str, table_name: str) -> Tuple[int, int]:
    """
    Load an Excel/CSV file into the database as a table.
    
    Args:
        file_path: Path to the Excel/CSV file
        table_name: Name to use for the table
        
    Returns:
        Tuple[int, int]: (row_count, column_count)
        
    Raises:
        ValueError: If file cannot be loaded or table name is invalid
    """
    try:
        logger.info(f"Loading file '{file_path}' as table '{table_name}' in database.")
        
        # Validate table name (alphanumeric and underscores only)
        if not table_name.replace("_", "").isalnum():
            raise ValueError(f"Invalid table name: {table_name}. Only alphanumeric and underscores allowed.")
        
        # Read the file
        sheets_data = read_excel_file(file_path)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_rows = 0
        total_columns = 0
        
        # For single-sheet files (CSV or single Excel sheet)
        if len(sheets_data) == 1:
            sheet_name, df = list(sheets_data.items())[0]
            
            # Clean column names
            df.columns = df.columns.str.strip().str.replace(" ", "_", regex=False)
            
            # Load to database
            df.to_sql(table_name, conn, index=False, if_exists="replace")
            
            total_rows = len(df)
            total_columns = len(df.columns)
            
            logger.info(f"Loaded table '{table_name}' with {total_rows} rows and {total_columns} columns")
        
        # For multi-sheet Excel files, use sheet names as suffixes
        else:
            logger.warning(
                f"File has {len(sheets_data)} sheets. "
                f"Loading all sheets with table name prefix '{table_name}_'"
            )
            
            for sheet_name, df in sheets_data.items():
                # Clean column names
                df.columns = df.columns.str.strip().str.replace(" ", "_", regex=False)
                
                # Create table name with sheet suffix
                sheet_table_name = f"{table_name}_{sheet_name}".replace(" ", "_")
                
                # Load to database
                df.to_sql(sheet_table_name, conn, index=False, if_exists="replace")
                
                total_rows += len(df)
                total_columns += len(df.columns)
                
                logger.info(
                    f"Loaded sheet '{sheet_name}' as table '{sheet_table_name}' "
                    f"with {len(df)} rows and {len(df.columns)} columns"
                )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully loaded file to database. Total: {total_rows} rows, {total_columns} columns")
        return total_rows, total_columns
        
    except Exception as e:
        logger.error(f"Failed to load file to database: {e}", exc_info=True)
        raise ValueError(f"Failed to load file to database: {e}")


# =============================== REMOVE TABLE ===============================
def remove_table_from_db(table_name: str) -> bool:
    """
    Remove a table from the database.
    
    Args:
        table_name: Name of the table to remove
        
    Returns:
        bool: True if table was removed, False if it didn't exist
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        
        if cursor.fetchone() is None:
            logger.warning(f"Table '{table_name}' does not exist in database")
            conn.close()
            return False
        
        # Drop the table
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        conn.close()
        
        logger.info(f"Removed table '{table_name}' from database")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Failed to remove table '{table_name}': {e}", exc_info=True)
        raise


# =============================== GET ALL TABLES ===============================
def get_all_table_names() -> List[str]:
    """
    Get list of all table names in the database.
    
    Returns:
        List[str]: List of table names
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.debug(f"Found {len(tables)} tables in database: {tables}")
        return tables
        
    except sqlite3.Error as e:
        logger.error(f"Failed to get table names: {e}", exc_info=True)
        return []


# =============================== CLEAR DATABASE ===============================
def clear_database() -> int:
    """
    Drop all tables from the database.
    
    Returns:
        int: Number of tables dropped
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        # Drop each table
        for table_name in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.debug(f"Dropped table: {table_name}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared database: dropped {len(tables)} tables")
        return len(tables)
        
    except sqlite3.Error as e:
        logger.error(f"Failed to clear database: {e}", exc_info=True)
        raise


# =============================== REBUILD DATABASE ===============================
def rebuild_database(file_registry: Dict[str, Dict]) -> int:
    """
    Rebuild entire database from file registry.
    
    Args:
        file_registry: Dictionary mapping file_id to file metadata
                      Each entry should have: file_path, table_name
        
    Returns:
        int: Number of files successfully loaded
    """
    try:
        logger.info(f"Rebuilding database from {len(file_registry)} files")
        
        # Clear existing database
        clear_database()
        
        # Load each file
        loaded_count = 0
        for file_id, file_info in file_registry.items():
            try:
                file_path = file_info.get("file_path")
                table_name = file_info.get("table_name")
                
                if not file_path or not table_name:
                    logger.warning(f"Skipping file {file_id}: missing file_path or table_name")
                    continue
                
                # Check if file exists
                if not Path(file_path).exists():
                    logger.warning(f"Skipping file {file_id}: file not found at {file_path}")
                    continue
                
                # Load to database
                load_file_to_db(file_path, table_name)
                loaded_count += 1
                
            except Exception as e:
                logger.error(f"Failed to load file {file_id} during rebuild: {e}", exc_info=True)
                continue
        
        logger.info(f"Database rebuild complete. Loaded {loaded_count}/{len(file_registry)} files")
        return loaded_count
        
    except Exception as e:
        logger.error(f"Failed to rebuild database: {e}", exc_info=True)
        raise


