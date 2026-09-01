"""Tests for the ``python -m epilogue`` entry point (subprocess).

These tests invoke the real entry point as a subprocess to prove that
``sys.exit(main())`` in ``epilogue/__main__.py`` works end-to-end.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_epilogue(*args: str) -> subprocess.CompletedProcess[str]:
    """Run ``python -m epilogue`` with the given args as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "epilogue", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_happy_path_exit_zero_and_changelog_on_stdout(
    tmp_path: Path,
) -> None:
    """In-range cycles produce a changelog on stdout and exit 0."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: Bootstrap\n"
        "- did the thing\n"
        "\n"
        "## Cycle 2: Build\n"
        "- did more\n",
        encoding="utf-8",
    )
    result = _run_epilogue(
        "--project", "demo", "--from", "1", "--to", "2", "--log", str(log),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "# demo" in result.stdout
    assert "## Cycle 1: Bootstrap" in result.stdout
    assert "## Cycle 2: Build" in result.stdout
    assert "- did the thing" in result.stdout
    assert "- did more" in result.stdout


def test_no_cycles_in_range_exit_one_and_stderr(
    tmp_path: Path,
) -> None:
    """Out-of-range query produces exit 1 and a message on stderr."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: Bootstrap\n"
        "- did the thing\n",
        encoding="utf-8",
    )
    result = _run_epilogue(
        "--project", "demo", "--from", "5", "--to", "10", "--log", str(log),
    )
    assert result.returncode == 1
    assert "no cycles" in result.stderr.lower() or "No cycles" in result.stderr


def test_usage_error_missing_args_exit_two() -> None:
    """Missing required arguments produce exit 2 (argparse usage error)."""
    result = _run_epilogue("--project", "demo")
    assert result.returncode == 2
    assert "usage" in result.stderr.lower() or "required" in result.stderr.lower()
