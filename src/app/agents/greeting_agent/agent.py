from google.adk.agents import Agent
from .prompt import GREETING_AGENT_NAME, GREETING_AGENT_DESCRIPTION, GREETING_AGENT_INSTRUCTION

greeting_agent = Agent(
    model="gemini-2.5-flash",
    name=GREETING_AGENT_NAME,
    description=GREETING_AGENT_DESCRIPTION,
    instruction=GREETING_AGENT_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True
)