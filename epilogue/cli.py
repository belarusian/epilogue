"""Command-line interface for epilogue.

This module provides the named CLI surface for the mission:

    epilogue --project <name> --from <n> --to <m> --log <path> [--format {text,json}]

It parses and validates its arguments, then runs the real parse-to-render
pipeline: it reads the cycle log, parses it into cycles, filters to the
requested ``--from``/``--to`` range, renders the output in the requested
``--format`` (human-readable ``text`` changelog by default, or machine-readable
``json``), and prints it to stdout.

Exit-code contract (documented on :func:`main`):

* ``0`` — successful render; the changelog is printed to stdout.
* ``1`` — no cycles fall within the requested range; a clear message is
  printed to stderr (this holds for BOTH the ``text`` and ``json`` formats).
* ``2`` — usage errors (missing/invalid arguments, an invalid cycle range, or
  a missing log path), raised by argparse.

The module is stdlib-only and fully typed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from epilogue.parser import parse_log
from epilogue.render import render, render_json


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
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["text", "json"],
        default="text",
        help=(
            "Output format: 'text' (human-readable changelog, the default) "
            "or 'json' (machine-readable document)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the epilogue CLI.

    Args:
        argv: The command-line arguments (excluding the program name). When
            ``None``, ``sys.argv[1:]`` is used.

    Returns:
        A process exit code. ``0`` on a successful render (the output is
        printed to stdout in the requested ``--format``); ``1`` when no cycles
        fall within the requested range (a clear message is printed to stderr,
        for both formats); ``2`` for usage errors (missing/invalid arguments,
        an invalid cycle range, an invalid ``--format`` value, or a missing log
        path), raised by argparse.
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

    text = args.log.read_text(encoding="utf-8")
    cycles = parse_log(text)
    selected = [c for c in cycles if args.from_cycle <= c.number <= args.to_cycle]

    if not selected:
        print(
            f"epilogue: no cycles in range {args.from_cycle}..{args.to_cycle} "
            f"in {args.log}",
            file=sys.stderr,
        )
        return 1

    if args.output_format == "json":
        out = render_json(selected, project=args.project)
    else:
        out = render(selected, project=args.project)
    print(out)
    return 0
