"""Request models for API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Chat request model for user queries."""
    
    message: str = Field(..., description="User's query message")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Show me all customers",
                "session_id": "abc123-session-id"
            }
        }


class SessionDeleteRequest(BaseModel):
    """Session deletion request model."""
    
    session_id: str = Field(..., description="Session ID to delete")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-session-id"
            }
        }
