# TICKET-051: Unguarded `read_text` crashes the CLI on a directory, invalid UTF-8, or unreadable log
**Status: CLOSED (Cycle 24) — superseded by TICKET-061/062/063 (Cycle 20, PR #23).** The unguarded `read_text` was fixed in Cycle 20: `epilogue/cli.py` now rejects a non-regular-file `--log` as a usage error (exit 2) and catches `OSError`/`UnicodeDecodeError` around `read_text` (exit 3, clean one-line stderr message). This ticket is a duplicate of the already-closed 061/062/063; no code change was needed in Cycle 24.


## Title
`epilogue/cli.py` reads the log with an unguarded `args.log.read_text(encoding="utf-8")`
(`cli.py:130`). The only pre-check is `args.log.exists()` (`cli.py:127`), which is
`True` for a directory and for a file that exists but is unreadable. As a result,
three ordinary inputs crash the CLI with an uncaught Python traceback instead of a
clean error message.

## Evidence
`epilogue/cli.py:127-130`:
    if not args.log.exists():
        parser.error(f"log path does not exist: {args.log}")

    text = args.log.read_text(encoding="utf-8")

`Path.exists()` returns `True` for a directory (`is_file()` is `False`), so the
guard passes and `read_text` raises. Reproduced against the shipped code
(Python 3.10), each case exits `1` with a raw traceback on stderr:

1. **Directory as `--log`** (`--log /tmp/epi_test/dirlog`):
   `IsADirectoryError: [Errno 21] Is a directory` at `cli.py:130`.
2. **Invalid UTF-8** (a log containing byte `0xe9`):
   `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 22:
   invalid continuation byte` at `cli.py:130`.
3. **Unreadable file** (`chmod 000`):
   `PermissionError: [Errno 13] Permission denied` at `cli.py:130`.

None of these is caught anywhere in `main()` (`cli.py:101-158`); the exception
propagates through `__main__.py:13` (`sys.exit(main())`) and Python prints the
full traceback.

## Impact
- The CLI's documented contract (README "Exit codes", `cli.py` module docstring)
  promises clean stderr messages for error conditions. A user who points `--log`
  at a directory, a non-UTF-8 file, or a file they cannot read gets a multi-line
  Python traceback instead of a one-line diagnostic.
- The crash path is reachable in normal use (a directory is a plausible
  `--log` value; a log written by another tool may not be UTF-8).
- The traceback leaks internal paths and the call stack, which is noisy and
  unhelpful for a CLI whose stated goal is a clean, truthful changelog.

## Suggestion
Guard the read. Either (a) require a regular file — replace the `exists()` check
with `args.log.is_file()` so a directory is a clean usage error (exit `2`) — and
(b) wrap `read_text` in a `try/except (OSError, UnicodeDecodeError)` that calls
`parser.error(...)` (exit `2`) with a clear message such as
`"cannot read log <path>: <reason>"`. Add a test per case (see TICKET-055).

Issue: #84
