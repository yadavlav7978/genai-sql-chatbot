# =============================== FILE PURPOSE ===============================
"""
Health API Endpoint - Provides a simple health check endpoint for the API.

This module provides:
- GET /api/health: Health check endpoint
"""

# =============================== IMPORTS ===============================
from fastapi import APIRouter
from src.app.configs.logger_config import get_logger

logger = get_logger("Health-Api-Service")

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    """Health check endpoint to verify API is running."""
    logger.info("Health check requested")
    return {"status": "healthy"}
