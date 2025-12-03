# =============================== IMPORTS ===============================
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional

from src.app.configs.logger_config import get_logger
from src.app.utils.response_parser import parse_agent_response
from src.app.services import session_service, runner
from google.genai import types

# =============================== LOGGER ===============================
logger = get_logger("Chat-Api-service")

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
        # Validate user message
        if not message:
            logger.warning("Chat request failed. Message is empty.")
            raise HTTPException(status_code=400, detail="Message required")

        # Log incoming request details
        trimmed_msg = message[:100] + ("..." if len(message) > 100 else "")
        logger.info(
            f"Chat request received. Session ID: {session_id if session_id else 'New Session'}, "
            f"Message: '{trimmed_msg}'"
        )

        # Check if file is uploaded
        from src.app.api.file_manager import CURRENT_FILE_ID, UPLOAD_DIR
        if not CURRENT_FILE_ID:
            logger.warning("Chat request stopped. No uploaded file found.")
            raise HTTPException(
                status_code=400,
                detail="Please upload an Excel/CSV file before using the chat"
            )

        from src.app.services import session_service, runner
        from google.genai import types

        user_id = "web-user"  # future: from authentication

        # =============================== SESSION MANAGEMENT ===============================
        if not session_id:
            logger.info("No session ID provided. Creating a new session.")
            session = await session_service.create_session(
                app_name="sql-chatbot",
                user_id=user_id
            )
            session_id = session.id
            logger.info(f"New session created with ID: {session_id}")

        else:
            logger.info(f"Using existing session ID: {session_id}")
            session = await session_service.get_session(
                app_name="sql-chatbot",
                user_id=user_id,
                session_id=session_id
            )

            if not session:
                logger.warning(f"Session {session_id} not found. Creating a new session.")
                session = await session_service.create_session(
                    app_name="sql-chatbot",
                    user_id=user_id,
                    session_id=session_id
                )
                logger.info(f"New session created with ID: {session_id}")

        # =============================== FILE CONTEXT ===============================
        file_path = None
        if CURRENT_FILE_ID:
            # Find the file that matches the ID
            for file in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
                file_path = str(file)
                logger.info(f"Using uploaded file for context: {file.name}")
                break
        else:
            logger.info("No uploaded file available for this chat.")

        # =============================== SEND MESSAGE TO GENAI ===============================
        user_msg = types.UserContent(message)
        selected_agent = None

        logger.info("Sending message to AI model...")
        response_text = ""

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
        logger.info(f"AI response received: '{trimmed_resp}'")

        # =============================== PARSE AI RESPONSE ===============================
        parsed = parse_agent_response(response_text)

        logger.info(f"Chat request processed successfully for session ID: {session_id}")

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
