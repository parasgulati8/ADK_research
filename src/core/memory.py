"""
Memory: long-term vs short-term agent memory.
Long-term = research vault, traceability logs; short-term = current session context.
"""

from pathlib import Path
from typing import Any, Optional

# from src.schemas.state import ...


class Memory:
    """Long-term (vault, traceability) and short-term (session) memory for agents."""

    def __init__(
        self,
        vault_dir: Optional[Path] = None,
        traceability_dir: Optional[Path] = None,
    ) -> None:
        self.vault_dir = vault_dir or Path("data/research_vault")
        self.traceability_dir = traceability_dir or Path("data/traceability")
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.traceability_dir.mkdir(parents=True, exist_ok=True)
        self._short_term: list[dict[str, Any]] = []

    def add_short_term(self, entry: dict[str, Any]) -> None:
        """Append to current session context (e.g. last N messages or facts)."""
        self._short_term.append(entry)

    def get_short_term(self, last_n: Optional[int] = None) -> list[dict[str, Any]]:
        """Return short-term context; optionally last_n entries."""
        if last_n is None:
            return self._short_term.copy()
        return self._short_term[-last_n:]

    def clear_short_term(self) -> None:
        """Reset session context."""
        self._short_term.clear()

    def store_in_vault(self, key: str, data: Any) -> Path:
        """Persist a research artifact (e.g. synthesized doc) in the vault."""
        path = self.vault_dir / f"{key}.json"
        import json
        path.write_text(json.dumps(data, indent=2))
        return path

    def link_traceability(self, research_insight_id: str, commit_or_artifact_id: str) -> None:
        """Record a link from a research insight to a code commit or artifact."""
        import json
        log_path = self.traceability_dir / "links.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "research_insight_id": research_insight_id,
                "commit_or_artifact_id": commit_or_artifact_id,
            }) + "\n")
