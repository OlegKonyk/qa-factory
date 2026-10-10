# The first run's records

A copy of the small JSON records from the run folder `.artifacts/runs/linkding-sort-by-modified/`,
taken on 2026-10-10, first while the run was parked at the Verify gate, then again after Oleg approved it and Review and Ship ran the same day. The run folder itself is local
and gitignored; this copy keeps the evidence if it is lost, but a run cannot resume from it.

- `steps/` one record per step: its input, output, timing and metrics.
- `frame/`, `plan/`, `review/` the structured answers of the one-prompt steps. `review/` now holds
  the driver step's review of 2026-10-10; the hand-run of 2026-10-08 is in `../summary.json`.
- `ship/` the commit on `qa/linkding-sort-by-modified` and the suite run with the new tests.
- `steps/04-verify.answer1.json` the approval that was used, moved aside by the driver.
- `implement/` the source diff of upstream commit 0490013 and the changed-file lists.
- `verify/` one report per check (`write_tests`, `lint`, `revert`, `mutation`, `suite`,
  `test_cases`) and `report.json`, which gathers timings and costs.

Left out: the two copies of linkding the revert and mutation checks made (48 MB). Paths inside
the records point at the shared worktrees `wt/base` and `wt/head` used then; they moved to
`wt/linkding-sort-by-modified/` on 2026-10-10.
