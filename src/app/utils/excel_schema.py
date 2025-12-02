"""Utility functions for reading Excel files and generating schema representations."""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.app.configs.logger_config import get_logger

logger = get_logger("excel_schema")


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    
    Args:
        obj: Object that may contain numpy types
        
    Returns:
        Object with numpy types converted to Python native types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif pd.isna(obj):
        return None
    else:
        return obj


def infer_sql_type(pandas_dtype: str, series: pd.Series) -> str:
    """
    Infer SQL data type from pandas dtype and actual data.
    
    Args:
        pandas_dtype: Pandas dtype string
        series: Pandas Series to analyze
        
    Returns:
        SQL type string
    """
    dtype_str = str(pandas_dtype).lower()
    
    # Integer types
    if 'int' in dtype_str:
        # Check if it's boolean-like (0/1)
        if series.nunique() == 2 and set(series.dropna().unique()).issubset({0, 1}):
            return 'BOOLEAN'
        return 'INTEGER'
    
    # Float types
    if 'float' in dtype_str:
        return 'REAL'
    
    # Boolean types
    if 'bool' in dtype_str:
        return 'BOOLEAN'
    
    # DateTime types
    if 'datetime' in dtype_str or 'date' in dtype_str:
        return 'DATETIME'
    
    # Time types
    if 'time' in dtype_str:
        return 'TIME'
    
    # String/Text types (default)
    return 'TEXT'


def analyze_column(series: pd.Series, column_name: str) -> Dict[str, Any]:
    """
    Analyze a single column and return its metadata.
    
    Args:
        series: Pandas Series representing the column
        column_name: Name of the column
        
    Returns:
        Dictionary with column metadata
    """
    # Infer SQL type
    sql_type = infer_sql_type(str(series.dtype), series)
    
    # Calculate statistics - optimized operations
    total_count = len(series)
    null_count = int(series.isna().sum())  # Convert to int immediately
    null_percentage = (null_count / total_count * 100) if total_count > 0 else 0.0
    
    # Get unique values count - use faster method
    unique_count = int(series.nunique())
    
    # Get sample values (non-null) - limit to 3 for performance
    # Use iloc for faster access instead of head()
    sample_values = []
    non_null_series = series.dropna()
    if len(non_null_series) > 0:
        # Take first 3 non-null values for performance
        sample_count = min(3, len(non_null_series))
        sample_values = non_null_series.iloc[:sample_count].tolist()
    
    # Check if column could be a primary key (all unique, no nulls)
    # Use faster comparison
    is_potential_pk = (unique_count == total_count and null_count == 0 and total_count > 0)
    
    # Convert numpy types to Python native types for JSON serialization
    nullable = bool(null_count > 0)
    is_pk = bool(is_potential_pk)
    
    # Convert sample values to strings, handling numpy types - optimized
    sample_vals = []
    for val in sample_values:
        if pd.isna(val):
            continue
        # Convert numpy types to Python native types
        try:
            if hasattr(val, 'item'):  # numpy scalar
                val = val.item()
            sample_vals.append(str(val))
        except (ValueError, TypeError):
            # Skip problematic values
            continue
    
    return {
        "name": str(column_name),
        "type": sql_type,
        "nullable": nullable,
        "null_count": int(null_count),
        "null_percentage": float(round(null_percentage, 2)),
        "unique_count": int(unique_count),
        "total_count": int(total_count),
        "sample_values": sample_vals,
        "is_potential_primary_key": is_pk
    }


def read_excel_file(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Read Excel file and return dictionary of sheet names to DataFrames.
    Optimized for performance with large files.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Dictionary mapping sheet names to DataFrames
    """
    file_path_obj = Path(file_path)
    file_ext = file_path_obj.suffix.lower()
    
    if file_ext == '.csv':
        # Read CSV file with optimized settings
        # Use low_memory=False for better type inference, but nrows for very large files
        df = pd.read_csv(file_path, low_memory=False, nrows=None)
        return {"Sheet1": df}  # CSV files have no sheets, use default name
    elif file_ext in ['.xlsx', '.xls']:
        # Read Excel file (all sheets) with optimized engine
        engine = 'openpyxl' if file_ext == '.xlsx' else 'xlrd'
        excel_data = pd.read_excel(file_path, sheet_name=None, engine=engine)
        return excel_data
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def generate_schema(file_path: str) -> Dict[str, Any]:
    """
    Read an Excel/CSV file and generate a comprehensive schema representation.
    
    Args:
        file_path: Path to the Excel/CSV file
        
    Returns:
        Dictionary containing schema information with the following structure:
        {
            "file_path": str,
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
                            "type": str,
                            "nullable": bool,
                            "null_count": int,
                            "null_percentage": float,
                            "unique_count": int,
                            "total_count": int,
                            "sample_values": List[str],
                            "is_potential_primary_key": bool
                        }
                    ]
                }
            ],
            "summary": {
                "total_tables": int,
                "total_rows": int,
                "total_columns": int
            }
        }
    """
    try:
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name
        file_ext = file_path_obj.suffix.lower()
        
        # Read the file
        sheets_data = read_excel_file(file_path)
        
        tables = []
        total_rows = 0
        total_columns = 0
        
        # Process each sheet/table
        for sheet_name, df in sheets_data.items():
            # Clean column names (remove extra spaces, replace spaces with underscores)
            # Use vectorized operations for better performance
            df.columns = df.columns.str.strip().str.replace(' ', '_', regex=False)
            
            columns = []
            # Process columns in batch for better performance
            for col_name in df.columns:
                column_info = analyze_column(df[col_name], col_name)
                columns.append(column_info)
            
            table_info = {
                "name": sheet_name,
                "row_count": int(len(df)),
                "column_count": int(len(df.columns)),
                "columns": columns
            }
            
            tables.append(table_info)
            total_rows += len(df)
            total_columns += len(df.columns)
        
        schema = {
            "file_path": str(file_path),
            "file_name": file_name,
            "file_type": file_ext,
            "tables": tables,
            "summary": {
                "total_tables": int(len(tables)),
                "total_rows": int(total_rows),
                "total_columns": int(total_columns)
            }
        }
        
        # Convert all numpy types to Python native types for JSON serialization
        schema = convert_numpy_types(schema)
        
        logger.info(
            f"Schema generated successfully for {file_name}: "
            f"{len(tables)} table(s), {total_rows:,} row(s), {total_columns} column(s)"
        )
        return schema
        
    except Exception as e:
        logger.error(f"Error generating schema for {file_path}: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate schema: {str(e)}")


def get_schema_summary(schema: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the schema.
    
    Args:
        schema: Schema dictionary from generate_schema()
        
    Returns:
        Formatted string summary
    """
    summary = schema.get("summary", {})
    tables = schema.get("tables", [])
    
    lines = [
        f"File: {schema.get('file_name', 'Unknown')}",
        f"Type: {schema.get('file_type', 'Unknown')}",
        f"Tables: {summary.get('total_tables', 0)}",
        f"Total Rows: {summary.get('total_rows', 0):,}",
        f"Total Columns: {summary.get('total_columns', 0)}",
        ""
    ]
    
    for table in tables:
        lines.append(f"Table: {table['name']}")
        lines.append(f"  Rows: {table['row_count']:,}, Columns: {table['column_count']}")
        for col in table['columns']:
            pk_marker = " [PK]" if col.get('is_potential_primary_key') else ""
            null_info = f" ({col['null_count']} nulls)" if col['null_count'] > 0 else ""
            lines.append(f"  - {col['name']}: {col['type']}{pk_marker}{null_info}")
        lines.append("")
    
    return "\n".join(lines)

