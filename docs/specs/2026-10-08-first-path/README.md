# The specs the first path was built from

Written on 2026-10-08 by the main session and handed, one each, to the agents of Oleg's
supervisor plugin, which built the pieces in parallel. Kept as the record of what was asked; the
code is the source of truth now. `common.md` is the contract every piece shared.

| Spec | What it built | Built by |
|---|---|---|
| `a-driver.md` | the step contract and the driver (`factory/envelope.py`, `driver.py`, `__main__.py`) | supervisor:implementer (Sonnet) |
| `b-revert.md` | the revert check, its failure sorter plugin, the lint check | supervisor:senior-implementer (Opus) |
| `c-mutants.md` | the mutation check on changed functions, the suite runner | supervisor:implementer (Sonnet) |
| `d-headless.md` | the headless Claude Code runner, Frame, Plan, Review, the linkding target files | supervisor:implementer (Sonnet) |

Not specced, written by the main session: the Implement, Verify and Ship steps, and the two
prompts of Verify (`factory/prompts/write_tests.md`, `test_cases.md`).

Where the code differs from these specs:

- A mutant's line offset counts from the function's `def` line (offset 0), so the spec's
  two-line example gives 2, not 1. The builder stopped on the contradiction and asked.
- `lint.run` takes `app_package=` for the check against mocking the application's own code.
- Run folders are absolute paths under the repository's `.artifacts/runs/`, and an answer file is
  consumed once (review findings, fixed before the first run).
- Worktrees are per ticket, `<worktrees>/<ticket id>/base` and `head`, since 2026-10-10
  (`docs/decisions.md`); `common.md` still shows the earlier shared `wt/base` and `wt/head`.
