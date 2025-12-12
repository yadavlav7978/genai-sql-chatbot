from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

from src.app.configs.logger_config import get_logger


logger = get_logger("Mcp-Toolset")


def get_mcp_toolset() -> McpToolset:
    """
    Initialize and return the MCP toolset with SSE connection.
    
    Returns:
        McpToolset: Configured MCP toolset instance
    """
    try:
        logger.info("Initializing McpToolset with SSE connection to MCP server")
        mcp_toolset = McpToolset(
            connection_params=SseConnectionParams(
                url='http://127.0.0.1:8001/sse',
                timeout=5.0,
                sse_read_timeout=300.0
            ),
            tool_name_prefix="",
            require_confirmation=False
        )
        logger.info("McpToolset initialized successfully")
        return mcp_toolset
    except Exception as e:
        logger.error(f"Failed to initialize McpToolset: {str(e)}", exc_info=True)
        raise
