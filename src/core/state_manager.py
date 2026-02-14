"""
State Manager: handles the "Context Gap" and state persistence.
Bridges research outputs (insights, TRD) to development inputs so agents stay in sync.
"""

from pathlib import Path
from typing import Any, Optional

# from src.schemas.state import ResearchDevState


class StateManager:
    """Handles context gap and state persistence across Research and Development wings."""

    def __init__(self, persist_dir: Optional[Path] = None) -> None:
        self.persist_dir = persist_dir or Path("data/traceability")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, Any] = {}

    def get_state(self) -> dict[str, Any]:
        """Return current in-memory state (research insights, TRD, code refs)."""
        return self._state.copy()

    def update_state(self, updates: dict[str, Any]) -> None:
        """Merge updates into current state."""
        self._state.update(updates)

    def persist_state(self, label: Optional[str] = None) -> Path:
        """Write state to disk (e.g. JSON in data/traceability) for traceability."""
        import json
        name = label or "state"
        path = self.persist_dir / f"{name}.json"
        path.write_text(json.dumps(self._state, indent=2))
        return path

    def load_state(self, path: Path) -> dict[str, Any]:
        """Load state from a traceability JSON file."""
        import json
        self._state = json.loads(path.read_text())
        return self.get_state()
