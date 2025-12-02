from google.adk.agents import Agent
from .prompt import GREETING_AGENT_NAME, GREETING_AGENT_DESCRIPTION, GREETING_AGENT_INSTRUCTION
from google.adk.models.lite_llm import LiteLlm
import os

greeting_agent = Agent(
    model=LiteLlm(model=os.environ['MODEL']),
    name=GREETING_AGENT_NAME,
    description=GREETING_AGENT_DESCRIPTION,
    instruction=GREETING_AGENT_INSTRUCTION,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True
)