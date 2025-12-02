"""Schema API endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from src.app.utils.excel_schema import generate_schema, get_schema_summary
from src.app.configs.logger_config import get_logger
from src.app.api.file_manager import CURRENT_FILE_ID, CURRENT_SCHEMA, UPLOAD_DIR

logger = get_logger("schema-service")

router = APIRouter(prefix="/api/schema", tags=["schema"])


@router.get("/current")
async def get_schema():
    """
    Get schema for the current uploaded file (uses cached schema).
    
    Returns:
        Cached schema representation of the file
    """
    logger.info("Schema request for current file")
    try:
        from src.app.api.file_manager import CURRENT_FILE_ID, CURRENT_SCHEMA, UPLOAD_DIR
        
        if not CURRENT_FILE_ID:
            logger.warning("Schema request failed: No file uploaded")
            raise HTTPException(status_code=404, detail="No file uploaded")
        
        # Return cached schema if available
        if CURRENT_SCHEMA:
            logger.info(f"Serving cached schema for file ID: {CURRENT_FILE_ID}")
            schema_summary = get_schema_summary(CURRENT_SCHEMA)
            return JSONResponse({
                "status": "success",
                "schema": CURRENT_SCHEMA,
                "schema_summary": schema_summary,
                "cached": True
            })
        
        # Fallback: regenerate if cache is missing
        logger.warning("Cached schema not found, regenerating...")
        file_path = None
        for file in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
            file_path = file
            break
        
        if not file_path or not file_path.exists():
            logger.warning(f"Schema generation failed: File not found - {CURRENT_FILE_ID}")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"Generating schema for file: {file_path.name}")
        schema = generate_schema(str(file_path))
        schema_summary = get_schema_summary(schema)
        
        logger.info(f"Schema generated successfully: {schema.get('summary', {}).get('total_tables', 0)} tables")
        
        return JSONResponse({
            "status": "success",
            "schema": schema,
            "schema_summary": schema_summary,
            "cached": False
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")


@router.post("/analyze")
async def analyze_file(file_path: str):
    """
    Analyze a file and return its schema.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Schema representation
    """
    logger.info(f"File analysis requested: {file_path}")
    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            logger.warning(f"File analysis failed: File not found - {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(f"Analyzing file: {path_obj.name}")
        schema = generate_schema(str(path_obj))
        schema_summary = get_schema_summary(schema)
        
        logger.info(f"File analysis completed: {path_obj.name}")
        
        return JSONResponse({
            "status": "success",
            "schema": schema,
            "schema_summary": schema_summary
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File analysis failed for {file_path}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")

