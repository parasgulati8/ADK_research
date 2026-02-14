"""
Technical Requirements Document (TRD) schema.
Used by Architect output and Coder/QA input.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TRDModule(BaseModel):
    """A single module or component in the TRD."""
    name: str = ""
    description: str = ""
    interfaces: list[str] = Field(default_factory=list)
    implementation_notes: Optional[str] = None


class TRD(BaseModel):
    """Technical Requirements Document produced by the Architect."""
    title: str = ""
    summary: str = ""
    modules: list[TRDModule] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    non_functional: dict[str, Any] = Field(default_factory=dict)
