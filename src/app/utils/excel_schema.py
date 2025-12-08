# =============================== FILE PURPOSE ===============================
"""
This file contains helper functions that:

- Read Excel/CSV files
- Analyze columns and detect data types
- Build a schema for each sheet/table
- Prepare a summary of rows, columns, and tables
- Convert numpy types into Python types for safe JSON output

This file does not handle API requests. It is used by the schema API and file manager.
"""


# =============================== IMPORTS ===============================
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.app.configs.logger_config import get_logger

# =============================== LOGGER ===============================
logger = get_logger("Utils-Service-Excel-Schema")


# =============================== NUMPY TYPE CONVERSION ===============================
def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to normal Python types so they can be returned as JSON."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    if pd.isna(obj):
        return None
    return obj


# =============================== SQL TYPE INFERENCE ===============================
def infer_sql_type(pandas_dtype: str, series: pd.Series) -> str:
    """Decide the SQL type based on pandas datatype and column values."""
    dtype_str = str(pandas_dtype).lower()

    if "int" in dtype_str:
        if series.nunique() == 2 and set(series.dropna().unique()).issubset({0, 1}):
            return "BOOLEAN"
        return "INTEGER"

    if "float" in dtype_str:
        return "REAL"

    if "bool" in dtype_str:
        return "BOOLEAN"

    if "datetime" in dtype_str or "date" in dtype_str:
        return "DATETIME"

    if "time" in dtype_str:
        return "TIME"

    return "TEXT"


# =============================== COLUMN ANALYSIS ===============================
def analyze_column(series: pd.Series, column_name: str) -> Dict[str, Any]:
    """Analyze one column and return key information about it."""
    sql_type = infer_sql_type(str(series.dtype), series)

    total_count = len(series)
    null_count = int(series.isna().sum())
    null_percentage = (null_count / total_count * 100) if total_count > 0 else 0
    unique_count = int(series.nunique())

    # Collect up to 3 sample values
    sample_values = []
    non_null_series = series.dropna()
    if len(non_null_series) > 0:
        sample_values = non_null_series.iloc[:min(3, len(non_null_series))].tolist()

    is_potential_pk = (
        unique_count == total_count and null_count == 0 and total_count > 0
    )

    # Clean sample values
    cleaned_samples = []
    for val in sample_values:
        if pd.isna(val):
            continue
        try:
            if hasattr(val, "item"):
                val = val.item()
            cleaned_samples.append(str(val))
        except Exception:
            continue

    return {
        "name": str(column_name),
        "type": sql_type,
        "nullable": null_count > 0,
        "null_count": null_count,
        "null_percentage": round(null_percentage, 2),
        "unique_count": unique_count,
        "total_count": total_count,
        "sample_values": cleaned_samples,
        "is_potential_primary_key": is_potential_pk,
    }


# =============================== FILE READER ===============================
def read_excel_file(file_path: str) -> Dict[str, pd.DataFrame]:
    """Read a CSV or Excel file and return all sheets as DataFrames."""
    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".csv":
        logger.info(f"Reading CSV file: {file_path}")
        df = pd.read_csv(file_path, low_memory=False)
        return {"Sheet1": df}

    if file_ext in [".xlsx", ".xls"]:
        logger.info(f"Reading Excel file: {file_path}")
        engine = "openpyxl" if file_ext == ".xlsx" else "xlrd"
        return pd.read_excel(file_path, sheet_name=None, engine=engine)

    raise ValueError(f"Unsupported file type: {file_ext}")


# =============================== SCHEMA GENERATION ===============================
def generate_schema(file_path: str) -> Dict[str, Any]:
    """Generate a complete schema for a given Excel/CSV file."""
    try:
        file_path_obj = Path(file_path)
        file_name = file_path_obj.name

        logger.info(f"Starting schema generation for uploaded file: {file_name}")

        sheets_data = read_excel_file(file_path)

        tables = []
        total_rows = 0
        total_columns = 0

        for sheet_name, df in sheets_data.items():
            df.columns = df.columns.str.strip().str.replace(" ", "_", regex=False)

            columns = []
            for col_name in df.columns:
                columns.append(analyze_column(df[col_name], col_name))

            tables.append({
                "name": sheet_name,
                "row_count": int(len(df)),
                "column_count": int(len(df.columns)),
                "columns": columns,
            })

            total_rows += len(df)
            total_columns += len(df.columns)

        schema = {
            "file_path": str(file_path),
            "file_name": file_name,
            "file_type": file_path_obj.suffix.lower(),
            "tables": tables,
            "summary": {
                "total_tables": len(tables),
                "total_rows": total_rows,
                "total_columns": total_columns,
            },
        }

        schema = convert_numpy_types(schema)

        logger.info(
            f"Schema created for {file_name}. "
            f"Tables: {len(tables)}, Rows: {total_rows}, Columns: {total_columns}"
        )

        return schema

    except Exception as e:
        logger.error(f"Failed to generate schema for {file_path}: {e}", exc_info=True)
        raise ValueError(f"Failed to generate schema: {e}")


# =============================== SCHEMA SUMMARY ===============================
def get_schema_summary(schema: Dict[str, Any]) -> str:
    """Create a simple, readable summary for a schema."""
    summary = schema.get("summary", {})
    tables = schema.get("tables", [])

    lines = [
        f"File: {schema.get('file_name', 'Unknown')}",
        f"Type: {schema.get('file_type', 'Unknown')}",
        f"Tables: {summary.get('total_tables', 0)}",
        f"Total Rows: {summary.get('total_rows', 0)}",
        f"Total Columns: {summary.get('total_columns', 0)}",
        "",
    ]

    for table in tables:
        lines.append(f"Table: {table['name']}")
        lines.append(f"  Rows: {table['row_count']}, Columns: {table['column_count']}")

        for col in table["columns"]:
            pk = " [PK]" if col.get("is_potential_primary_key") else ""
            nulls = f" ({col['null_count']} nulls)" if col["null_count"] > 0 else ""
            lines.append(f"  - {col['name']}: {col['type']}{pk}{nulls}")

        lines.append("")

    return "\n".join(lines)
