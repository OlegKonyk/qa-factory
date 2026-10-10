# Status

Read this first. Update it last, in the same pull request as the work.

## Waiting on Oleg

Nothing. (Open decisions go here first, as a short numbered list he can answer in place.)

## Where things stand, 2026-10-10

- **The first ticket is finished.** On Oleg's approval, Review approved with three low findings
  (51 s, 0.47 USD) and Ship committed the tests and cases as `d1c4de7` on
  `qa/linkding-sort-by-modified` in `~/Library/Caches/qa-factory/linkding/wt/linkding-sort-by-modified/head`;
  linkding's suite with them: 1294 passed, and 2 browser tests passed (32 s). All numbers measured.
- **The factory no longer stops to ask when its checks pass** (`docs/decisions.md`). Verify
  approves on its own and records `approval.json`; a ticket may set `"gate": "person"`. Next: a
  fix round and a stronger model's advice before any person, then exploration track 1
  (`docs/next-session.md`).
- **The exploration plan is approved** (`docs/exploration.md`). Nothing at work runs a factory
  yet, so track 2 is a real trial of running this one on Restate.
- What was tried, including what failed, is in `docs/log.md`. The architecture, drawn for review,
  is https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa; its tables are in `docs/architecture.md`.

## Done

- The repository, the planning session and the decisions (previous entry; `docs/decisions.md`).
- **The factory, first path** (`factory/`, pull request 6, 2026-10-08):
  - `python -m factory run <ticket.json>`: the driver over frame, plan, implement, verify, review,
    ship; one JSON record per step in `.artifacts/runs/<ticket id>/steps/`; a step that needs a
    person writes `question.md` and exits 2; a re-run skips passed steps, re-runs failed ones, and
    consumes `answer.json` once. `--until <step>` stops after a step.
  - Frame, Plan and Review are one-prompt headless Claude Code calls with a JSON schema
    (`factory/headless.py`, `factory/prompts/`). Implement is the developers' real commit: it
    records the source diff and the changed files. Ship commits the approved tests and cases on a
    `qa/<ticket id>` branch in the application's worktree and runs its suite.
  - Verify (`factory/steps/verify.py`): a headless Claude Code session (Opus) writes the API and
    browser tests into the application's own test folders by the per-application strategy rule;
    then ruff plus a no-assertion check; the revert check with its failure sorter
    (`factory/checks/revert.py`, pytest plugin `failsort_plugin.py`); mutmut 3.8.0 on the changed
    functions, with the generated tests alone and with the developers' tests added
    (`factory/checks/mutants.py`); the application's full suite; then one readable test case per
    test in the signoff skeleton, linted by a copy of the signoff linter (`factory/checks/cases.py`).
  - linkding as the first application: `targets/linkding/fetch.py` (clone, env, worktrees, e2e
    preparation), `app.json` (the run recipe), `strategy.md` (the rule the test writer reads), and
    the first ticket, written from upstream pull request #1363.
  - 99 factory tests (`uv run pytest`), `just check` green.
- **One worktree pair per ticket** (pull request 7, 2026-10-10), so a run parked at a gate keeps
  its trees while other tickets run; Review and Ship restore the generated tests from the run
  folder if a worktree lost them. 100 factory tests.
- **The record** (2026-10-10): `docs/log.md`, the build specs in `docs/specs/2026-10-08-first-path/`,
  the first run's full records in `docs/runs/2026-10-08-linkding-sort-by-modified/records/`.
- **The first run** (`docs/runs/2026-10-08-linkding-sort-by-modified/`), all numbers measured:
  - Frame 13 s, 0.03 USD; Plan 14 s, 0.07 USD (both Sonnet). Implement 0.06 s.
  - Verify 800 s, 4.90 USD: the test writer 414 s and 3.62 USD (Opus, 39 turns) wrote 4 API tests
    and 2 browser tests; lint clean; revert check 18 s: 5 of 6 tests fail on the old code for a
    behavioural reason and 1 (the unknown-sort fallback) passes on both, as a regression guard;
    mutmut on `_base_bookmarks_query`: 108 mutants checked, the generated API tests kill 27 (25 %)
    over the whole function and 10 of 10 on the changed lines; with the developers' tests 98 of
    108 (91 %); runs 21 s and 138 s; linkding's suite 1294 passed in 24 s and 83 browser tests
    passed, 1 skipped, in 68 s; the test cases 116 s and 1.28 USD (Opus), 6 cases, lint clean.
  - Review, run by hand on the same artifacts (not yet as a driver step, since the gate is still
    open): approve, two low findings, 53 s, 0.58 USD (Opus).
  - Total model spend of the recorded run: 5.58 USD. Wall time of the run through Verify: 13.5 min.
  - Review and Ship ran as steps on 2026-10-10 after the approval (top of this file).

## What lives only on this machine

- `.artifacts/runs/<ticket id>/`, the run folders: what a resume needs. Gitignored, so
  `git clean -fdx` deletes them. If one is lost, its run starts over (about 5 USD and 13 minutes
  for the first ticket, estimated from its run). The evidence is copied to `docs/runs/`.
- `~/Library/Caches/qa-factory/linkding/`: the clone, its environment and one worktree pair per
  ticket. `targets/linkding/fetch.py --ticket <ticket> [--prepare-e2e]` rebuilds them; Review and
  Ship put the generated tests back from the run folder.

## Next

0. From `docs/next-session.md`: the fix round and the stronger model's advice in Verify, then
   exploration track 1 (the feature loop measured); then track 2 (Restate and a run report), then
   track 3 (the deployed environment, linkding's Docker image on this laptop).

1. Run a second ticket end to end: the "Filter bundles by reading or sharing state" commit (573b6f5) is
   the natural second, since it touches a model, a migration, the API and a form.
2. From what the run showed: the plan step proposes file names the writer must ignore (fixed by
   prompt, worth a schema); the review step's low findings (random titles in the API fixture)
   could feed back into the writer as a second round; Frame and Plan run before the change exists
   and read the code instead of a diff, which is right for a real ticket but confused the prompt.
3. After the loop runs twice: the agent-written Implement step, the Learn step, flaky quarantine
   and test selection, isso as the second application, and whether Temporal goes under the driver.
