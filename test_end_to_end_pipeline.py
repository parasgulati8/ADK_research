"""
End-to-end test for the 4-agent financial_system pipeline.

This script:
- Initializes the Kite MCP toolset and performs login.
- Injects MCP tools + calculate_portfolio_metrics into PortfolioDataAgent.
- Runs the SequentialAgent orchestrator over a sample user query.
- Captures all JSON code blocks produced by the agents and validates them
  against the Pydantic schemas:
    - PortfolioSummary
    - RiskPerformanceSummary
    - NewsSummary
    - RecommendationPlan

Run with:
    python test_end_to_end_pipeline.py
"""

import asyncio
import json
import os
import re
import webbrowser
from typing import List

from dotenv import load_dotenv
from google.genai import types

from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import InvocationContext, Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

from financial_system.agents.orchestrator import root_agent
from financial_system.schemas import (
    NewsSummary,
    PortfolioSummary,
    RecommendationPlan,
    RiskPerformanceSummary,
)
from financial_system.tools import calculate_portfolio_metrics


async def interactive_login(mcp_tools) -> None:
    """Re-use the same login pattern as financial_system.main."""
    from google.adk.tools import ToolContext  # local import to avoid confusion

    login_tool = next((t for t in mcp_tools if "login" in t.name.lower()), None)
    if not login_tool:
        print("No login tool found; proceeding without explicit login.")
        return

    print("🔑 Initiating Kite Login (test)...")
    current_session = Session(
        id="e2e_login_session",
        appName="FinancialSystemE2ETest",
        userId="test_user",
    )
    invocation_context = InvocationContext(
        invocation_id="e2e_login_task",
        agent=Agent(name="LoginAgent", description="Handle authentication for E2E test"),
        session=current_session,
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
    )
    tool_context = ToolContext(invocation_context=invocation_context)
    result = await login_tool.run_async(args={}, tool_context=tool_context)
    
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
        print(f"Response (first 1000 chars): {str(result)[:1000]}")
    
    input("\n🚀 After completing login in your browser, press Enter to continue...")


def extract_json_blocks(text: str) -> List[str]:
    """
    Extract all ```json ... ``` blocks from the combined agent output.
    Returns the raw JSON strings (without fences).
    """
    blocks: List[str] = []
    pattern = re.compile(r"```json\s*(.*?)```", re.DOTALL | re.IGNORECASE)
    for match in pattern.finditer(text):
        blocks.append(match.group(1).strip())
    return blocks


async def main() -> None:
    load_dotenv()

    with open("access_token.txt", "r", encoding="utf-8") as f:
        valid_token = f.read().strip()

    params = SseConnectionParams(
        url="https://mcp.kite.trade/sse",
        headers={
            "Authorization": f"Bearer {valid_token}",
            "X-Kite-API-Key": os.getenv("KITE_API_KEY"),
        },
    )

    print("📡 [E2E] Connecting to Kite MCP Server...")
    kite_toolset = McpToolset(connection_params=params)
    mcp_tools = await kite_toolset.get_tools()

    await interactive_login(mcp_tools)

    # Inject tools into PortfolioDataAgent
    p_agent = next(a for a in root_agent.sub_agents if a.name == "PortfolioDataAgent")
    p_agent.tools = mcp_tools + [calculate_portfolio_metrics]

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="FinancialAnalystE2E",
        user_id="e2e_user",
        session_id="e2e_session",
    )

    runner = Runner(
        app_name="FinancialAnalystE2E",
        agent=root_agent,
        session_service=session_service,
    )

    user_query = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Run a full portfolio analysis including risk, performance, "
                    "diversification, news, and final recommendations."
                )
            )
        ],
    )

    print("\n--- 🧪 E2E PIPELINE RUNNING ---\n")
    collected_text_chunks: List[str] = []

    async for event in runner.run_async(
        user_id="e2e_user",
        session_id="e2e_session",
        new_message=user_query,
    ):
        content = getattr(event, "content", None)
        if content and getattr(content, "parts", None):
            for part in content.parts:
                if getattr(part, "text", None):
                    text = part.text
                    collected_text_chunks.append(text)
                    print(f"🤖 Agent: {text}")

    await kite_toolset.close()

    combined = "\n".join(collected_text_chunks)
    json_blocks = extract_json_blocks(combined)

    if not json_blocks:
        raise RuntimeError("No JSON code blocks found in agent output.")

    print(f"\nFound {len(json_blocks)} JSON block(s) from agents.")

    # We expect 4 JSON blocks in order: PortfolioSummary, RiskPerformanceSummary,
    # NewsSummary, RecommendationPlan. We validate in that order but log any mismatches.
    validators = [
        ("PortfolioSummary", PortfolioSummary),
        ("RiskPerformanceSummary", RiskPerformanceSummary),
        ("NewsSummary", NewsSummary),
        ("RecommendationPlan", RecommendationPlan),
    ]

    for i, (label, model) in enumerate(validators):
        if i >= len(json_blocks):
            print(f"⚠️ Missing JSON block for {label} (only {len(json_blocks)} blocks found).")
            break
        raw_json = json_blocks[i]
        try:
            instance = model.model_validate_json(raw_json)
            print(f"✅ {label} validation passed.")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ {label} validation FAILED: {exc}")
            print("Raw JSON was:")
            print(raw_json)

    print("\n--- ✅ E2E TEST COMPLETE ---")


if __name__ == "__main__":
    asyncio.run(main())

