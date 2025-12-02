"""FastAPI application entry point."""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.app.api import chat_router, schema_router, health_router, file_manager_router
from src.app.configs.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("sql-chatbot")

# Configure API key
def configure_api_key():
    """Configure Google API key from environment variables."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        logger.info("Google API key loaded successfully")
        return True
    else:
        logger.warning(
            "GOOGLE_API_KEY or GEMINI_API_KEY not found. "
            "Please set one of these in your .env file. "
            "Chat functionality will not work without an API key."
        )
        return False

# Initialize API key configuration
configure_api_key()

# Create FastAPI app
app = FastAPI(
    title="SQL ChatBot API",
    description="AI-powered SQL Chatbot using Google ADK",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(schema_router)
app.include_router(file_manager_router)
app.include_router(health_router)

# Configure file uploads directory
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting SQL ChatBot API server...")
    logger.info(f"Uploads directory: {UPLOADS_DIR.absolute()}")
    
    # Check for existing files on startup
    from src.app.api import file_manager
    file_manager.check_file_on_startup()
    
    # Verify API key on startup
    if configure_api_key():
        logger.info("Application started successfully")
    else:
        logger.error("Application started but API key is missing")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down SQL ChatBot API server...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SQL ChatBot API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.main_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

