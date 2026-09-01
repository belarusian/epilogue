"""Command-line interface for epilogue.

This module provides the named CLI surface for the mission:

    epilogue --project <name> --from <n> --to <m> --log <path>

It parses and validates its arguments, then reports that the core
parse-to-render capability is still pending (a later Build phase). This is
honest scaffolding: the CLI shell exists and is testable, but it does not
pretend to render changelogs yet.

The module is stdlib-only and fully typed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Distinct non-zero exit code for the "core capability pending" state.
# Deliberately NOT 2: argparse reserves 2 for usage errors (missing/invalid
# arguments, an invalid cycle range, a missing log path). Using a different
# code keeps the pending-capability path distinguishable by exit code alone.
PENDING_EXIT_CODE = 3

PENDING_MESSAGE = (
    "epilogue: core capability pending (Build phase). "
    "Argument parsing and validation succeeded, but parse-to-render is not "
    "implemented yet."
)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the epilogue CLI.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="epilogue",
        description=(
            "Render release-note-style changelogs from a project cycle log "
            "for a range of cycles."
        ),
    )
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Name of the project the cycle log belongs to.",
    )
    parser.add_argument(
        "--from",
        dest="from_cycle",
        type=int,
        required=True,
        help="First cycle number (inclusive) to render.",
    )
    parser.add_argument(
        "--to",
        dest="to_cycle",
        type=int,
        required=True,
        help="Last cycle number (inclusive) to render.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        required=True,
        help="Path to the project cycle log file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the epilogue CLI.

    Args:
        argv: The command-line arguments (excluding the program name). When
            ``None``, ``sys.argv[1:]`` is used.

    Returns:
        A process exit code. ``0`` on ``--help``; ``2`` for usage errors
        (missing/invalid arguments, an invalid cycle range, or a missing log
        path); ``3`` for the pending-capability path (distinct from usage errors,
        and also reported on stderr).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.from_cycle > args.to_cycle:
        parser.error(
            f"invalid cycle range: --from ({args.from_cycle}) must be <= "
            f"--to ({args.to_cycle})"
        )

    if not args.log.exists():
        parser.error(f"log path does not exist: {args.log}")

    # Validation succeeded. The core parse-to-render capability is not yet
    # implemented (a later Build phase), so report that honestly.
    print(PENDING_MESSAGE, file=sys.stderr)
    return PENDING_EXIT_CODE
