import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams
from google.genai import types
import logging

# Setup
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("❌ GOOGLE_API_KEY not found in environment!")

# Load Kite MCP connection
with open("access_token.txt", "r") as f:
    valid_token = f.read().strip()

params = SseConnectionParams(
    url="https://mcp.kite.trade/sse",
    headers={
        "Authorization": f"Bearer {valid_token}",
        "X-Kite-API-Key": os.getenv("KITE_API_KEY"),
    },
    timeout=120
)

# ============================================================================
# MULTI-AGENT PORTFOLIO ANALYSIS SYSTEM
# ============================================================================

class PortfolioAnalysisTeam:
    """
    Multi-agent system for comprehensive portfolio analysis:
    1. DataFetcher - Retrieves portfolio data from Kite
    2. RiskAnalyzer - Analyzes portfolio risk and concentration
    3. PerformanceAnalyzer - Evaluates returns and performance
    4. DiversificationAnalyzer - Checks asset allocation and diversification
    5. TaxOptimizer - Suggests tax-loss harvesting opportunities
    6. RecommendationEngine - Provides actionable insights
    """
    
    def __init__(self):
        self.kite_toolset = McpToolset(connection_params=params)
        self.runner = None
        self.session = None
        
    async def initialize(self):
        """Initialize agents and session"""
        print("🚀 Initializing Portfolio Analysis Team...\n")
        
        # Discover Kite tools
        self.tools = await asyncio.wait_for(
            self.kite_toolset.get_tools(), 
            timeout=60.0
        )
        print(f"✅ Connected to Kite MCP. {len(self.tools)} tools available.\n")
        
        # Setup a shared session service and session for all agent runners
        self.session_service = InMemorySessionService()
        self.session = await self.session_service.create_session(
            app_name="PortfolioAnalysis",
            user_id="analyst"
        )
        
        # Note: Runner instances are created per-agent in _run_agent_task()
        # to ensure each agent has a proper `agent` value. No global Runner
        # is required here.
        
        print("=" * 70)
        print("PORTFOLIO ANALYSIS TEAM READY")
        print("=" * 70)
        self._print_team_structure()
    
    def _print_team_structure(self):
        """Display team structure"""
        agents = [
            ("🔐 DataFetcher", "Retrieves portfolio, positions, holdings, margins"),
            ("⚠️  RiskAnalyzer", "Analyzes concentration, sector exposure, volatility"),
            ("📈 PerformanceAnalyzer", "Evaluates returns, benchmarks, performance"),
            ("🎯 DiversificationAnalyzer", "Checks asset allocation and diversification"),
            ("💰 TaxOptimizer", "Identifies tax-loss harvesting opportunities"),
            ("💡 RecommendationEngine", "Derives actionable insights and suggestions"),
            ("📊 ReportGenerator", "Synthesizes findings into executive summary"),
        ]
        
        print("\nTeam Structure:")
        for name, desc in agents:
            print(f"  {name}")
            print(f"    └─ {desc}")
        print()
    
    async def analyze_portfolio(self, analysis_type="comprehensive"):
        """Main portfolio analysis workflow"""
        
        analyses = {
            "comprehensive": self._comprehensive_analysis,
            "risk": self._risk_analysis,
            "performance": self._performance_analysis,
            "diversification": self._diversification_analysis,
        }
        
        if analysis_type not in analyses:
            print(f"❌ Unknown analysis type: {analysis_type}")
            return
        
        await analyses[analysis_type]()
    
    async def _comprehensive_analysis(self):
        """Full portfolio analysis workflow"""
        
        print("\n" + "=" * 70)
        print("COMPREHENSIVE PORTFOLIO ANALYSIS")
        print("=" * 70 + "\n")
        
        # Step 1: Data Fetcher Agent
        await self._run_agent_task(
            "DataFetcher",
            "Phase 1️⃣ : Data Collection",
            """Fetch my complete portfolio data:
1. Get my full holdings with quantities and values
2. Get my current open positions
3. Get my account margins and available funds
4. Get my recent trades and order history
Prepare a summary of all fetched data."""
        )
        
        # Step 2: Risk Analyzer Agent
        await self._run_agent_task(
            "RiskAnalyzer",
            "Phase 2️⃣ : Risk Analysis",
            """Analyze portfolio risk:
1. Identify concentration risks (any single holding > 20%)
2. Analyze sector exposure and concentration
Provide risk assessment and red flags."""
        )
        
        # Step 3: Performance Analyzer Agent
        await self._run_agent_task(
            "PerformanceAnalyzer",
            "Phase 3️⃣ : Performance Analysis",
            """Evaluate portfolio performance:
1. Calculate overall portfolio performance
2. Identify top and bottom performers
3. Analyze gain/loss distribution
4. Review recent trading performance
Provide performance insights and trends."""
        )
        
        # Step 4: Diversification Analyzer Agent
        await self._run_agent_task(
            "DiversificationAnalyzer",
            "Phase 4️⃣ : Diversification Check",
            """Analyze portfolio diversification:
1. Check sector-wise allocation
2. Review company size (Large-cap vs Mid vs Small)
3. Assess geographic exposure
4. Review asset class distribution
Provide diversification recommendations."""
        )
        
        # Step 5: Tax Optimizer Agent
        await self._run_agent_task(
            "TaxOptimizer",
            "Phase 5️⃣ : Tax Optimization",
            """Identify tax optimization opportunities:
1. Find positions with unrealized losses
2. Suggest tax-loss harvesting candidates
3. Review holding periods for capital gains
4. Check for long-term vs short-term gains
Provide tax-efficient strategy recommendations."""
        )
        
        # Step 6: Recommendation Engine
        await self._run_agent_task(
            "RecommendationEngine",
            "Phase 6️⃣ : Action Items",
            """Synthesize all analysis and provide recommendations:
1. Top 3 immediate actions based on risk analysis
2. Best opportunities for portfolio rebalancing
3. Sectors to increase/decrease exposure in
4. Specific stocks to consider buying/selling
Prioritize by impact and urgency."""
        )
        
        # Step 7: Report Generator
        await self._run_agent_task(
            "ReportGenerator",
            "Phase 7️⃣ : Executive Summary",
            """Create a comprehensive executive summary:
1. Portfolio health score (1-10)
2. Key metrics at a glance
3. Top 3 risks and mitigation strategies
4. Top 3 opportunities
5. Recommended immediate actions
Format as a professional investment report."""
        )
        
        print("\n" + "=" * 70)
        print("✅ PORTFOLIO ANALYSIS COMPLETE")
        print("=" * 70 + "\n")
    
    async def _risk_analysis(self):
        """Focused risk analysis"""
        print("\n" + "=" * 70)
        print("RISK ANALYSIS")
        print("=" * 70 + "\n")
        
        await self._run_agent_task(
            "RiskAnalyzer",
            "Risk Assessment",
            "Perform a detailed risk analysis of my portfolio and provide mitigation strategies"
        )
    
    async def _performance_analysis(self):
        """Focused performance analysis"""
        print("\n" + "=" * 70)
        print("PERFORMANCE ANALYSIS")
        print("=" * 70 + "\n")
        
        await self._run_agent_task(
            "PerformanceAnalyzer",
            "Performance Review",
            "Analyze my portfolio performance, identify winners and losers, and explain trends"
        )
    
    async def _diversification_analysis(self):
        """Focused diversification analysis"""
        print("\n" + "=" * 70)
        print("DIVERSIFICATION ANALYSIS")
        print("=" * 70 + "\n")
        
        await self._run_agent_task(
            "DiversificationAnalyzer",
            "Diversification Review",
            "Evaluate my portfolio diversification and provide rebalancing suggestions"
        )
    
    async def _run_agent_task(self, agent_name, phase_name, task_description):
        """Execute an agent task within session context"""
        
        print(f"\n{phase_name}")
        print("-" * 70)
        
        # Create agent based on name
        agent = self._create_agent(agent_name)
        
        # Use the shared session service and session created in initialize
        session_service = getattr(self, 'session_service', InMemorySessionService())
        session = getattr(self, 'session', None)
        if session is None:
            session = await session_service.create_session(app_name=agent_name, user_id="analyst")

        runner = Runner(
            app_name=agent_name,
            agent=agent,
            session_service=session_service
        )
        
        try:
            # Execute task
            async for event in runner.run_async(
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=task_description)]
                ),
                user_id="analyst",
                session_id=session.id
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(part.text, end="", flush=True)
                        elif hasattr(part, 'function_call') and part.function_call and hasattr(part.function_call, 'name'):
                            print(f"\n[Executing: {part.function_call.name}]\n", flush=True)
            
            print("\n")
        
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⚠️  API quota limits reached. Please retry in a few minutes.\n")
            else:
                print(f"❌ Error: {type(e).__name__}\n")
    
    def _create_agent(self, agent_name):
        """Factory method to create agents"""
        
        agent_configs = {
            "DataFetcher": {
                "name": "DataFetcher",
                "instruction": """You are a portfolio data fetcher. Your job is to:
1. Get the user's complete holdings using get_holdings
2. Get their positions using get_positions
3. Get margins and funds using get_margins
4. Get recent trades using get_trades
Fetch all data and present a clear summary."""
            },
            "RiskAnalyzer": {
                "name": "RiskAnalyzer",
                "instruction": """You are a risk analyst. Analyze the portfolio data to:
1. Identify concentration risks (holdings > 20% of portfolio)
2. Find illiquid positions
3. Check cash reserves as a percentage of portfolio
4. Identify correlated holdings
Provide clear risk assessment and recommendations."""
            },
            "PerformanceAnalyzer": {
                "name": "PerformanceAnalyzer",
                "instruction": """You are a performance analyst. Evaluate:
1. Overall portfolio returns
2. Winning vs losing positions
3. Performance drivers and detractors
4. Recent trading success rate
Provide insights on what's working and what isn't."""
            },
            "DiversificationAnalyzer": {
                "name": "DiversificationAnalyzer",
                "instruction": """You are a diversification expert. Assess:
1. Sector-wise allocation
2. Large-cap vs Mid-cap vs Small-cap exposure
3. Geographic and industry diversification
4. Cash allocation
Recommend portfolio rebalancing if needed."""
            },
            "TaxOptimizer": {
                "name": "TaxOptimizer",
                "instruction": """You are a tax optimization specialist. Identify:
1. Positions with unrealized losses for tax harvesting
2. Long-term capital gains opportunities
3. Short-term losses to offset gains
4. Optimal timing for sales
Provide tax-efficient strategies."""
            },
            "RecommendationEngine": {
                "name": "RecommendationEngine",
                "instruction": """You are an investment advisor. Based on all analysis:
1. Provide top 3 immediate actions
2. Suggest specific buy/sell recommendations
3. Recommend sector allocation changes
4. Suggest risk mitigation strategies
Be specific and actionable."""
            },
            "ReportGenerator": {
                "name": "ReportGenerator",
                "instruction": """You are an investment report writer. Create an executive summary:
1. Portfolio health score (1-10 with explanation)
2. Key metrics: total value, diversity score, risk level
3. Top 3 portfolio risks
4. Top 3 portfolio opportunities
5. Specific action items prioritized
Format professionally for presentation."""
            },
        }
        
        config = agent_configs.get(agent_name, {})
        
        return LlmAgent(
            name=config.get("name", agent_name),
            model="gemini-2.5-flash-lite",
            tools=self.tools,
            instruction=config.get("instruction", f"You are the {agent_name} agent.")
        )
    
    async def close(self):
        """Cleanup"""
        await self.kite_toolset.close()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def main():
    """Main entry point"""
    team = PortfolioAnalysisTeam()
    
    try:
        await team.initialize()
        
        # Run comprehensive analysis
        # await team.analyze_portfolio("comprehensive")
        
        # Or run specific analyses:
        await team.analyze_portfolio("risk")
        # await team.analyze_portfolio("performance")
        # await team.analyze_portfolio("diversification")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {type(e).__name__}: {e}")
    
    finally:
        await team.close()


if __name__ == "__main__":
    asyncio.run(main())