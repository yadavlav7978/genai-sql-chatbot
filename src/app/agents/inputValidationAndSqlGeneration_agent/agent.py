from google.adk.agents import LlmAgent
from .prompt import name, description, instruction
from src.app.tools import get_schema

inputValidationAndSqlGeneration_agent = LlmAgent(
    model="gemini-2.5-flash",
    name=name,
    description=description,
    instruction=instruction,
    tools=[get_schema],
    output_key="generated_sql"  # will store result in state['generated_sql']
)
