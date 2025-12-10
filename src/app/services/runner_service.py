# =============================== FILE PURPOSE ===============================
"""
Runner Service - Initializes and manages the Google ADK Runner for executing agents.

This module provides:
- Initialization of the ADK Runner with the Orchestrator Agent
- Integration with Session Service
"""

# =============================== IMPORTS ===============================
from google.adk.runners import Runner
from src.app.agents import orchestrator_agent
from src.app.services import session_service
from src.app.configs.logger_config import get_logger

logger = get_logger("runner_service")

# Initialize ADK Runner
runner = Runner(
    agent=orchestrator_agent,
    app_name="sql-chatbot",
    session_service=session_service
)

logger.info("ADK Runner initialized successfully")