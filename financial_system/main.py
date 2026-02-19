import asyncio
import os
import re
import webbrowser

from dotenv import load_dotenv
from google.genai import types

from google.adk.agents import Agent  # Ensure this import matches your ADK version
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import InvocationContext, Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

# Import the orchestrator and tools
from financial_system.agents.orchestrator import root_agent
from financial_system.tools import calculate_portfolio_metrics

async def interactive_login(mcp_tools):
    login_tool = next((t for t in mcp_tools if "login" in t.name.lower()), None)
    
    if login_tool:
        print("🔑 Initiating Kite Login...")
        
        # 1. Correct the Session fields (use id, appName, and userId)
        current_session = Session(
            id="initial_setup_session",  # Changed from session_id
            appName="FinancialSwarm",    # Required
            userId="dev_user"            # Required
        )

        # 2. Setup the InvocationContext
        # Note: Ensure dummy_agent also has required fields if it fails next
        invocation_context = InvocationContext(
            invocation_id="manual_login_task",
            agent=Agent(name="LoginAgent", description="Handle authentication"),
            session=current_session,
            session_service=InMemorySessionService(),
            artifact_service=InMemoryArtifactService(),
        )

        # 3. Initialize ToolContext and Run
        tool_context = ToolContext(invocation_context=invocation_context)
        result = await login_tool.run_async(
            args={}, 
            tool_context=tool_context
        )
        
        # Extract the full login URL from the response
        login_url = None
        if isinstance(result, dict) and "content" in result:
            for item in result.get("content", []):
                if isinstance(item, dict) and "text" in item:
                    text = str(item["text"])
                    # Try to extract URL from markdown format [text](url) or plain https://
                    url_match = re.search(r'https?://[^\s\)\]\`]+', text)
                    if url_match:
                        login_url = url_match.group(0)
                        break
        
        if login_url:
            print(f"\n🔗 Login URL (full):\n{login_url}\n")
            print("⚠️ Copy the URL above and open it in your browser to complete login.")
            # Optionally auto-open in browser
            try:
                webbrowser.open(login_url)
                print("🌐 Browser window opened automatically.")
            except Exception:
                print("(Could not auto-open browser - please copy URL manually)")
        else:
            print(f"\n⚠️ Could not extract login URL from response:")
            print(f"Response: {result}")
        
        input("\n🚀 After completing login in your browser, press Enter to continue...")

# async def interactive_login(mcp_tools):
#     """Handles the browser-based Zerodha login flow."""
#     login_tool = next((t for t in mcp_tools if t.name == 'login'), None)
#     if not login_tool:
#         return False
    
#     print("🔑 Initiating Kite Login...")
#     result = await login_tool.run_async(args={})
#     # Extract URL from the MCP tool response
#     text = result['content'][0]['text']
#     url_match = re.search(r'https?://[^\s)\]]+', text)
#     if url_match:
#         webbrowser.open(url_match.group(0))
#         input('🚀 After logging in, press Enter to continue...')
#         return True
#     return False


async def main():
    """
    Run the full 4-agent financial analysis pipeline:
    1) PortfolioDataAgent
    2) RiskAndPerformanceAgent
    3) NewsAndMacroAgent
    4) RecommendationAgent
    """
    load_dotenv()

    # 1. Initialize Kite MCP Toolset
    with open("access_token.txt", "r", encoding="utf-8") as f:
        valid_token = f.read().strip()

    params = SseConnectionParams(
        url="https://mcp.kite.trade/sse",
        headers={
            "Authorization": f"Bearer {valid_token}",
            "X-Kite-API-Key": os.getenv("KITE_API_KEY"),
        },
    )

    print("📡 Connecting to Kite MCP Server...")
    kite_toolset = McpToolset(connection_params=params)
    mcp_tools = await kite_toolset.get_tools()

    # 2. Handle Login if needed
    await interactive_login(mcp_tools)

    # 3. Inject tools into PortfolioDataAgent (first agent in the pipeline)
    p_agent = next(a for a in root_agent.sub_agents if a.name == "PortfolioDataAgent")
    p_agent.tools = mcp_tools + [calculate_portfolio_metrics]

    # 4. Run the System
    session_service = InMemorySessionService()

    # Ensure session is created first
    await session_service.create_session(
        app_name="FinancialAnalyst",
        user_id="unique_user_id",
        session_id="unique_session_id",
    )

    runner = Runner(
        app_name="FinancialAnalyst",
        agent=root_agent,
        session_service=session_service,
    )

    # Prepare the user message in the format ADK expects
    user_query = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Analyze my portfolio risk, performance, diversification, "
                    "and recent news, then provide clear recommendations."
                )
            )
        ],
    )

    print("\n--- 🧠 ANALYST IS THINKING ---\n")

    # Stream events from the orchestrator, printing any text parts.
    async for event in runner.run_async(
        user_id="unique_user_id",
        session_id="unique_session_id",
        new_message=user_query,
    ):
        content = getattr(event, "content", None)
        if content and getattr(content, "parts", None):
            for part in content.parts:
                if getattr(part, "text", None):
                    print(f"🤖 Agent: {part.text}")

    await kite_toolset.close()
    print("\n\n--- ✅ ANALYSIS COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(main())