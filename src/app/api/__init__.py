"""API routes module."""
from .chat import router as chat_router
from .health import router as health_router
from .file_manager import router as file_manager_router

__all__ = ["chat_router", "health_router", "file_manager_router"]
