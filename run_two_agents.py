import os
import re
import webbrowser
import asyncio
import traceback
import logging
import json
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams
from google.genai import types

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("two-agents")

# Load env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in environment")

# Read kite access token
with open("access_token.txt", "r") as f:
    valid_token = f.read().strip()

params = SseConnectionParams(
    url="https://mcp.kite.trade/sse",
    headers={
        "Authorization": f"Bearer {valid_token}",
        "X-Kite-API-Key": os.getenv("KITE_API_KEY"),
    },
    timeout=120,
)

async def find_tool(tools, name):
    for t in tools:
        # try name attr first
        if getattr(t, 'name', None) == name or getattr(t, 'id', None) == name:
            return t
        # fallback inspect raw_mcp_tool if present
        raw = getattr(t, 'raw_mcp_tool', None)
        if raw and getattr(raw, 'name', None) == name:
            return t
    return None

async def interactive_login(team):
    login_tool = await find_tool(team.tools, 'login')
    if not login_tool:
        logger.warning('No login tool found')
        return False

    logger.info('Invoking login tool to obtain URL...')
    try:
        result = await login_tool.run_async(args={}, tool_context=None)
    except Exception as e:
        logger.exception('login_tool.run_async failed')
        return False

    # extract URL
    url = None
    if isinstance(result, dict) and 'content' in result:
        for item in result['content']:
            if isinstance(item, dict):
                text = item.get('text')
                if not text:
                    continue
                m = re.search(r'https?://[^\s)\]]+', text)
                if m:
                    url = m.group(0)
                    break
    if url:
        logger.info('Opening browser to: %s', url)
        webbrowser.open(url)
        input('After completing browser login press Enter to continue...')
        return True
    else:
        logger.warning('Login tool returned no URL. Result: %s', result)
        return False

async def run_agent_task(team, agent_name, prompt):
    logger.info('Starting agent task: %s', agent_name)
    agent = LlmAgent(
        name=agent_name,
        model="gemini-1.5-flash-8b",
        tools=team.tools,
        instruction=prompt
    )
    runner = Runner(app_name=agent_name, agent=agent, session_service=team.session_service)

    # create or reuse a session for this agent using the shared session_service
    session = await team.session_service.create_session(app_name=agent_name, user_id='analyst')

    try:
        async for event in runner.run_async(new_message=types.Content(role='user', parts=[types.Part(text=prompt)]), user_id='analyst', session_id=session.id):
            # log raw event for debugging
            logger.debug('Event: %s', event)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    # function call parts
                    if getattr(part, 'function_call', None):
                        fc = part.function_call
                        logger.info('[Function call requested] %s', getattr(fc, 'name', None))
                    # text parts
                    if getattr(part, 'text', None):
                        print(part.text, end='', flush=True)
        print('\n')
    except Exception as e:
        logger.exception('Agent task %s failed', agent_name)
        raise


async def fetch_and_total_holdings(team):
    """Call the get_holdings tool directly and compute total market value."""
    get_holdings_tool = await find_tool(team.tools, 'get_holdings')
    if not get_holdings_tool:
        logger.warning('get_holdings tool not found')
        return None, []

    try:
        result = await get_holdings_tool.run_async(args={}, tool_context=None)
    except Exception:
        logger.exception('get_holdings.run_async failed')
        return None, []

    # result expected to be dict with 'content' -> list -> item with 'text' containing JSON array
    holdings = []
    try:
        if isinstance(result, dict) and 'content' in result:
            for item in result['content']:
                text = item.get('text') if isinstance(item, dict) else None
                if not text:
                    continue
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        holdings.extend(parsed)
                except Exception:
                    # ignore parse errors
                    logger.debug('Failed to json-decode holdings text')
        # compute total value
        total = 0.0
        for h in holdings:
            qty = h.get('quantity', 0) or 0
            price = h.get('last_price') if h.get('last_price') is not None else h.get('price', 0)
            try:
                total += float(qty) * float(price)
            except Exception:
                pass
        return total, holdings
    except Exception:
        logger.exception('Error parsing holdings result')
        return None, []

async def main():
    team = None
    try:
        logger.info('Initializing McpToolset...')
        kite_toolset = McpToolset(connection_params=params)
        tools = await kite_toolset.get_tools()
        logger.info('Found %d tools', len(tools))

        # Build a minimal team-like object with shared session service
        team = type('T', (), {})()
        team.kite_toolset = kite_toolset
        team.tools = tools
        team.session_service = InMemorySessionService()
        team.session = await team.session_service.create_session(app_name='TwoAgent', user_id='analyst')

        # interactive login
        ok = await interactive_login(team)
        if not ok:
            logger.warning('Login did not complete; continuing may fail')

        # Run DataFetcher
        await run_agent_task(team, 'DataFetcher', 'Fetch holdings, positions, margins and recent trades. Use get_holdings, get_positions, get_margins, get_trades tools.')

        # After DataFetcher: fetch holdings and trades to supply numeric totals to the RiskAnalyzer
        total_value, holdings = await fetch_and_total_holdings(team)

        # try to fetch recent trades so we can tell the risk agent if there are none
        trades_tool = await find_tool(team.tools, 'get_trades')
        recent_trades = []
        if trades_tool:
            try:
                tresult = await trades_tool.run_async(args={}, tool_context=None)
                if isinstance(tresult, dict) and 'content' in tresult:
                    for item in tresult['content']:
                        text = item.get('text') if isinstance(item, dict) else None
                        if not text:
                            continue
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, list):
                                recent_trades.extend(parsed)
                        except Exception:
                            pass
            except Exception:
                logger.exception('get_trades.run_async failed')

        trades_note = 'No recent trades.' if not recent_trades else f'{len(recent_trades)} recent trades found.'

        if total_value is None:
            risk_prompt = 'Analyze risk: identify concentration risks (>20%), sector exposure, and suggest mitigations based on holdings data. (Portfolio total value not available.)'
        else:
            # build small holdings summary
            summary_items = []
            for h in holdings[:20]:
                sym = h.get('tradingsymbol') or h.get('instrument_token')
                qty = h.get('quantity', 0)
                price = h.get('last_price') if h.get('last_price') is not None else h.get('price', 0)
                summary_items.append(f"{sym}:{qty}@{price}")
            holdings_summary = ', '.join(summary_items)
            risk_prompt = (f"Analyze risk: identify concentration risks (>20%), sector exposure, and suggest mitigations based on holdings data. "
                           f"Total portfolio value: {total_value:.2f}. Holdings (first 20): {holdings_summary}. {trades_note}")

        # Run RiskAnalyzer with enriched prompt
        await run_agent_task(team, 'RiskAnalyzer', risk_prompt)

    except Exception:
        logger.exception('Fatal error in two-agent runner')
    finally:
        if team is not None:
            try:
                await team.kite_toolset.close()
            except Exception:
                logger.exception('Error closing kite_toolset')

if __name__ == '__main__':
    asyncio.run(main())
