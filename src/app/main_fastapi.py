"""FastAPI application entry point."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.app.api import (
    chat_router, schema_router,
    health_router, file_manager_router
)
from src.app.configs.logger_config import setup_logger
from src.app.configs.apiKey_config import configure_api_key
from src.app.api import file_manager

# Setup logger
logger = setup_logger("Main-Service")



# Initialize API key configuration
configure_api_key()


# =============================== FASTAPI INIT ===============================
logger.info("Initializing FastAPI application...")

app = FastAPI(
    title="SQL ChatBot API",
    description="AI-powered SQL Chatbot using Google ADK",
    version="1.0.0"
)


# =============================== CORS CONFIGURATION ===============================

allowed_origins = ["http://localhost:4200", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# =============================== ROUTER SETUP ===============================

app.include_router(chat_router)
app.include_router(schema_router)
app.include_router(file_manager_router)
app.include_router(health_router)



# =============================== FILE UPLOAD DIRECTORY ===============================
UPLOADS_DIR = Path("uploads")

if not UPLOADS_DIR.exists():
    logger.warning("Uploads directory not found. Creating 'uploads' folder...")
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")



# =============================== STARTUP EVENT ===============================
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 Starting SQL ChatBot API server...")

    # Check for existing files on startup
    file_manager.check_file_on_startup()

    # Verify API key on startup
    if configure_api_key():
        logger.info("🎉 Application started successfully with valid API configuration.")
    else:
        logger.error("⚠️ Application started, but API key configuration failed.")


# =============================== SHUTDOWN EVENT ===============================
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 Shutting down SQL ChatBot API server...")


# =============================== ROOT ENDPOINT ===============================
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SQL ChatBot API", "version": "1.0.0"}


# =============================== UVICORN ENTRY ===============================
if __name__ == "__main__":
    logger.info("Launching Uvicorn server...")
    import uvicorn
    uvicorn.run(
        "src.app.main_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
