"""Orchestrator Agent - Main entry point for routing user queries."""

from google.adk.agents import LlmAgent
from .prompt import name, description, instruction

# Import sub-agents - must import from .agent module, not from parent package
from src.app.agents.greeting_agent.agent import greeting_agent
from src.app.agents.sql_agent.agent import sql_agent

orchestrator_agent = LlmAgent(
    model="gemini-2.5-flash",
    name=name,
    description=description,
    instruction=instruction,
    sub_agents=[
        greeting_agent,
        sql_agent
    ]
)
