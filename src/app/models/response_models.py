"""Response models for API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


class ChatResponse(BaseModel):
    """Chat response model for AI responses."""
    
    status: str = Field(..., description="Response status")
    explanation: str = Field(..., description="AI explanation text")
    query_result: Optional[str] = Field(None, description="SQL query execution result")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    error: Optional[str] = Field(None, description="Error message if any")
    selected_agent: Optional[str] = Field(None, description="Agent that handled the request")
    session_id: str = Field(..., description="Session ID for this conversation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "explanation": "Here are all the customers in the database",
                "query_result": "| id | name |\n|1|John|",
                "sql_query": "SELECT * FROM customers",
                "error": None,
                "selected_agent": "sql_agent",
                "session_id": "abc123-session-id"
            }
        }


class SessionDeleteResponse(BaseModel):
    """Session deletion response model."""
    
    status: str = Field(..., description="Deletion status")
    message: str = Field(..., description="Deletion confirmation message")
    session_id: str = Field(..., description="Deleted session ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Session deleted successfully",
                "session_id": "abc123-session-id"
            }
        }
