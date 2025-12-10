"""
Chat API Endpoints - SQL Chatbot Backend

Purpose
-------
Provides a clean interface for the frontend to communicate with the SQL chatbot. It validates
incoming requests, ensures files are present, manages user sessions, sends messages to the
agent runner, and returns a structured JSON response.

What this file does
-------------------
- Accepts chat messages from the UI.
- Verifies required Excel/CSV files are uploaded.
- Creates or loads a chat session.
- Sends the message to the orchestrator/agent and waits for the final response.
- Parses the response into explanation, SQL query, results, and errors.
- Allows deleting a session safely (idempotent).
"""

# =============================== IMPORTS ===============================
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional

from src.app.configs.logger_config import get_logger
from src.app.utils.response_parser import parse_agent_response
from src.app.services import session_service, runner
from google.genai import types
import asyncio

# =============================== LOGGER ===============================
logger = get_logger("Chat-Api-Service")

# =============================== ROUTER ===============================
router = APIRouter(prefix="/api", tags=["chat"])


# =============================== CHAT ENDPOINT ===============================
@router.post("/chat")
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Main SQL Chatbot endpoint handling user messages."""

    try:
        if not message:
            raise HTTPException(status_code=400, detail="Message required")

        # Trim log message for readability
        trimmed_msg = message[:100] + ("..." if len(message) > 100 else "")
        logger.info(
            f"Chat request received. "
            f"Session: {session_id or 'New Session'}, Message: '{trimmed_msg}'"
        )

        # Ensure file(s) exist before querying
        from src.app.api.file_manager import FILE_REGISTRY
        if not FILE_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail="Please upload an Excel/CSV file before using the chat"
            )

        logger.info(f"Processing chat with {len(FILE_REGISTRY)} uploaded file(s).")

        user_id = "web-user"  # Future: real auth user ID

        # =============================== SESSION MANAGEMENT ===============================
        if not session_id:
            logger.info("No session ID provided. Creating a new session.")
            session = await session_service.create_session(
                app_name="sql-chatbot",
                user_id=user_id
            )
            session_id = session.id
            logger.info(f"New session created: {session_id}")

        else:
            session = await session_service.get_session(
                app_name="sql-chatbot",
                user_id=user_id,
                session_id=session_id
            )

            if not session:
                logger.warning(f"Session not found. Creating new session with provided ID: {session_id}")
                session = await session_service.create_session(
                    app_name="sql-chatbot",
                    user_id=user_id,
                    session_id=session_id
                )

        # =============================== SEND MESSAGE TO GENAI ===============================
        user_msg = types.UserContent(message)
        selected_agent = None
        response_text = ""

        logger.info("Sending message to agent...")

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_msg
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text

            if event.actions and event.actions.transfer_to_agent:
                selected_agent = event.actions.transfer_to_agent
                logger.info(f"Orchestrator agent selected: {selected_agent}")

        trimmed_resp = response_text[:200] + ("..." if len(response_text) > 200 else "")
        logger.info(f"Model response received: '{trimmed_resp}'")

        # =============================== PARSE RESPONSE ===============================
        parsed = parse_agent_response(response_text)

        return {
            "status": "success",
            "explanation": parsed["explanation"],
            "query_result": parsed["query_result"],
            "sql_query": parsed["sql_query"],
            "error": parsed["error"],
            "selected_agent": selected_agent,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")


# =============================== DELETE SESSION ===============================
@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""

    try:
        logger.info(f"Session delete requested: {session_id}")

        user_id = "web-user"

        session = await session_service.get_session(
            app_name="sql-chatbot",
            user_id=user_id,
            session_id=session_id
        )

        if not session:
            logger.warning(f"Session {session_id} not found. Returning success (idempotent delete).")
            return {
                "status": "success",
                "message": "Session not found or already deleted",
                "session_id": session_id
            }

        await session_service.delete_session(
            app_name="sql-chatbot",
            user_id=user_id,
            session_id=session_id
        )

        logger.info(f"Session deleted: {session_id}")

        return {
            "status": "success",
            "message": "Session deleted successfully",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Session deletion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session deletion error: {e}")
