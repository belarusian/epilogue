# TICKET-055: No test coverage for the CLI's I/O error paths (directory / invalid UTF-8 / unreadable)
**Status: CLOSED (Cycle 24) — superseded by TICKET-065 (Cycle 20, PR #23).** All three I/O failure modes are now pinned by tests in `tests/test_cli.py`: `test_log_directory_is_usage_error` (exit 2, "not a regular file", no traceback), `test_invalid_utf8_log_returns_three` (exit 3, "could not read log", no traceback), and `test_unreadable_log_returns_three` (exit 3, chmod 000, no traceback). This ticket is a duplicate of the already-closed 065; no code change was needed in Cycle 24.


## Title
`tests/test_cli.py` covers the happy path, missing/invalid arguments, an invalid
range, a missing log path, and the no-cycles-in-range / no-matching-status exit
codes. It has **no** test for the I/O failure modes that reach the unguarded
`read_text` (`cli.py:130`): a directory as `--log`, an invalid-UTF-8 log, and an
unreadable (`chmod 000`) log. These are exactly the paths behind TICKET-051 and
TICKET-052, and they are currently untested.

## Evidence
`tests/test_cli.py` test inventory (grep of `def test`):
    test_help_exits_zero, test_missing_required_args_is_nonzero,
    test_invalid_range_from_greater_than_to_is_nonzero,
    test_missing_log_path_is_nonzero, test_success_renders_changelog_to_stdout,
    test_no_cycles_in_range_returns_one_and_stderr_message,
    test_project_is_reflected_in_output, test_empty_log_file_returns_one,
    test_preamble_only_log_returns_one, test_negative_from_with_in_range_cycle_returns_zero,
    ... (json, status, range-filter tests) ...

A grep for the relevant terms across `tests/` finds nothing:
    $ grep -rn "is_dir\|IsADirectory\|UnicodeDecode\|PermissionError\|read_text\|chmod\|0o000\|000" tests/
    (no matches)

The only log-path error tested is `test_missing_log_path_is_nonzero`
(`tests/test_cli.py:66`), which exercises the `exists()` guard for a path that
does not exist — not a path that exists but cannot be read as a UTF-8 file.

## Impact
- The crashes in TICKET-051 (uncaught `IsADirectoryError` / `UnicodeDecodeError`
  / `PermissionError`) and the exit-code collision in TICKET-052 are not pinned
  by any test, so a regression (or a fix) would not be caught by the gate.
- The gate (`pytest && ruff && mypy`) is green today precisely because these
  paths are never exercised; the suite gives false confidence that the CLI's
  error handling is complete.

## Suggestion
Add tests in `tests/test_cli.py` (using `tmp_path` and `capsys`):
- a directory passed as `--log` -> assert the documented exit code and a clean
  stderr message (no traceback);
- a log file written with a non-UTF-8 byte -> assert the documented exit code
  and a clean stderr message;
- a `chmod 0o000` file -> assert the documented exit code and a clean stderr
  message (skip on platforms where `chmod 0` does not deny access, e.g. running
  as root).
These tests should assert the exit code chosen when TICKET-052 is resolved and
should fail (red) against the current code, documenting the gap.
