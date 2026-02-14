"""
Search Specialist: executes web and literature search; feeds raw data to the analyst.
"""

from typing import Any, Optional

# from src.tools.browser import search, scrape


class SearchSpecialist:
    """Uses search and scraping tools to gather papers, docs, and web content."""

    def __init__(self, system_prompt: Optional[str] = None) -> None:
        self.system_prompt = system_prompt or "You are the Search Specialist."

    def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Run search (e.g. Google Search API) and return ranked snippets."""
        raise NotImplementedError("SearchSpecialist.search not yet implemented")

    def run(self, query: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Execute search and return raw findings for the analyst."""
        raw = self.search(query)
        return {"query": query, "raw_findings": raw}
