"""
Research Analyst: assists Lead Analyst in analyzing and structuring research.
"""

from typing import Any, Optional


class ResearchAnalyst:
    """Analyzes and structures research outputs; extracts key facts for the Lead Analyst."""

    def __init__(self, system_prompt: Optional[str] = None) -> None:
        self.system_prompt = system_prompt or "You are a Research Analyst."

    def analyze(self, raw_findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Structure raw findings into key facts and themes for the Lead Analyst."""
        raise NotImplementedError("Analyst.analyze not yet implemented")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run the analyst on given context; return structured analysis."""
        return self.analyze(context.get("raw_findings", []))
