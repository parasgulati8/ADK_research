"""
Coder: implements code according to the TRD in the workspace.
"""

from pathlib import Path
from typing import Any, Optional

# from src.schemas.trd import TRD
# from src.tools.sandbox import run_in_sandbox


class Coder:
    """Implements features and modules as specified in the TRD."""

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        self.workspace_dir = workspace_dir or Path("workspace/generated_app")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.system_prompt = system_prompt or "You are the Coder."

    def implement(self, trd: dict[str, Any]) -> dict[str, Any]:
        """Generate code per TRD into workspace/generated_app."""
        raise NotImplementedError("Coder.implement not yet implemented")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Run the coder; return list of created/modified files."""
        return self.implement(context.get("trd", {}))
