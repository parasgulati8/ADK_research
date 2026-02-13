# /my_stock_agent/agent.py
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.google_search_tool import google_search

search_specialist = LlmAgent(
    name="SearchSpecialist",
    model="gemini-2.5-flash-lite", # Stable model for better UI performance
    tools=[google_search],
    output_key="market_data"
)

editor = LlmAgent(
    name="Editor",
    model="gemini-2.5-flash-lite",
    instruction="Summarize {market_data} into an executive brief."
)

# This is the agent the UI will interact with
root_agent = SequentialAgent(
    name="my_team",
    sub_agents=[search_specialist, editor]
)
