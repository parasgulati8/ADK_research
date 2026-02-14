"""
Browser / Web: Google Search and web scraping for research agents.
"""

import os
from typing import Any, Optional

# Use GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX from env; or requests/beautifulsoup for scraping


def search_web(query: str, max_results: int = 10, api_key: Optional[str] = None, cx: Optional[str] = None) -> list[dict[str, Any]]:
    """Call Google Custom Search API; return list of {title, link, snippet}."""
    api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = cx or os.getenv("GOOGLE_SEARCH_CX")
    if not api_key or not cx:
        return []  # or raise ValueError("Missing Google Search config")
    # TODO: implement requests.get to Custom Search JSON API
    raise NotImplementedError("search_web not yet implemented")


def scrape_url(url: str, user_agent: Optional[str] = None) -> dict[str, Any]:
    """Fetch URL and return parsed content (title, text, links) for research vault."""
    # TODO: requests + BeautifulSoup or similar
    raise NotImplementedError("scrape_url not yet implemented")
