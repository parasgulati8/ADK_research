"""
Proper MCP Tool Calling with Session Context
This uses the Runner pattern which maintains session state across tool calls
This script is for testing MCP connection with Kite tool calling using a single LLMAgent
"""
import os
import asyncio
from dotenv import load_dotenv
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json
import webbrowser

load_dotenv()

async def run_with_session_context():
    """Using Runner maintains the session context through tool calls"""
    
    with open("access_token.txt", "r") as f:
        token = f.read().strip()
    
    print("=== Kite MCP with Session Context ===\n")
    print("⚠️  Kite MCP requires browser-based OAuth authentication.")
    print("    The agent will guide you through this.\n")
    
    params = SseConnectionParams(
        url="https://mcp.kite.trade/sse",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Kite-API-Key": os.getenv("KITE_API_KEY"),
        },
        timeout=120
    )
    
    kite_toolset = McpToolset(connection_params=params)
    
    try:
        tools = await asyncio.wait_for(kite_toolset.get_tools(), timeout=60.0)
        print(f"✅ Connected to Kite MCP. {len(tools)} tools available.\n")

        # Create agent with clear instructions
        analyst = LlmAgent(
            name="KiteAssistant",
            model="gemini-2.5-flash",
            tools=tools,
            instruction="""You are a Zerodha Kite assistant. Follow these steps:
1. First, ask the user to click the login link when you call 'login' tool
2. once logged in, proceed with other tools like get_holdings, get_mf_holdings, get_ltp, search_instruments, get_historical_data
"""
#             """You are a Zerodha Kite assistant. Follow these steps:
# 1. First, ask the user to click the login link when you call 'login' tool
# 2. Wait for the user to confirm they completed the login in their browser
# 3. Only after confirmation, proceed with other tools like get_holdings, get_mf_holdings, get_ltp, search_instruments, get_historical_data
# 4. Never assume login is complete without user confirmation
# """
        )
        
        # Runner maintains session state
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="KiteAssistant", 
            user_id="user"
        )
        runner = Runner(
            app_name="KiteAssistant", 
            agent=analyst, 
            session_service=session_service
        )
        
        print("🚀 Starting interactive session...\n")
        print("=" * 60)
        
        # Multi-turn conversation
        user_query = input("\nYou: What would you like to do with your Kite account? \n> ")
        
        async def _execute_tool_call(tool_name, arguments):
            """Execute a tool by name with parsed arguments.
            Returns the raw tool result or raises an exception.
            """
            tool = next((t for t in tools if t.name == tool_name), None)
            if not tool:
                raise RuntimeError(f"Tool not found: {tool_name}")

            # run_async requires args and tool_context
            try:
                result = await tool.run_async(args=(arguments or {}), tool_context=None)
                return result
            except TypeError:
                # Some tool implementations may expect keyword-only args
                return await tool.run_async(args=arguments or {}, tool_context=None)

        async def _handle_event_part(part):
            if hasattr(part, 'text') and part.text:
                print(f"Assistant: {part.text}")
                return

            if not (hasattr(part, 'function_call') and part.function_call):
                return

            tool_name = part.function_call.name
            print(f"\n[Agent requested tool: {tool_name}]")

            # Try to parse arguments if provided
            raw_args = None
            if hasattr(part.function_call, 'arguments') and part.function_call.arguments:
                try:
                    raw_args = json.loads(part.function_call.arguments)
                except Exception:
                    raw_args = {}

            # Define safe vs sensitive tools
            safe_tools = {"get_holdings", "get_positions", "get_profile", "get_quotes", "get_orders", "get_trades", "get_margins", "get_ltp"}
            sensitive_tools = {"place_order", "modify_order", "cancel_order", "place_gtt_order", "modify_gtt_order", "delete_gtt_order"}

            if tool_name == "login":
                # Execute login to obtain the URL, then open in browser and ask for confirmation
                print("Executing login tool to obtain authorization URL...")
                try:
                    login_res = await _execute_tool_call("login", raw_args or {})
                    # attempt to extract URL from response
                    text_parts = None
                    if isinstance(login_res, dict) and "content" in login_res:
                        text_parts = login_res.get("content")
                    if text_parts:
                        url = None
                        for item in text_parts:
                            if item.get("type") == "text" and "http" in item.get("text", ""):
                                # crude URL extraction
                                import re
                                m = re.search(r"https?://[^\")\s]+", item.get("text"))
                                if m:
                                    url = m.group(0)
                                    break
                        if url:
                            print(f"Opening login URL in your browser: {url}")
                            try:
                                webbrowser.open(url)
                            except Exception:
                                print("Failed to open browser automatically. Please open the URL above manually.")
                            input("\nAfter you've completed the login in your browser, press Enter to continue...")
                            return
                    print("Login tool executed; please follow the returned instructions to authenticate.")
                except Exception as e:
                    print(f"Login execution failed: {e}")
                return

            if tool_name in sensitive_tools:
                # Require explicit user confirmation
                confirm = input(f"The agent intends to call a sensitive tool '{tool_name}'. Do you want to proceed? (yes/no): ")
                if confirm.strip().lower() not in ("y", "yes"):
                    print("Skipping sensitive tool call.")
                    return

            if tool_name in safe_tools or tool_name in sensitive_tools:
                print(f"Calling tool '{tool_name}' with args: {raw_args}")
                try:
                    res = await _execute_tool_call(tool_name, raw_args or {})
                    print("Tool result:")
                    print(res)
                except Exception as e:
                    print(f"Tool call failed: {type(e).__name__}: {e}")
                return

            # Unknown tool: just log
            print(f"Tool '{tool_name}' is not in the auto-run safe list. Agent requested it; manual handling required.")

        async for event in runner.run_async(
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_query)]
            ),
            user_id="user",
            session_id=session.id
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    await _handle_event_part(part)
        
        # Allow multi-turn if needed
        print("\n" + "=" * 60)
        while True:
            follow_up = input("\nYou: Any follow-up questions? (type 'exit' to quit)\n> ")
            if follow_up.lower() == 'exit':
                break
            
            async for event in runner.run_async(
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=follow_up)]
                ),
                user_id="user",
                session_id=session.id
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        await _handle_event_part(part)
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
    finally:
        await kite_toolset.close()

if __name__ == "__main__":
    asyncio.run(run_with_session_context())
