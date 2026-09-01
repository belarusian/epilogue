# epilogue

CLI that reads a project cycle log (Rules/Build Order/## Cycle blocks) and renders release-note-style changelogs for a cycle range: --project, --from, --to; merges vs no-ops vs NOT MERGED distinguished truthfully from the log; stdlib only; full pytest suite; CI green on push.

Built cycle-by-cycle; see the ground-truth log: `../ai/cycle-001-epilogue-gate.md`
