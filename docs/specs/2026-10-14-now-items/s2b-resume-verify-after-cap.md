# s2b · Resume Verify after the spend cap

Worktree: `~/dev/qa-factory-wt/fixes` (branch `fix/mutation-resume-devtests`), after s2a.

## The problem

`factory/steps/verify.py`: `_guarded` turns `rounds.CapReached` into a failed step. On the
bundles ticket of 2026-10-10 every check had passed and the cap was hit while writing the readable
test cases (`write_cases`, the `FINAL_CHECKS`). A re-run of the ticket (the driver archives the
failed record and calls `verify.run` again) starts a fresh writer round: about 4 USD and the
passing tests thrown away. It should resume at the readable cases.

## The fix

1. When `_guarded` catches `CapReached`, the report (`verify/report.json`, written by
   `_write_report`) records where it stopped: `"stopped_at"`: the stage that was about to call a
   model (`"test_cases"`, `"test_cases_repair"`, `"advice"`, `"write"`, `"repair"`, `"guided"`,
   `"review_fix"`), and `"resumable"`: true only when the last attempt passed every check in
   `ATTEMPT_CHECKS` (so only the readable cases or their approval are left). Keep `status: "fail"`
   and the reason text as they are. Find the cleanest way to know the stage: a `ctx["stage"]` set
   before each model call is acceptable.
2. `verify.run(inp)` with no answer: if `verify/report.json` exists with `resumable: true`, resume
   instead of starting a writer round: build the context from the previous report
   (`_context(inp, previous=report)`), restore the tests into the head tree (`_restore`, which also
   sets `ctx["files"]`), load `ctx["checks"]` from the last round's check files
   (`verify/rounds/<n>/<check>.json`, so `_approve` finds `revert`, `suite` and `mutation`), set
   `ctx["attempts"]`, `ctx["repaired"]`, `ctx["guided"]` from the history, then run the
   `FINAL_CHECKS` and `_approve` through `_guarded`, under the current caps. The caps come from
   `rounds.caps_for(ticket, app)` through `_context`, and the driver reads the ticket file afresh
   on every run, so raising `caps.usd` in the ticket file is the documented way to continue; make
   sure `Ledger` takes the passed caps over the file's (`rounds.py`: it does today, check it stays
   so) and that `rounds.json` records the new caps.
3. The record's reason on the resumed pass says it resumed ("resumed at the readable cases after
   the spend cap; tests of round n kept") so the run report shows it; `ctx["history"]` gets an
   entry `{"round": n, "kind": "resume", ...}` or the report's `rounds` list shows it, your call,
   as long as `python -m factory report` renders without error on such a run (check with the
   report's tests).
4. A cap hit anywhere else (during a writer round or a stronger-model call) stays as today: a
   fresh round on re-run. Say so in a comment where the branch is taken.
5. `docs/adopt.md` section 6: one bullet on what a run stopped at its cap does on re-run and how
   to raise the cap.

## Tests and evidence

- `tests/test_verify_loop.py` has fakes for the checks and the writer; add: a run whose checks
  pass and whose cases call raises `CapReached` leaves `resumable: true` and `stopped_at:
  "test_cases"`; a re-run with a raised cap resumes, calls no writer, writes the cases and
  approves, and the reason says it resumed; a cap hit inside the writer round leaves
  `resumable: false` and the re-run starts a writer round as before; `python -m factory report`
  renders the resumed run.
- Paste the last lines of `ruff check`, `ruff format --check` and `pytest`.
- Do not run anything against linkding or isso and make no model call.

## Report

Files changed; commands and output; deviations with reasons; what was left alone. Do not commit.
