"""
Structure of the Research-to-Dev handoff state.
Used by StateManager and Orchestrator.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResearchDevState(BaseModel):
    """Full state passed between Research and Development wings."""
    query: str = ""
    raw_findings: list[dict[str, Any]] = Field(default_factory=list)
    technical_direction: dict[str, Any] = Field(default_factory=dict)
    trd: dict[str, Any] = Field(default_factory=dict)
    code_artifacts: list[str] = Field(default_factory=list)  # paths or commit refs
    review_report: Optional[dict[str, Any]] = None
    traceability_links: list[dict[str, str]] = Field(default_factory=list)
