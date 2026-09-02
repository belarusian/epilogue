# TICKET-062: `--log` with invalid UTF-8 bytes crashes with a raw traceback (UnicodeDecodeError) and exit 1
**Status: CLOSED (Cycle 20, PR #23).**

## Title
A `--log` file that is not valid UTF-8 crashes the CLI with a full Python
traceback (`UnicodeDecodeError`) and exit code 1, instead of a clean message.

## Evidence
`epilogue/cli.py` line 130:

    text = args.log.read_text(encoding="utf-8")

The read is unguarded. `Path.read_text(encoding="utf-8")` raises
`UnicodeDecodeError` (a `ValueError`, NOT an `OSError`) when the bytes are not
valid UTF-8.

Empirical (this audit): a log file containing the byte `0xff`:

    $ python -m epilogue --project demo --from 1 --to 2 --log /tmp/bad.md
    # exit code: 1
    # stderr ends in:
    #   File "/usr/lib/python3.10/codecs.py", line 322, in decode
    #     (result, consumed) = self._buffer_decode(data, self.errors, final)
    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 13: invalid start byte

## Impact
- A log saved as Latin-1, or a corrupted log, crashes the CLI with a traceback.
- The exit code is 1, colliding with "no cycles in range" (see TICKET-064).

## Suggestion
Wrap the read in a handler for `UnicodeDecodeError` and print a clean one-line
message to stderr, then return a distinct exit code (see TICKET-064):

    try:
        text = args.log.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(f"epilogue: log is not valid UTF-8: {args.log} ({exc})", file=sys.stderr)
        return 3

Note `UnicodeDecodeError` is a `ValueError`, not an `OSError`, so it needs its
own handler (or a combined `except (OSError, UnicodeDecodeError)` — see
TICKET-063).

Issue: #95
