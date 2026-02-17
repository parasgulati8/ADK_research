import os
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools.mcp_tool import McpTool


# ---------------------------------------------------------
# 1. SETUP & CITATION CALLBACK
# ---------------------------------------------------------
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE" # Force AI Studio for better MCP support

def citation_retrieval_callback(response):
    """Extracts grounding sources and appends them to the agent's text."""
    if response.grounding_metadata and response.grounding_metadata.citations:
        sources = "\n\n**Sources & Grounding:**"
        for citation in response.grounding_metadata.citations:
            sources += f"\n- {citation.uri}"
        response.text += sources
    return response

# 1. Connect to your local Kite MCP server
kite_tool = McpTool(
    name="KiteTrading",
    # Point to your local server instance
    url="https://mcp.kite.trade/mcp",#"http://localhost:8080/mcp", 
    instruction="Use this tool to fetch live Stock prices, holdings, portfolio info."
)
# kite_tool = McpTool(
#     name="KiteTrading",
#     # Use the official Zerodha hosted endpoint
#     url="https://mcp.kite.trade/mcp", 
#     instruction="Use this tool to fetch live NIFTY data and portfolio info."
# )

# ---------------------------------------------------------
# 2. THE SPECIALIST AGENTS
# ---------------------------------------------------------

# STEP 1: PORTFOLIO ANALYST (Zerodha MCP)
# Security: The toolset handles tokens; the agent only sees the final JSON data.
portfolio_analyst = LlmAgent(
    name="PortfolioAnalyst",
    model="gemini-2.5-flash-lite",
    tools=[kite_tool],
    output_key="portfolio_data", # Writes to state
    instruction="""
    Use 'get_holdings' and 'get_margins'. 
    Categorize holdings into sectors (IT, Pharma, BFSI, etc.).
    Calculate your 'Current Risk Factor': Which 3 stocks represent the highest capital risk?
    Output a structured summary of the portfolio's current health.
    """
)





# STEP 2: GEOPOLITICAL EXPERT (Grounding Metadata)
geopolitical_expert = LlmAgent(
    name="GeopoliticalExpert",
    model="gemini-2.0-flash",
    tools=[google_search],
    after_model_callbacks=[citation_retrieval_callback],
    output_key="world_news",
    instruction="""
    Search for global macro events today (Feb 16, 2026).
    Focus specifically on:
    1. US Fed or RBI interest rate commentary.
    2. Crude oil and commodity price shifts affecting India.
    3. Trade policy or geopolitical tension in the Middle East or SE Asia.
    You MUST provide source URLs for every claim.
    """
)

# STEP 3: QUANTITATIVE ANALYZER (Correlation & Tech Analysis)
quant_analyzer = LlmAgent(
    name="QuantAnalyzer",
    model="gemini-2.0-pro", # Pro model for deep correlation logic
    output_key="quant_logic",
    instruction="""
    Review {portfolio_data} against {world_news}.
    1. CORRELATION: How do the news events directly impact my specific holdings? 
       (e.g., If USD/INR is rising, how does it affect my IT holdings?)
    2. TECHNICAL CHECK: Use Google Search to find current RSI and 200-day EMA 
       for my top 3 high-exposure stocks mentioned in {portfolio_data}.
    3. INFERENCE: Determine if a stock is 'Overbought/Oversold' while facing macro headwinds.
    """
)

# STEP 4: RISK CRITIQUE (Guardrails)
risk_critique = LlmAgent(
    name="RiskCritique",
    model="gemini-2.0-flash",
    output_key="risk_vetting",
    instruction="""
    Act as a 'Red Team' Risk Officer. Review the {quant_logic}.
    GUARDRAILS:
    - Check if the technical analysis (RSI/EMA) is based on factual current data.
    - Identify 'Confirmation Bias': Is the analyzer ignoring positive news?
    - VIX Check: If India VIX or VIX is > 18, flag an 'Extreme Risk' warning.
    - REJECT any recommendation to buy or sell more than 5% of the total portfolio value in one day.
    """
)

# STEP 5: STRATEGIC LEAD (Orchestrator)
# This agent synthesizes all previous state data into the final report.
root_agent = SequentialAgent(
    name="FinanceDirector",
    sub_agents=[portfolio_analyst, geopolitical_expert, quant_analyzer, risk_critique],
    instruction="""
    Synthesize all specialist reports into a 1-page Investment Strategy.
    1. **Portfolio Health Summary** (from {portfolio_data})
    2. **Macro Volatility Scan** (from {world_news})
    3. **Recommended Changes**: Direct Buy/Sell/Hedge actions based on {quant_logic}.
    4. **Risk Disclaimers**: Incorporate the {risk_vetting} notes as 'Cautions'.
    Ensure the report is brief, actionable, and grounded in data.
    """
)

# ---------------------------------------------------------
# 3. EXECUTION RUNNER
# ---------------------------------------------------------

async def main():
    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, session_service=session_service)
    
    # Create a fresh session
    session = await session_service.create_session(app_name="FinanceDirector", user_id="Paras")
    
    print("🚀 Running Financial Intelligence Pipeline...")
    print("--- (This may take 30-60s due to search and tool calls) ---\n")
    
    async for event in runner.run_async(
        new_message=types.Content(role="user", parts=[types.Part(text="Generate my daily portfolio strategic briefing.")]),
        session_id=session.id,
        user_id="Paras"
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
    
    # import os
# from google.adk.agents import LlmAgent, SequentialAgent
# from google.adk.tools.google_search_tool import google_search
# from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

# # 1. Portfolio Specialist: Data stays as structured state
# portfolio_analyst = LlmAgent(
#     name="PortfolioAnalyst",
#     model="gemini-2.5-flash-lite",
#     tools=[MCPToolset(connection_params=SseServerParams(url="https://mcp.kite.trade/sse"))],
#     output_key="portfolio_data", # Stateful Memory: Saves result to session
#     instruction="""
#     Use the 'get_holdings' tool to retrieve current investments.
#     Output a JSON-structured summary containing:
#     - Ticker Symbols and Quantity.
#     - Sector Weightage (e.g., Finance: 40%, IT: 20%).
#     - Total Unrealized P&L.
#     DO NOT provide investment advice. Only provide data grounding.
#     """
# )
# def citation_callback(response):
#     """Appends grounding URLs to the agent output."""
#     if response.grounding_metadata and response.grounding_metadata.citations:
#         sources = "\n\nSources:" + "".join([f"\n- {c.uri}" for c in response.grounding_metadata.citations])
#         response.text += sources
#     return response

# geopolitical_scout = LlmAgent(
#     name="GeopoliticalScout",
#     model="gemini-2.0-flash",
#     tools=[google_search],
#     after_model_callbacks=[citation_callback],
#     output_key="geopolitical_context",
#     instruction="""
#     Identify today's (Feb 16, 2026) top 3 global macro events.
#     Focus on: 1. Interest rate shifts, 2. Supply chain disruptions in Asia, 3. Energy price volatility, 4. Any major macroeconomic and geopolotical news
#     Constraint: You MUST cite specific financial news URLs for every event mentioned.
#     """
# )

# quant_analyzer = LlmAgent(
#     name="QuantAnalyzer",
#     model="gemini-2.0-pro", # High-reasoning model
#     instruction="""
#     Analyze {portfolio_data} against {geopolitical_context}.
#     Task 1 (Correlation): If news is 'Bearish' for a sector, identify which tickers in the portfolio are at risk.
#     Task 2 (Technical Context): For high-exposure tickers, search for 'Current RSI and 200-day EMA' levels.
#     Task 3 (Synthesis): Identify if a stock is 'Overextended' (RSI > 70) while facing geopolitical headwinds.
#     """
# )
# critique_agent = LlmAgent(
#     name="RiskCritique",
#     model="gemini-2.0-flash",
#     instruction="""
#     Act as a Conservative Risk Officer. Review the QuantAnalyzer's report.
#     GUARDRAILS:
#     1. FACT-CHECK: Verify if the suggested technical levels (RSI/EMA) align with the reported news.
#     2. BIAS CHECK: Ensure the analyzer isn't panic-selling on 'Noise' vs 'Signal'.
#     3. VIX CHECK: If market volatility (VIX) is > 20, force a defensive recommendation.
#     4. REJECT if the analyzer suggests putting >10% of total capital into a single new investment.
#     """
# )

# root_agent = SequentialAgent(
#     name="PortfolioStrategist",
#     sub_agents=[portfolio_analyst, geopolitical_scout, quant_analyzer, critique_agent],
#     instruction="""
#     Deliver a Final Strategic Briefing.
#     Format:
#     - **Current Health**: Summary of {portfolio_data}.
#     - **Threat Landscape**: Critical news from {geopolitical_context}.
#     - **Actions**: Direct 'Buy/Sell/Hold' instructions with 'Stop-Loss' levels.
#     - **Critique Note**: Incorporate the Risk Officer's concerns as 'Cautions'.
#     """
# )
# # /my_stock_agent/agent.py
# from google.adk.agents import LlmAgent, SequentialAgent
# from google.adk.tools.google_search_tool import google_search

# search_specialist = LlmAgent(
#     name="SearchSpecialist",
#     model="gemini-2.5-flash-lite", # Stable model for better UI performance
#     tools=[google_search],
#     output_key="market_data"
# )

# editor = LlmAgent(
#     name="Editor",
#     model="gemini-2.5-flash-lite",
#     instruction="Summarize {market_data} into an executive brief."
# )

# # This is the agent the UI will interact with
# root_agent = SequentialAgent(
#     name="my_team",
#     sub_agents=[search_specialist, editor]
# )
                                                                                                                                                                                                                   