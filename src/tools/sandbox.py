"""
Sandbox: isolated environment for safe code execution (e.g. Coder output validation).
"""

import subprocess
from pathlib import Path
from typing import Any, Optional


def run_in_sandbox(
    command: list[str],
    cwd: Optional[Path] = None,
    timeout_seconds: int = 30,
    env: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """
    Run a command in an isolated way (subprocess with timeout).
    Returns {stdout, stderr, returncode, timed_out}.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
            env={**(env or {})} if env else None,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": (e.stdout or ""),
            "stderr": (e.stderr or ""),
            "returncode": -1,
            "timed_out": True,
        }
