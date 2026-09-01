# TICKET-065: Documented exit-code contract omits I/O failures; no test coverage for any I/O failure mode
**Status: CLOSED (Cycle 20, PR #23).**

## Title
The documented exit-code contract never describes what happens when the log
exists but cannot be read (directory, invalid UTF-8, unreadable), and
`tests/test_cli.py` has no test for any of those failure modes.

## Evidence
- The contract in `README.md` (lines 56-58, 233-235) and `epilogue/cli.py`
  (docstring lines 14-22, 108-116) enumerates only exit codes 0, 1, and 2. It
  never mentions the behavior when the log exists but cannot be read.
- `README.md` line 57 says exit 2 covers "missing log"; line 58 says exit 1 is
  "no cycles ... (a clear message is printed to stderr)". Neither describes the
  actual I/O-failure behavior (raw traceback, exit 1).
- `tests/test_cli.py` has no test for any I/O failure mode. The search
  `grep -n "directory\|IsADirectory\|UnicodeDecode\|PermissionError\|read_text\|is_file\|OSError\|traceback" tests/test_cli.py`
  returns nothing. The existing tests cover: `--help` (exit 0), missing required
  args (non-zero), invalid range (non-zero), missing log path (non-zero,
  "does not exist"), success (exit 0), no-cycles-in-range (exit 1), and the
  status-filter paths. None exercise a directory, an invalid-UTF-8 file, or an
  unreadable file.

## Impact
- The contract is incomplete: a reader of the README cannot predict the
  behavior for the three most likely real-world I/O mistakes.
- The behavior is untested, so the current crash (or a regression) would not be
  caught by the gate.
- The documented "clear message to stderr" for exit 1 is contradicted by the
  actual traceback output, so the docs and the code disagree.

## Suggestion
- Add a test for each I/O failure mode (directory, invalid UTF-8, unreadable)
  asserting: (a) no traceback on stderr, (b) a clean one-line message, (c) the
  documented exit code. For the unreadable case, guard with
  `@pytest.mark.skipif(os.geteuid() == 0, reason="root can read mode-000 files")`
  since root bypasses the permission check.
- Update `README.md` and the `epilogue/cli.py` docstrings to document the
  I/O-failure exit code (see TICKET-064) so the contract matches the code.
