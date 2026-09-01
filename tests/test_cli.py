"""Tests for the epilogue CLI (argparse + validation + parse-to-render).

These tests exercise the CLI surface without invoking the real process:
``main`` is called in-process and ``SystemExit`` is caught where argparse
raises it (``--help`` and usage errors). The success and "no cycles in range"
paths are covered with small temp logs written to ``tmp_path``; no real
ground-truth log file is read.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from epilogue.cli import main


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


def test_success_renders_changelog_to_stdout(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Valid args with in-range cycles render the changelog to stdout, exit 0."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: A\n"
        "- added the data model\n"
        "## Cycle 2: B\n"
        "- a no-op: nothing changed\n",
        encoding="utf-8",
    )
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
    assert code == 0
    out = capsys.readouterr().out
    # The project title and both cycle headers are present on stdout.
    assert "# demo" in out
    assert "## Cycle 1: A" in out
    assert "## Cycle 2: B" in out
    # The status sub-sections are truthfully distinguished.
    assert "### Merged" in out
    assert "### No-ops" in out
    assert "added the data model" in out
    assert "a no-op: nothing changed" in out


def test_no_cycles_in_range_returns_one_and_stderr_message(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cycles outside --from/--to yield the distinct code 1 and a stderr message."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 5: X\n"
        "- something merged\n",
        encoding="utf-8",
    )
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
    # Distinct from both success (0) and usage errors (2).
    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no cycles in range" in captured.err
    assert "1..2" in captured.err


def test_project_is_reflected_in_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The --project value is emitted as the top-level title (not discarded)."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: A\n"
        "- added the data model\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project",
            "my-special-project",
            "--from",
            "1",
            "--to",
            "1",
            "--log",
            str(log),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "# my-special-project" in out
    # The title is the first line of the rendered changelog.
    assert out.splitlines()[0] == "# my-special-project"
