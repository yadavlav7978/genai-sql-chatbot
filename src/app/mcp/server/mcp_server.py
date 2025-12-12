import sys
from pathlib import Path

# Navigate up to genai-sql-chatbot directory (5 levels up from mcp_server.py)
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

import json
import sqlite3
from src.app.utils.database_manager import get_db_connection, get_all_table_names
from src.app.configs.logger_config import get_logger
# Import with aliases to avoid naming conflicts with wrapper functions
from src.app.mcp.tools import execute_sql_query, get_schema_summary

logger = get_logger("Mcp-Server")


#Initialize FastMcp instance
mcp = FastMCP("Sql_Chatbot_Mcp_Server")


@mcp.tool()
def execute_sql(query: str) -> str:
    '''Execute a SQL query on data from the persistent database.'''
    logger.info("Calling execute_sql tool from mcp server")
    return execute_sql_query(query)  # Call the actual implementation


@mcp.tool()
def get_schema():
    '''Retrieve schemas for all tables currently available in the database.'''
    logger.info("Calling get_schema tool from mcp server")
    return get_schema_summary()  # Call the actual implementation

#Run the MCP Server
if __name__ == "__main__":
    logger.info("Starting SQL Chatbot MCP server on http://127.0.0.1:8001")
    mcp.run(transport="sse", host="127.0.0.1", port=8001)
