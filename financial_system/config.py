"""
Central configuration for the financial_system package.

These constants are intended to be imported by agents and tools so that
behavior (like max holdings to analyze) can be tuned in one place.
"""

# Maximum number of holdings the LLM should reason about in detail
MAX_HOLDINGS: int = 50

# Maximum number of news articles to fetch per ticker/sector
MAX_NEWS_PER_TARGET: int = 5

# Default lookback window for news queries (in days)
NEWS_DAYS_BACK: int = 3

# Default model name for LLM agents (can be overridden per-agent)
DEFAULT_MODEL_NAME: str = "gemini-2.0-flash-lite"

