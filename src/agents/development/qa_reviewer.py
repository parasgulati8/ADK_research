"""
QA Reviewer: reviews code for correctness and alignment with TRD.
"""

from pathlib import Path
from typing import Any, Optional

# from src.schemas.trd import TRD
# from src.tools.sandbox import run_in_sandbox


class QAReviewer:
    """Verifies implemented code matches TRD and project conventions."""

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        self.workspace_dir = workspace_dir or Path("workspace/generated_app")
        self.system_prompt = system_prompt or "You are the QA Reviewer."

    def review(self, trd: dict[str, Any], code_artifacts: dict[str, Any]) -> dict[str, Any]:
        """Check code against TRD; return issues and suggestions."""
        raise NotImplementedError("QAReviewer.review not yet implemented")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run the reviewer; return review report."""
        return self.review(
            context.get("trd", {}),
            context.get("code_artifacts", {}),
        )
