# =============================== FILE PURPOSE ===============================
"""
API Key Configuration - Manages the loading and configuration of external API keys (e.g., Azure OpenAI).

This module provides:
- Loading environment variables
- Configuring Azure OpenAI credentials
- Validation of required API keys
"""

# =============================== IMPORTS ===============================
from dotenv import load_dotenv
import os
from src.app.configs.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("API-Key-Service" )




# =============================== API KEY CONFIG ===============================
def configure_api_key():
    """Configure Google API key from environment variables."""
    logger.info("Configuring Azure OpenAI credentials...")

    api_key = os.getenv("API_KEY")
    api_endpoint = os.getenv("API_ENDPOINT")
    api_version = os.getenv("API_VERSION")

    if not api_key:
        logger.error("❌ API_KEY missing in environment variables.")
        return False
    if not api_endpoint:
        logger.error("❌ API_ENDPOINT missing in environment variables.")
        return False
    if not api_version:
        logger.error("❌ API_VERSION missing in environment variables.")
        return False

    os.environ["AZURE_API_KEY"] = api_key
    os.environ["AZURE_API_BASE"] = api_endpoint
    os.environ["AZURE_API_VERSION"] = api_version

    logger.info("✅ Azure OpenAI credentials loaded successfully.")
    return True