# TICKET-063: `--log` that is unreadable (permission denied) crashes with a raw traceback (PermissionError) and exit 1
**Status: CLOSED (Cycle 20, PR #23).**

## Title
A `--log` file the user cannot read (permission denied, or any OS-level read
failure) crashes the CLI with a full Python traceback (`PermissionError`) and
exit code 1, instead of a clean message.

## Evidence
`epilogue/cli.py` line 130:

    text = args.log.read_text(encoding="utf-8")

The read is unguarded. `Path.read_text` raises `PermissionError` (a subclass of
`OSError`) when the file cannot be opened for reading.

Empirical (this audit): a log file with mode `000`:

    $ chmod 000 /tmp/noperm.md
    $ python -m epilogue --project demo --from 1 --to 2 --log /tmp/noperm.md
    # exit code: 1
    # stderr ends in:
    #   File "/usr/lib/python3.10/pathlib.py", line 1119, in open
    #     return self._accessor.open(self, mode, buffering, encoding, errors,
    # PermissionError: [Errno 13] Permission denied: '/tmp/noperm.md'

## Impact
- A log the user has no read permission on (or that is otherwise unreadable at
  the OS level — any `OSError`/`IOError`) crashes with a traceback.
- The exit code is 1, colliding with "no cycles in range" (see TICKET-064).

## Suggestion
Catch `OSError` (the base of `PermissionError`) around the read and print a
clean one-line message to stderr, then return a distinct exit code (see
TICKET-064):

    try:
        text = args.log.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"epilogue: could not read log: {args.log} ({exc})", file=sys.stderr)
        return 3

Note `UnicodeDecodeError` is NOT an `OSError` (it is a `ValueError`), so the
encoding case (TICKET-062) needs its own handler or a combined
`except (OSError, UnicodeDecodeError)`.

Issue: #96
