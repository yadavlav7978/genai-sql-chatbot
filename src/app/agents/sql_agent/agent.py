"""SQL Agent - Orchestrates SQL query processing."""

from google.adk.agents import LlmAgent, SequentialAgent
from .prompt import name, description

# Import sub-agents - must import from .agent module, not from parent package
from src.app.agents.inputValidationAndSqlGeneration_agent.agent import inputValidationAndSqlGeneration_agent
from src.app.agents.sqlValidatorAndSqlExecutor_agent.agent import sqlValidatorAndSqlExecutor_agent


sql_agent = SequentialAgent(
    name=name,
    description=description,
    sub_agents=[
        inputValidationAndSqlGeneration_agent,
        sqlValidatorAndSqlExecutor_agent
    ]
)
