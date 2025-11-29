from google.adk.runners import Runner
from src.app.agents import greeting_agent
from src.app.services import session_service


runner = Runner(agent=greeting_agent, app_name="sql-chatbot", session_service=session_service)