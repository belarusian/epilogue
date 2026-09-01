# TICKET-069

Status: CLOSED
Priority: P2
Type: README drift (documentation vs code)
Module: README.md ("Status filter" section)

## Symptom
The "Status filter" example block in README.md shows the CLI stdout for
`--status not_merged` ending with TWO trailing blank lines after the last
entry, but the actual CLI emits exactly ONE trailing newline (no trailing
blank lines). The block therefore does not reproduce the documented output
byte-for-byte.

## Evidence
- README.md lines 219-227 (the "Status filter" ```text block): the last
  content line `- Abandoned: the old approach` is followed by two blank
  lines before the closing fence.
- Actual CLI output (verified by running the pipeline on the documented
  sample log):
  `python3 -m epilogue --project demo --from 1 --to 2 --log log.md --status not_merged`
  prints, byte-for-byte:
  `# demo\n## Cycle 2: Build\n\n### Not Merged\n- Abandoned: the old approach\n`
  (exactly one trailing newline; no trailing blank lines).
- The main "Example" block (README.md lines 92-109) already follows the
  correct convention: its last content line `- Abandoned: the old approach`
  is immediately followed by the closing fence (one trailing newline). The
  "Status filter" block is the outlier.
- Root cause: the block predates TICKET-054, which normalized BOTH the text
  and json CLI outputs to end with exactly one trailing newline
  (`cli.py` main(): `sys.stdout.write(out.rstrip("\n") + "\n")`). The
  "Status filter" example was not updated to match.

## Proposed minimal additive fix
Remove the two trailing blank lines inside the "Status filter" ```text block
so its last content line is immediately followed by the closing fence,
matching the actual CLI output and the convention used by the main "Example"
block. No code change; README-only.

## Verification
After the fix, the block's content (between the fences) must equal the actual
CLI stdout for the documented invocation, byte-for-byte (one trailing
newline, no trailing blank lines). Re-run the pipeline and diff.
