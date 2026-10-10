# The sort ticket, written blind (2026-10-10)

`uv run python -m factory run targets/linkding/tickets/sort-by-modified-blind.json`: all six steps
passed in one round, 902 s wall, 5.48 USD. The numbers are in `summary.md` (from
`python -m factory summary`); the comparison with the run of 2026-10-08 is in
`../2026-10-10-track-1-comparison.md` and `docs/exploration.md`.

- `tests/`, `testcases/`: the four tests and their readable cases, as shipped on
  `qa/linkding-sort-by-modified-blind` (commit `737c758` in the ticket's head worktree).
- `records/`: the run folder's small records. `records/verify/rounds/1/writer_tool_calls.json`
  lists the blind writer's tool calls (name and input); the raw session transcript stays local,
  because it also holds this machine's hook output.

Left out: the copies of linkding the revert and mutation checks made.
