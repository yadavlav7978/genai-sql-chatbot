# =============================== FILE PURPOSE ===============================
"""
Session Service - Manages chat sessions using an in-memory session store.

This module provides:
- Initialization of InMemorySessionService
- Session management for the chatbot application
"""

# =============================== IMPORTS ===============================
from google.adk.sessions import InMemorySessionService
from src.app.configs.logger_config import get_logger

logger = get_logger("session_service")

# Initialize session service
session_service = InMemorySessionService()

logger.info("Session service initialized successfully")