from google.adk.agents import LlmAgent
from .prompt import name, description, instruction
from src.app.tools import get_schema
from google.adk.models.lite_llm import LiteLlm
import os

inputValidationAndSqlGeneration_agent = LlmAgent(
    model=LiteLlm(model=os.environ['MODEL']),
    name=name,
    description=description,
    instruction=instruction,
    tools=[get_schema],
    output_key="generated_sql"  # will store result in state['generated_sql']
)
