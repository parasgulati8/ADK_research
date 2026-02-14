"""
GitHub: repository management (clone, issues, PRs) for agents.
"""

import os
from pathlib import Path
from typing import Any, Optional


class GitHubClient:
    """Wrapper for GitHub API and git operations."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"

    def clone(self, repo: str, target_dir: Path) -> Path:
        """Clone repository to target_dir. Uses GITHUB_TOKEN for private repos."""
        raise NotImplementedError("GitHubClient.clone not yet implemented")

    def create_issue(self, owner: str, repo: str, title: str, body: str) -> dict[str, Any]:
        """Create a GitHub issue."""
        raise NotImplementedError("GitHubClient.create_issue not yet implemented")

    def create_pr(self, owner: str, repo: str, head: str, base: str, title: str, body: str) -> dict[str, Any]:
        """Create a pull request."""
        raise NotImplementedError("GitHubClient.create_pr not yet implemented")

    def get_file(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
        """Get file contents from repo."""
        raise NotImplementedError("GitHubClient.get_file not yet implemented")
