"""Tests for the epilogue CLI (argparse + validation + parse-to-render).

These tests exercise the CLI surface without invoking the real process:
``main`` is called in-process and ``SystemExit`` is caught where argparse
raises it (``--help`` and usage errors). The success and "no cycles in range"
paths are covered with small temp logs written to ``tmp_path``; no real
ground-truth log file is read.
"""

from __future__ import annotations

import json
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


# ---------------------------------------------------------------------------
# Edge-case tests (Cycle 5)
# ---------------------------------------------------------------------------


def test_empty_log_file_returns_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A 0-byte log file yields no cycles -> exit 1."""
    log = tmp_path / "empty.md"
    log.write_bytes(b"")
    code = main(
        [
            "--project", "demo",
            "--from", "1", "--to", "5",
            "--log", str(log),
        ]
    )
    assert code == 1
    err = capsys.readouterr().err
    assert "no cycles" in err.lower() or "No cycles" in err


def test_preamble_only_log_returns_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A log with no '## Cycle' headers yields no cycles -> exit 1."""
    log = tmp_path / "preamble.md"
    log.write_text(
        "# My Project\n"
        "Some preamble text.\n"
        "No cycle headers here.\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project", "demo",
            "--from", "1", "--to", "5",
            "--log", str(log),
        ]
    )
    assert code == 1
    err = capsys.readouterr().err
    assert "no cycles" in err.lower() or "No cycles" in err


def test_negative_from_with_in_range_cycle_returns_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """argparse accepts negative ints; --from -1 --to 2 renders cycles 1 and 2."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: First\n"
        "- alpha\n"
        "\n"
        "## Cycle 2: Second\n"
        "- beta\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project", "demo",
            "--from", "-1", "--to", "2",
            "--log", str(log),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "## Cycle 1: First" in out
    assert "## Cycle 2: Second" in out
    assert "- alpha" in out
    assert "- beta" in out


def test_duplicate_cycle_numbers_both_rendered(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Two '## Cycle 1:' headers produce two cycles; both survive the filter."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: First\n"
        "- alpha\n"
        "\n"
        "## Cycle 1: Second\n"
        "- beta\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project", "demo",
            "--from", "1", "--to", "1",
            "--log", str(log),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    # Both cycles must appear
    assert "## Cycle 1: First" in out
    assert "## Cycle 1: Second" in out
    assert "- alpha" in out
    assert "- beta" in out


# ---------------------------------------------------------------------------
# --format json tests (TICKET-023)
# ---------------------------------------------------------------------------


def test_format_json_success_exit_zero_valid_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--format json with in-range cycles exits 0 and prints valid JSON."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: A\n"
        "- added the data model\n"
        "## Cycle 2: B\n"
        "- a no-op: nothing changed\n"
        "- abandoned the renderer\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project", "demo",
            "--from", "1", "--to", "2",
            "--log", str(log),
            "--format", "json",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    doc = json.loads(out)  # stdout must be valid JSON
    assert doc["project"] == "demo"
    assert [c["number"] for c in doc["cycles"]] == [1, 2]
    assert doc["cycles"][0]["entries"][0] == {
        "description": "added the data model",
        "status": "merged",
    }
    # The three-way distinction is preserved as distinct tokens.
    statuses = [e["status"] for c in doc["cycles"] for e in c["entries"]]
    assert "merged" in statuses
    assert "no_op" in statuses
    assert "not_merged" in statuses


def test_format_json_no_cycles_in_range_exit_one_not_empty_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """JSON path with no cycles in range exits 1 with a stderr message (not
    an empty JSON document + exit 0)."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 5: X\n"
        "- something merged\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project", "demo",
            "--from", "1", "--to", "2",
            "--log", str(log),
            "--format", "json",
        ]
    )
    assert code == 1
    captured = capsys.readouterr()
    # No JSON document is printed to stdout on the no-cycles path.
    assert captured.out == ""
    assert "no cycles in range" in captured.err
    assert "1..2" in captured.err


def test_format_json_invalid_value_is_usage_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An invalid --format value is a usage error (exit 2 via argparse)."""
    log = tmp_path / "log.md"
    log.write_text("## Cycle 1: A\n- x\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "--project", "demo",
                "--from", "1", "--to", "1",
                "--log", str(log),
                "--format", "yaml",
            ]
        )
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "invalid choice" in err


def test_default_format_is_text_backward_compatible(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Omitting --format still yields the human-readable text changelog."""
    log = tmp_path / "log.md"
    log.write_text(
        "## Cycle 1: A\n"
        "- added the data model\n",
        encoding="utf-8",
    )
    code = main(
        [
            "--project", "demo",
            "--from", "1", "--to", "1",
            "--log", str(log),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    # Human-readable markers, not a JSON document.
    assert "# demo" in out
    assert "## Cycle 1: A" in out
    assert "### Merged" in out
    assert out.strip().startswith("# demo")
    # It must NOT be parseable as a JSON document (the text shape is not JSON).
    with pytest.raises(ValueError):
        json.loads(out)
