from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional

from src.app.configs.logger_config import get_logger
from src.app.api.file_manager import CURRENT_FILE_ID, UPLOAD_DIR

logger = get_logger("chat-service")

router = APIRouter(prefix="/api", tags=["chat"])


def parse_agent_response(response_text: str) -> dict:
    """
    Parse the structured agent response into clean sections.
    Expected format uses delimiters: <<<EXPLANATION>>>, <<<QUERY_RESULT>>>, <<<SQL>>>, <<<ERROR>>>, <<<END>>>
    """
    result = {
        "explanation": "",
        "query_result": None,
        "sql_query": None,
        "error": None
    }
    
    if not response_text:
        return result
    
    # Extract EXPLANATION section
    if "<<<EXPLANATION>>>" in response_text and "<<<" in response_text[response_text.find("<<<EXPLANATION>>>") + 17:]:
        start = response_text.find("<<<EXPLANATION>>>") + 17
        # Find the next delimiter
        next_delimiters = ["<<<QUERY_RESULT>>>", "<<<SQL>>>", "<<<ERROR>>>", "<<<INVALID>>>", "<<<END>>>"]
        end_positions = [response_text.find(d, start) for d in next_delimiters if response_text.find(d, start) != -1]
        end = min(end_positions) if end_positions else len(response_text)
        result["explanation"] = response_text[start:end].strip()
    
    # Extract QUERY_RESULT section (markdown table)
    if "<<<QUERY_RESULT>>>" in response_text:
        start = response_text.find("<<<QUERY_RESULT>>>") + 18
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["query_result"] = response_text[start:end].strip()
    
    # Extract SQL section
    if "<<<SQL>>>" in response_text:
        start = response_text.find("<<<SQL>>>") + 9
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["sql_query"] = response_text[start:end].strip()
    
    # Extract ERROR section
    if "<<<ERROR>>>" in response_text:
        start = response_text.find("<<<ERROR>>>") + 11
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["error"] = response_text[start:end].strip()
    
    # Extract INVALID section (treated as error)
    if "<<<INVALID>>>" in response_text:
        start = response_text.find("<<<INVALID>>>") + 13
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["error"] = response_text[start:end].strip()
    
    return result


@router.post("/chat")
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Main SQL Chatbot endpoint handling user messages."""
    try:
        if not message:
            logger.warning("Chat request failed: Message is empty")
            raise HTTPException(status_code=400, detail="Message required")

        logger.info(f"Received chat request. Session ID: {session_id if session_id else 'New Session'}, Message: '{message[:100]}{'...' if len(message) > 100 else ''}'")

        # Check if file is uploaded
        from src.app.api.file_manager import CURRENT_FILE_ID
        if not CURRENT_FILE_ID:
            logger.warning("Chat request rejected: No file uploaded")
            raise HTTPException(
                status_code=400,
                detail="Please upload an Excel/CSV file before starting chat"
            )

        from src.app.services import session_service, runner
        from google.genai import types

        user_id = "web-user"  # future: get from auth middleware

        # Session management
        if not session_id:
            # create new session
            logger.info("Creating new session for user")
            session = await session_service.create_session(
                app_name="sql-chatbot",
                user_id=user_id
            )
            session_id = session.id
            logger.info(f"New session created: {session_id}")
        else:
            # try to use existing session
            session = await session_service.get_session(
                app_name="sql-chatbot",
                user_id=user_id,
                session_id=session_id
            )

            if not session:
                logger.warning(f"Session {session_id} not found, creating new session")
                # recreate session
                session = await session_service.create_session(
                    app_name="sql-chatbot",
                    user_id=user_id,
                    session_id=session_id
                )
                logger.info(f"Recreated session: {session_id}")

        
        # Fetch uploaded file (if any)
        file_path = None
        if CURRENT_FILE_ID:
            for file in UPLOAD_DIR.glob(f"{CURRENT_FILE_ID}.*"):
                file_path = str(file)
                logger.info(f"Using uploaded file context: {file.name}")
                break
        else:
            logger.info("No file context available for this chat")

        # Prepare user message
        user_msg = types.UserContent(message)

        # Run GenAI pipeline
        response_text = ""

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_msg
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text

        logger.info(f"AI response generated: '{response_text[:200]}{'...' if len(response_text) > 200 else ''}'")
        
        # Parse the structured response
        parsed = parse_agent_response(response_text)
        
        logger.info(f"Chat request processed successfully for session: {session_id}")
        return {
            "status": "success",
            "explanation": parsed["explanation"],
            "query_result": parsed["query_result"],
            "sql_query": parsed["sql_query"],
            "error": parsed["error"],
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
