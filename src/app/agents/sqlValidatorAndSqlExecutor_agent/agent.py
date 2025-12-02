from google.adk.agents import LlmAgent
from .prompt import name, description, instruction
from src.app.tools import execute_sql,get_schema
from google.adk.models.lite_llm import LiteLlm
import os

sqlValidatorAndSqlExecutor_agent = LlmAgent(
    model=LiteLlm(model=os.environ['MODEL']),
    name=name,
    description=description,
    instruction=instruction,
    output_key="query_result",  # stored in state['query_result']
    tools=[execute_sql,get_schema]
)