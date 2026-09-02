# TICKET-061: `--log` pointing at a directory crashes with a raw traceback (IsADirectoryError) and exit 1
**Status: CLOSED (Cycle 20, PR #23).**

## Title
Passing a directory to `--log` crashes the CLI with a full Python traceback
(`IsADirectoryError`) and exit code 1, instead of a clean one-line message.

## Evidence
`epilogue/cli.py` lines 127-130:

    if not args.log.exists():
        parser.error(f"log path does not exist: {args.log}")

    text = args.log.read_text(encoding="utf-8")

The only pre-read guard is `args.log.exists()`. `Path.exists()` returns `True`
for a directory, so a directory passes the guard and reaches the unguarded
`read_text` at line 130.

Empirical (this audit):

    $ python -m epilogue --project demo --from 1 --to 2 --log /tmp/<dir>
    # exit code: 1
    # stderr ends in:
    #   File "/usr/lib/python3.10/pathlib.py", line 1119, in open
    #     return self._accessor.open(self, mode, buffering, encoding, errors,
    # IsADirectoryError: [Errno 21] Is a directory: '/tmp/<dir>'

## Impact
- A user who passes a directory (a common mistake, e.g. `--log ./logs`) gets a
  multi-line traceback instead of an actionable one-line message.
- The exit code is 1, which the documented contract reserves for "no cycles in
  range" (see TICKET-064). A caller cannot tell "you pointed at a directory"
  from "your range was empty".

## Suggestion
Replace the `exists()` guard with an `is_file()` guard so a directory is
rejected before the read:

    if not args.log.is_file():
        parser.error(f"log path is not a regular file: {args.log}")

This catches both the missing-file and the directory case in one check and
preserves the documented exit-2 "missing log" behavior for the missing case.
(Alternatively, keep `exists()` and add `elif not args.log.is_file():` for the
directory case.)

Issue: #94
