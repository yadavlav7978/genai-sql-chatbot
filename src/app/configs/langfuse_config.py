"""
Langfuse Configuration - Manages Langfuse observability integration for Google ADK.

This module provides:
- Loading Langfuse environment variables
- Initializing Langfuse client
- Setting up OpenTelemetry instrumentation for Google ADK
- Validation of Langfuse credentials
"""

# IMPORTS
from dotenv import load_dotenv
import os
from src.app.configs.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("Langfuse-Service")


def configure_langfuse():
    """Configure Langfuse observability with OpenTelemetry instrumentation for Google ADK."""
    logger.info("Configuring Langfuse observability...")
    
    # Load Langfuse credentials from environment
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    # Validate credentials
    if not public_key:
        logger.error("LANGFUSE_PUBLIC_KEY missing in environment variables.")
        return False
    if not secret_key:
        logger.error("LANGFUSE_SECRET_KEY missing in environment variables.")
        return False
    
    # Set environment variables (ensure they're available to all modules)
    os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
    os.environ["LANGFUSE_SECRET_KEY"] = secret_key
    os.environ["LANGFUSE_BASE_URL"] = base_url
    
    # Configure OpenTelemetry to export to Langfuse
    # Langfuse expects traces at /api/public/ingestion endpoint
    otlp_endpoint = f"{base_url}/api/public/ingestion"
    
    # Set OpenTelemetry environment variables
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Bearer {public_key}.{secret_key}"
    
    logger.info(f"OpenTelemetry endpoint configured: {otlp_endpoint}")
    
    try:
        # Verify Langfuse client connection
        from langfuse import Langfuse
        
        # Initialize client with explicit parameters to avoid LiteLLM conflicts
        langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=base_url
        )
        
        if langfuse_client.auth_check():
            logger.info("Langfuse client is authenticated and ready!")
        else:
            logger.error("Langfuse authentication failed. Please check your credentials.")
            return False
        
        # Initialize OpenTelemetry instrumentation for Google ADK
        from openinference.instrumentation.google_adk import GoogleADKInstrumentor
        
        # Check if already instrumented to avoid duplicate instrumentation
        instrumentor = GoogleADKInstrumentor()
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument()
            logger.info("Google ADK OpenTelemetry instrumentation initialized successfully.")
        else:
            logger.info("Google ADK is already instrumented.")
            
        logger.info(f"Traces will be sent to: {base_url}")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import required packages: {e}")
        logger.error("Please ensure 'langfuse' and 'openinference-instrumentation-google-adk' are installed.")
        return False
    except Exception as e:
        logger.error(f"Failed to configure Langfuse: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

