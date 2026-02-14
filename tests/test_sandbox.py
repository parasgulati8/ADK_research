"""Unit tests for sandbox tool."""

from pathlib import Path

import pytest

from src.tools.sandbox import run_in_sandbox


def test_run_in_sandbox_success() -> None:
    result = run_in_sandbox(["echo", "hello"], timeout_seconds=5)
    assert result["returncode"] == 0
    assert "hello" in result["stdout"]
    assert result["timed_out"] is False


def test_run_in_sandbox_failure() -> None:
    result = run_in_sandbox(["false"], timeout_seconds=5)
    assert result["returncode"] != 0
    assert result["timed_out"] is False


def test_run_in_sandbox_cwd() -> None:
    result = run_in_sandbox(["pwd"], cwd=Path.cwd(), timeout_seconds=5)
    assert result["returncode"] == 0
    assert str(Path.cwd()) in result["stdout"]
