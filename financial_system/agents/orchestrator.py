from google.adk.agents import SequentialAgent

from .portfolio_agent import portfolio_agent
from .risk_performance_agent import risk_performance_agent
from .news_agent import news_analyst
from .recommendation_agent import recommendation_agent

# Wire output keys so ADK state passes JSON between agents.
portfolio_agent.output_key = "portfolio_summary"
risk_performance_agent.output_key = "risk_performance"
news_analyst.output_key = "news_summary"
recommendation_agent.output_key = "recommendation_plan"

# Define the top-level orchestrator running all four agents in sequence.
root_agent = SequentialAgent(
    name="FinancialOrchestrator",
    sub_agents=[
        portfolio_agent,
        risk_performance_agent,
        news_analyst,
        recommendation_agent,
    ],
    description="""
You are the Lead Investment Strategist orchestrating a four-stage analysis:
1) PortfolioDataAgent builds a structured PortfolioSummary from Kite MCP tools.
2) RiskAndPerformanceAgent analyzes concentration, diversification, and winners/losers.
3) NewsAndMacroAgent brings in recent news and macro signals relevant to key holdings/sectors.
4) RecommendationAgent synthesizes everything into an actionable RecommendationPlan.
""",
)