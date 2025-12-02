"""Orchestrator Agent - Main entry point for routing user queries."""

from google.adk.agents import LlmAgent
from .prompt import name, description, instruction
from google.adk.models.lite_llm import LiteLlm
import os

# Import sub-agents - must import from .agent module, not from parent package
from src.app.agents.greeting_agent.agent import greeting_agent
from src.app.agents.sql_agent.agent import sql_agent

orchestrator_agent = LlmAgent(
    model=LiteLlm(model=os.environ['MODEL']),
    name=name,
    description=description,
    instruction=instruction,
    sub_agents=[
        greeting_agent,
        sql_agent
    ]
)
