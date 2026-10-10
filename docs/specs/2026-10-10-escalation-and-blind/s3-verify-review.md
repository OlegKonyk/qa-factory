# S3: the Verify and Review loop (repair round, stronger model, caps, blind writer)

Files: `factory/steps/verify.py`, `factory/steps/review.py`, `factory/prompts/write_tests_repair.md`
(new), `factory/prompts/write_tests_blind.md` (new), `tests/test_verify_loop.py` (new),
`tests/test_verify_step.py`, `tests/test_prompt_steps.py` (the review tests only).
Built after S1 and S2; use their interfaces exactly: `factory.rounds` (Ledger, caps_for,
CapReached), `factory.escalate` (decide, BUDGET_USD), `factory.blind` (is_blind, public_ticket,
hidden_paths, settings, audit), `headless.call(..., transcript_path=...)`,
`headless.one_prompt(..., allow_blind=False)`.

Read first: this whole file, `factory/steps/verify.py`, `factory/steps/review.py`,
`factory/steps/ship.py` (`restore_tests`), `factory/checks/revert.py` (report shape),
`factory/checks/mutants.py` (report shape: `mutants` holds `{key: {status, line, changed_line}}`),
`factory/prompts/write_tests.md`, `tests/test_verify_step.py`, `tests/test_implement.py` (a tmp git
repository fixture you can copy).

## What Verify does after this change

```
round 1   write   the writer (fresh session) writes the tests; then lint, revert, mutation, suite
          any failure ->
round 2   repair  only if the failure is repairable (lint, revert, mutation, see below), no repair
                  happened yet in this Verify run, and the ticket has a writer round left: the writer
                  gets the findings in a fresh session, edits its files in the head tree; checks
                  again from lint
          a failure that is not repairable, or a failure after the repair ->
advice    the stronger model (escalate.decide) reads the reports and decides:
          retry            -> round 3 guided: a fresh writer session with the findings and its
                              guidance; checks again from lint. Allowed once per Verify run and
                              only while the ticket has a writer round left.
          change_is_wrong  -> the step fails: "the stronger model judged the tests right and the
                              change wrong: <diagnosis>"
          environment      -> the step fails: "environment problem, diagnosed by the stronger
                              model: <diagnosis>"
          cannot_decide    -> the step stops for a person (needs_person, gate kind "escalation")
          A failure after the guided round goes to the stronger model again (retry no longer
          allowed). With no stronger-model call left on the ticket, the step fails with the last
          failure and says the cap was reached.
then      the test cases (as today; a failure there fails the step, it is not escalated), the
          automatic approval (as today), report.json
```

A `rounds.CapReached` raised anywhere (every model call takes its budget from
`ledger.budget_for(...)`) fails the step with the exception's message.

## verify.py, in detail

### Structure

- `RUNNER = subprocess.run`: passed as `runner=RUNNER` to every `headless.call` and to
  `escalate.decide`, so tests monkeypatch `verify.RUNNER` (never `subprocess.run`, which git uses).
- `class CheckFailed(Exception)`: add `repairable: bool = False` (constructor keyword).
- `ATTEMPT_CHECKS = [("write_tests", write_tests), ("lint", run_lint), ("revert", run_revert),
  ("mutation", run_mutation), ("suite", run_suite)]` and `FINAL_CHECKS = [("test_cases",
  write_cases)]`, replacing `CHECKS`. Every check is still `fn(ctx)`. `write_tests` reads its mode
  from `ctx["mode"]` ("fresh" or "repair"), and `ctx["findings"]`, `ctx["guidance"]`.
- `_context(inp) -> dict`: today's ctx plus `ledger` (`rounds.Ledger(run_dir,
  rounds.caps_for(ticket, app))`), `blind` (`blind.is_blind(ticket)`), `rounds: []`, `history: []`,
  `advice: []` (paths), `repaired: False`, `guided: False`, `round_no` (1 + the highest n of the
  existing `verify/rounds/<n>` folders, so a re-run of a failed Verify continues the numbering and
  keeps the earlier evidence), `mode`, `findings`, `guidance`.
- `_attempt(ctx, kind, findings="", guidance="") -> dict | None`: one round. `kind` is "write",
  "repair", "guided" or "review_fix"; mode is "fresh" for write, "repair" otherwise. Creates
  `verify/rounds/<n>/`, runs ATTEMPT_CHECKS in order until one raises CheckFailed, dumps each
  check's result (or `{"status": "fail", "reason": ..., "repairable": ...}`) to both
  `verify/rounds/<n>/<check>.json` and `verify/<check>.json` (the latest round at the top level,
  where later steps and today's tests read it), appends `{"round": n, "kind": kind, "checks":
  {name: {"status", "s"}}, "failure": <failure or None>}` to `ctx["rounds"]` and `{"round", "kind",
  "failure": <reason or None>}` to `ctx["history"]`, writes report.json (`_write_report`), and
  returns the failure `{"check", "reason", "repairable", "report": <the round's check JSON path>}`
  or None.
- `_settle(ctx, failure) -> dict | None`: the loop above. Returns None when an attempt passed,
  else the step's terminal output dict (fail or needs_person). Uses `escalate.decide(ticket=<the
  full ticket>, strategy=<strategy text>, diff=<the change diff>, failure, history=ctx["history"],
  test_files=ctx["files"], head_tree, run_dir, allow_retry, budget_usd=ledger.budget_for(
  escalate.BUDGET_USD), out_path=verify/escalation-<k>.json, runner=RUNNER)` where k = the
  ticket's advice count + 1; then `ledger.add("verify", "advice", cost, model, duration_s,
  outcome=decision)`; the path goes into `ctx["advice"]` and the step's artifacts as
  `escalation` (the latest).
- `_findings(ctx, failure) -> str`: plain text for the writer from the failing round's check JSON,
  at most 8000 characters:
  - lint: one line per finding, `file:line rule message`;
  - revert: one line per test whose verdict is not `proves-behaviour` or `passes-without-change`:
    `nodeid: verdict (at head: <at_head>, without the change: <reverted>): <message, 300 chars>`;
    when no test proves behaviour, say so;
  - mutation: the reason, then `on the changed lines: checked N, killed K, survived S`, then up to
    10 surviving mutants on changed lines as `line L: <that source line from the head tree>`;
  - suite: each run's summary and the last 20 lines of each failing run;
  - write_tests and anything else: the reason.
- `run(inp)`: answer handling first (below); then `ctx = _context(inp)`; `failure = _attempt(ctx,
  "write")`; `terminal = _settle(ctx, failure)`; return it if set; then FINAL_CHECKS; then the
  approval exactly as today. All wrapped so CapReached becomes a fail output. report.json and the
  output's metrics as today, plus: `report["rounds"]`, `report["advice"]`, `report["ledger"]`
  (`ledger.summary()`), `report["blind"]`, `report["blind_audit"]` (from round 1's manifest, if
  any), `metrics["rounds"]` (attempts in this run), `metrics["ticket_spent_usd"]`.
- Costs: `ctx["costs"]` keeps one entry per model call with a unique key: `write_tests` (round 1,
  the name today's records use), `<kind>.r<n>` for later writer rounds, `advice.<k>`,
  `test_cases`, `test_cases_repair`; `metrics["cost_usd"]` stays their sum. Each call also goes
  into the ledger: kinds `write`, `repair`, `guided`, `review_fix`, `advice`, `cases`,
  `cases_repair`.

### Which failures are repairable

- lint: always.
- revert: when the report has test results (offenders, or no test proves behaviour); not when
  pytest ended without a result or timed out (the report's `tests` is empty).
- mutation: "checked no mutant" and "kill no mutant on the changed lines"; not "mutmut did not run".
- write_tests, suite: never (they go to the stronger model directly).

### write_tests

- **fresh, sequential** (`ctx["mode"] == "fresh"` and not blind): exactly as today.
- **fresh, blind**: the writer runs in the base worktree.
  - Clean the test folders in both trees first (`git clean -fdq -- <dirs>` and `git checkout --
    <dirs>`, as today's head-only clean does).
  - Prompt `write_tests_blind.md` (below) with `ticket_json` = `blind.public_ticket(ticket)`;
    no diff, no developers' tests.
  - `headless.call(..., cwd=base_tree, settings=blind.settings(hidden, base=WRITER_SETTINGS),
    transcript_path=verify/rounds/<n>/writer.jsonl, runner=RUNNER)` where
    `hidden = blind.hidden_paths(repo, FACTORY_ROOT)`.
  - Read `git status --porcelain --untracked-files=all` in the base tree: source touched or
    tracked tests modified there are reverted and fail the step, as today in the head tree. New
    files under the test folders are copied to the same relative paths in the head tree, then the
    base tree's test folders are cleaned again (the base tree is left as it was).
  - The rest as today (manifest, copies, checks of what was written), on the head tree.
  - `manifest["blind_audit"] = blind.audit(transcript, hidden)`. A flagged call does not fail the
    step; it is recorded, and `report["blind_audit"]` carries it.
- **repair** (any mode): the writer runs in the head tree on the files already there.
  - No clean of the test folders.
  - Prompt `write_tests_repair.md` (below): `ticket_json` (public ticket when blind, full
    otherwise), `strategy`, `change_section`, `files` (the current manifest files, one per line),
    `findings`, `guidance` (or "(none)"), dirs, file names, `python`, `browser_glob`.
    `change_section` is, sequential: "## The change (source files only)\n\n```diff\n<diff>\n```";
    blind: "## The change\n\nThe change is in this tree. Its diff is not given: work from the
    findings, the ticket and the code." (After the join a blind repair may read the code, but its
    prompt carries no diff and no developers' tests: decided 2026-10-10.)
  - The same status handling as fresh-sequential on the head tree (source touched or tracked tests
    modified: revert and fail; new files = the untracked files under the test folders).
- In every mode: clear `verify/tests/` before copying the current files there, and also copy them
  to `verify/rounds/<n>/tests/`; write the manifest to `verify/tests_manifest.json` and
  `verify/rounds/<n>/tests_manifest.json`; the writer's budget is
  `ctx["ledger"].budget_for(WRITER_BUDGET_USD)`.

### run_mutation

Add a third set, `developers` (the developers' API test files alone), run once per Verify run
when there are any, and reused in later rounds (keep its result in `ctx`). The gate rules do not
change and read only the `generated` set.

### Answers to a gate

`_answer` today handles the approval gate. Keep it, and add the escalation gate: report.json
records `gate_kind` ("approval" or "escalation") and, for escalation, the last failure. On re-run
with an answer to an escalation gate:
- `{"decision": "retry", "guidance": "...", "by": "..."}`: run one guided attempt with that
  guidance (restore the tests into the head tree from `verify/tests` with `ship.restore_tests` if
  missing), with `repaired` and `guided` already True, then `_settle`, the cases and the approval
  as in `run`. Its ledger kind is `guided`.
- any other decision: the step fails with `decided by <by>: <decision>: <guidance or note>`.

### write_tests_blind.md

Based on `write_tests.md`, with these differences, in plain English:
- The change does not exist yet: you are in the repository at the commit before it. Write the
  acceptance tests for the ticket now, from the ticket and the code as it is, so they can join the
  change when it lands.
- No "The change" section and no "developers' own tests" section.
- Use only the public surface the ticket names: query strings, API JSON fields, routes, visible
  labels and controls exactly as the ticket states them. Never import or reference code names the
  change will add; use the test helpers only with the arguments they accept at this commit.
- The feature is missing here, so the tests must fail here, and for the right reason: run the API
  file and check that every test of new behaviour fails with an AssertionError, never with an
  ImportError, NameError, AttributeError, KeyError, TypeError or a server error. Read values
  defensively (assertIn before indexing) so that a missing field fails as an assertion. A test of
  behaviour that already exists (a fallback) may pass here.
- The browser test cannot run here (the assets are not built): check that it collects with
  `{python} -m pytest -p no:cacheprovider --collect-only -q -o "python_files={browser_glob}"
  {browser_tests_dir}/{browser_test_file}`. First assert the new control is present, then use it
  and assert the visible result.
- Do not use git and do not look for the change anywhere else on this machine.
- Same placeholders as `write_tests.md` minus `diff` and `dev_tests_diff`.

### write_tests_repair.md

Plain English: you wrote the test files listed for this ticket; the factory's checks found the
problems listed; fix them by editing those files (you may add a test file in the same folders when
the strategy puts a test elsewhere); never modify application code or existing tests; you are in
the repository at the commit that contains the change. Then the ticket, the strategy,
`{change_section}`, `{files}`, `{findings}`, `{guidance}`. How to work: a test that fails without
the change for a wrong reason (a crash or a missing name) must fail on an assertion instead; a test
that fails with the change expects something the change does not do: re-read the ticket and the
code and fix the test, unless the ticket clearly says otherwise; run the files and make them pass
(same commands as write_tests.md); ruff check and format; same rules (public surface, no sleeps, no
mocking of the application's code, no private names, every test asserts). Respond only through the
structured output: the files and short notes.

## review.py

- `one_prompt(..., allow_blind=False)`; its budget is `ledger.budget_for(1.00)`; its cost goes into
  the ledger as kind `review` (step "review"). CapReached fails the step.
- On `request_changes`, when the ticket has used no `review_fix` round yet and has a writer round
  left:
  1. Move `review/review.json` to `review/review.round1.json`.
  2. `fix = verify.repair_from_review(inp, <the review's structured data>)`.
  3. If fix is not a pass, return it (its reason prefixed "review fix round: ", its artifacts plus
     `review_round1`).
  4. Run the review prompt once more with the input's artifacts updated by fix's artifacts; its
     output's artifacts also carry fix's artifacts (the driver merges them, so Ship gets the new
     tests) and `review_round1`.
  5. Still `request_changes`: fail, "review still requests changes after the fix round: <high
     findings>".
- Otherwise (no round left, or a fix round already used): fail as today.

### verify.repair_from_review(inp, review) -> dict

Builds the context from Review's input (its artifacts include Verify's), restores the tests into
the head tree from `artifacts["tests_dir"]` (`ship.restore_tests`), sets `ctx["files"]` from the
manifest, then `_attempt(ctx, "review_fix", findings=<one line per finding: file:line severity
summary, then the failure scenario>)`, `_settle`, the test cases, the approval (rule "every check
passed after the review's fix round"; a `"gate": "person"` ticket gets needs_person as in `run`),
report.json; returns the output dict with Verify's artifacts. When the ticket has no writer round
left, it returns a fail without calling anything.

## Tests

`tests/test_verify_loop.py` (new), in the style of `tests/test_verify_step.py`:

1. lint fails in round 1 and passes in round 2: write_tests ran twice, the second with mode
   "repair" and the lint finding in `ctx["findings"]`; `verify/rounds/1/lint.json` and
   `verify/rounds/2/lint.json` both exist; report.json lists two rounds; the ledger holds `write`
   and `repair` entries (give the fake write_tests a cost via the ledger or ctx["costs"]).
2. Each stronger-model decision, with `escalate.decide` monkeypatched to a canned record:
   retry -> a guided round runs with the guidance and the step passes; change_is_wrong and
   environment -> fail with the diagnosis in the reason and `escalation` in the artifacts;
   cannot_decide -> needs_person, gate context names the failure, report.json has gate_kind
   "escalation".
3. A suite failure goes to the stronger model without a repair round.
4. Caps: writer_rounds 1 -> after the repair, decide gets allow_retry False; advice 0 -> fail
   naming the cap; usd below MIN_CALL_USD -> fail "spend cap reached".
5. A second Verify run in the same run folder numbers its rounds after the first's.
6. The answer to an escalation gate: retry with guidance runs a guided round and passes; another
   decision fails with the person's note.
7. write_tests in a tmp git repository pair (base and head worktrees of one repo, as in
   tests/test_implement.py) with `verify.RUNNER` faked to write a test file into its cwd and
   return canned JSON: fresh-blind runs in the base tree with `--settings` deny rules and
   `stream-json` in argv, the prompt has no diff, the file ends up in the head tree and not in the
   base tree; repair runs in the head tree and does not clean the folders.
8. The developers' mutation set runs once across two rounds (monkeypatch `mutants.run`).
9. Review (tests/test_prompt_steps.py): request_changes -> repair_from_review called (monkeypatched)
   -> re-review approves -> pass with fix's artifacts and review_round1; still request_changes ->
   fail; no writer round left -> fail without a fix; one_prompt gets allow_blind False; the
   review's cost is in the ledger.
10. repair_from_review with fake checks: restores the tests, runs a review_fix round, rewrites the
    cases and the approval.

Update `tests/test_verify_step.py` for the CHECKS split; keep every behaviour it tests today.
