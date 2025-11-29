from src.app.services import session_service , runner
from google.genai import types
import asyncio


async def test_greeting_agent():
    """Test the greeting agent."""
    # Changed session_id from "session-1" to None to allow the service to generate a unique ID
    session = await session_service.create_session(
        app_name="sql-chatbot",
        user_id="test-user",
        session_id=None
    )

    user_message = types.UserContent("Hi, I want to use this SQL chatbot.")

    async for event in runner.run_async(
        user_id="test-user",
        # Use the ID of the newly created session, which will be a unique UUID
        session_id=session.id,
        new_message=user_message
    ):
        if event.is_final_response():
            # final LLM response from greeting agent
            print("Agent Response:\n")
            if event.content and event.content.parts:
                print(event.content.parts[0].text)
            else:
                print("[WARN] Final event has no content")


if __name__ == "__main__":
    asyncio.run(test_greeting_agent())