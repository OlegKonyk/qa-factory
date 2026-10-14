# s3 · Finish a run after a cap hit in Review's fix round; four smaller defects the same run found

Branch `fix/finish-after-cap`, worktree `~/dev/qa-factory-wt/finishcap`. Written 2026-10-14 from the
gafaelfawr run `.artifacts/runs/gafaelfawr-oidc-client-updates` (read-only; never write there) and
its record `docs/runs/2026-10-14-gafaelfawr-oidc-client-updates/` on the branch
`feat/third-application` of the main checkout (read-only too).

## 1. A model call that ends on its budget is a cap hit, and Review can resume after it

**Measured.** Review requested changes; the fix round (Verify round 4, kind `review_fix`) wrote
tests that passed revert, lint, mutation and suite; then the readable-case writer was started with
`--max-budget-usd 0.70` (the cap minus the spend, `rounds.Ledger.budget_for`), cost 0.7046 USD and
`claude -p` ended it with `is_error` and empty text. `write_cases` (`factory/steps/verify.py`
around line 706) raised `CheckFailed("test case writer ended with an error: ")`, `_final` recorded
`test_cases` as failed and `_fail`ed the step with `resumable: False`, Review reported `review fix
round: test_cases: test case writer ended with an error: `, and a re-run fails at once with
`Verify's checks have not passed on the current tests (status fail); re-run Verify for this ticket`
(`factory/steps/review.py`, `run`). The only way on was a fresh Verify (about 6 USD) that throws the
fix round's tests away.

**Change.**

a. In `factory/headless.py` the result already carries `subtype` (read the module docstring and
   `Result`; a budget-ended call has a subtype that names the budget: read what the docstring
   says, and if it does not say, look at the transcript of the capped call in the run folder,
   `verify/rounds/4/` or the cases transcript named in `verify/test_cases.json`/`report.json`;
   state in the code what was read). Add `Result.budget_exceeded` (a property or field) that is
   true for that subtype.
b. In `verify.py`, both model-call sites that raise `CheckFailed("... ended with an error: ...")`
   (`write_tests` ~452, `write_cases` ~706) and the review's own model call if it has the same
   shape (`factory/steps/review.py`, `_review`): when `result.budget_exceeded`, raise
   `rounds.CapReached` with a message naming the call and the budget it had (read `rounds.py` for
   how CapReached is built and what message the existing cap raise uses; keep the shape). Then
   `_guarded` marks the step `resumable` when every attempt check passed, exactly as it does for
   a cap hit before the call. When the call failed for another reason, the error text must not be
   empty: include `subtype`, then `text`, then `stderr`, whichever is first non-empty.
c. In `review.py` `run`: before the "Verify's checks have not passed" failure, when the Verify
   report has `resumable: true`, continue the fix round: `fix = verify.run(inp)` (which takes the
   `_resume_after_cap` path on the fix round's tests under the caps the ticket gives now); if
   `fix["status"] != "pass"` return it as the fix-round failure the way the `answer` branch does
   (`"review fix round: " + reason`, artifacts carried with the round key); else
   `_review_again(inp, fix, _latest_round(run_dir), ledger, kwargs)`. Read `_latest_round` and the
   `answer` branch first and mirror them.
d. `docs/adopt.md` section 6: replace the bullet "A cap hit inside Review's fix round does not say
   so" with what is now true: the step ends with the cap named (`stopped_at: test_cases`,
   `resumable: true` in `verify/report.json`), and after raising `caps.usd` the same `run` command
   resumes at the readable cases on the fix round's tests and reviews them again; label it built
   2026-10-14 and measured on nothing yet (the session that merges this measures it on gafaelfawr
   and updates the wording). Keep the measured facts of the old bullet (what the run printed) as
   the history in one sentence.

## 2. The writer prompts carry the recipe's pytest arguments

**Measured.** `factory/prompts/write_tests_blind.md:34`, `write_tests.md:48`,
`write_tests_repair.md:36` tell the writer to run `{python} -m pytest -p no:cacheprovider <file>`,
without the recipe's `pytest_args`. In a `src/` layout worktree that command imports the clone's
code (the editable install), and on gafaelfawr the clone held the fix: the blind writer's plain
command gave `5 passed` on the old code; with `-o "pythonpath=src client/src"` the same tests gave
`3 failed, 2 passed`. The writer used the override only because the strategy rule said so. The
blind lane leaks through that command.

**Change.** A placeholder `{pytest_args}` in those three prompts (and in `_PYTEST` in `verify.py`
if the browser command has the same gap), filled with the recipe's `pytest_args` shell-quoted and
space-joined (`shlex.join`), replacing the hard-coded `-p no:cacheprovider`. Find where the prompts
are formatted (grep `api_test_file` in `verify.py`) and add the key. Tests: the rendered prompt
holds `-o 'pythonpath=src client/src'` (or however `shlex.join` quotes it) for a fake recipe with
those args, and plain `-p no:cacheprovider` for isso's. `docs/adopt.md` section 4, the strategy
paragraph "For a `src/` layout, the one-file command must carry the override": rewrite to say the
prompt now carries the recipe's `pytest_args` (built 2026-10-14, not yet measured on a writer
round) and that the strategy rule may still repeat it.

## 3. The developers' tests check matches parametrized tests

**Measured.** `verify/developers_revert.json` on gafaelfawr: the modified developers' test is
`tests/handlers/api_oidc_test.py::test_lifecycle`, pytest reported it as
`test_lifecycle[github-oidc-server]`, the check matched nothing: `status: error`, `ran: 0`, reason
"1 of 4 tests fail on an assertion without the change", `summary.md` counts 0.

**Change.** In `factory/checks/devtests.py` (and `revert.py` if the matching lives there; read
both), a reported node id `file::name[params]` belongs to the judged id `file::name` (strip a
trailing `[...]`). When several parametrizations map to one test, the test's verdict is the
worst of them in this order: `head-fails`, `crash`, `missing-name`, `passes-without-change`,
`proves-behaviour`, and the record keeps each parametrization's own verdict under `params`. Test
with a fake jsonl that has two parametrizations. `docs/adopt.md` section 7, the developers' tests
paragraph: replace the "A parametrized test gets no verdict" sentence with the rule (built
2026-10-14, measured by `python -m factory devtests` on the gafaelfawr run: the session that
merges this runs it and fills the numbers; write "not yet measured" until then).

## 4. The report tells the truth about a failed fix round

**Measured.** `report.md` of the run says "No readable cases were written. Verify ended with:
every check passed; approved by the factory" (`factory/report.py` `_case_lines` reads
`steps/04-verify.json`, which is the passed round 3), while round 4's `test_cases.json` says fail
and 5 cases exist on disk.

**Change.** `_case_lines` reads `verify/test_cases.json` first: when its status is `fail`, print
"The readable cases were not finished: <reason>" and list any case files found under
`verify/testcases/`; otherwise as now. Test with a fake run folder.

## 5. Tests, docs, done

`py-testing` conventions, tests beside the existing ones (`tests/test_verify_loop.py`,
`tests/test_review_step.py` or wherever Review is tested, `tests/test_devtests*.py`,
`tests/test_report.py`, `tests/test_headless.py`). `docs/log.md`: one entry with the four
measured facts and what is built, nothing claimed measured that was not. `just check` green in
the worktree, output pasted. No git commands.
