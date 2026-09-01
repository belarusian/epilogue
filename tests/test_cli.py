"""Tests for the epilogue CLI shell (argparse + validation + pending path).

These tests exercise the CLI surface without invoking the real process:
``main`` is called in-process and ``SystemExit`` is caught where argparse
raises it (``--help`` and usage errors).
"""

from __future__ import annotations

import pytest
from pathlib import Path

from epilogue.cli import PENDING_EXIT_CODE, PENDING_MESSAGE, main


def test_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` prints usage and exits 0."""
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "--project" in out
    assert "--from" in out
    assert "--to" in out
    assert "--log" in out


def test_missing_required_args_is_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    """Omitting a required argument is a usage error (non-zero exit)."""
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "required" in err.lower()


def test_invalid_range_from_greater_than_to_is_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--from`` greater than ``--to`` is rejected (non-zero exit)."""
    log = tmp_path / "log.md"
    log.write_text("## Cycle 1\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--project",
                "demo",
                "--from",
                "5",
                "--to",
                "3",
                "--log",
                str(log),
            ]
        )
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "invalid cycle range" in err


def test_missing_log_path_is_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ``--log`` path that does not exist is rejected (non-zero exit)."""
    missing = tmp_path / "does-not-exist.md"
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--project",
                "demo",
                "--from",
                "1",
                "--to",
                "2",
                "--log",
                str(missing),
            ]
        )
    assert excinfo.value.code != 0
    err = capsys.readouterr().err
    assert "does not exist" in err


def test_pending_capability_returns_distinct_code_and_message(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Valid args reach the pending-capability path: distinct code + stderr."""
    log = tmp_path / "log.md"
    log.write_text("## Cycle 1\n", encoding="utf-8")
    code = main(
        [
            "--project",
            "demo",
            "--from",
            "1",
            "--to",
            "2",
            "--log",
            str(log),
        ]
    )
    assert code == PENDING_EXIT_CODE
    assert code != 0
    err = capsys.readouterr().err
    assert PENDING_MESSAGE in err
    assert "pending" in err.lower()
