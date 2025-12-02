from google.adk.agents import LlmAgent
from .prompt import name, description, instruction
from src.app.tools import execute_sql,get_schema

sqlValidatorAndSqlExecutor_agent = LlmAgent(
    model="gemini-2.5-flash",
    name=name,
    description=description,
    instruction=instruction,
    output_key="query_result",  # stored in state['query_result']
    tools=[execute_sql,get_schema]
)