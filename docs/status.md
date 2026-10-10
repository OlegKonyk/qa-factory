# Status

Read this first. Update it last, in the same pull request as the work.

## Waiting on Oleg

1. Will tickets at work state the public contract (field names, values, labels, routes) before
   coding starts? Track 1's blind tests met the change with no mismatch, but both tickets were
   written from finished commits. If not, Plan has to fix the contract first.
2. Let the bundles ticket spend about 1.5 USD more (estimate) to finish (readable cases, Review,
   Ship)? It stopped at its 8 USD cap after its checks passed. Recommended: yes, as the first run
   track 2 watches on Restate (raise `"caps"` in `targets/linkding/tickets/bundle-filters-blind.json`
   and re-run; Verify resumes with the cases).

## Where things stand, 2026-10-10

- **The first ticket is finished.** On Oleg's approval, Review approved with three low findings
  (51 s, 0.47 USD) and Ship committed the tests and cases as `d1c4de7` on
  `qa/linkding-sort-by-modified` in `~/Library/Caches/qa-factory/linkding/wt/linkding-sort-by-modified/head`;
  linkding's suite with them: 1294 passed, and 2 browser tests passed (32 s). All numbers measured.
- **Track 1 is done** (`docs/exploration.md`, "Track 1 results"). Tests written blind, from the
  ticket and the code before the change, met the developers' real change on two linkding tickets
  with no contract mismatch: 17 of 17 pass with the change, 15 fail without it on an assertion, 2
  are regression guards, every mutant on the changed lines is killed. On the sort ticket they match
  the tests written after the change number for number (27 of 108 and 10 of 10 mutants). Model
  spend 13.96 USD against about 10 estimated, 4.27 of it the escalation running live. All measured.
- **The factory asks stronger models before people** (pull requests 13 and 14): a repair round,
  then Fable 5.1's decision; a recheck answer after a fix; caps per ticket. The bundles run used
  all of it for real and found four defects in the factory's own checks, now fixed.
- **Next: track 2**, the factory on Restate (`docs/next-session.md`). Nothing at work runs a
  factory yet, so it is a real trial.
- What was tried, including what failed, is in `docs/log.md`. The architecture, drawn for review,
  is https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa; its tables are in `docs/architecture.md`.

## Done

- **Track 1** (2026-10-10, `docs/runs/2026-10-10-*`): the sort ticket blind, shipped as `737c758`
  on `qa/linkding-sort-by-modified-blind` (902 s, 5.48 USD); the bundles ticket blind, written from
  linkding 573b6f5 (`targets/linkding/tickets/bundle-filters*.json`), checks passed after a
  recheck, stopped at its cap before the readable cases (8.47 USD). Pull request 14 fixed what the
  bundles run found: the revert check now puts the test helpers back to their old version; the
  writer is blamed only for its own changes; Fable needs 1.50 USD left to start; the writer may not
  create worktrees or run npm; a `recheck` answer judges an earlier round's tests again. The run
  summary counts the ticket's spend from `rounds.json`. 188 factory tests.
- **Stronger models before people, and blind mode** (2026-10-10, `docs/log.md`): one repair round
  for the test writer, then `claude-fable-5-1` decides retry, the change is wrong, an environment
  problem, or cannot decide (the only one that asks a person); one fix round when Review requests
  changes; caps per ticket in `<run folder>/rounds.json` (3 writer rounds, 2 stronger-model calls,
  15 USD by default). `"qa_mode": "blind"` runs Frame, Plan and the first writer in the base
  worktree with every other copy of the code hidden. `python -m factory summary` prints a run's
  numbers. 172 factory tests.
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

- `.artifacts/runs/<ticket id>/`, the run folders: what a resume needs. Three exist:
  `linkding-sort-by-modified` and `linkding-sort-by-modified-blind` (finished),
  `linkding-bundle-filters-blind` (stopped at its cap, resumable). Gitignored, so
  `git clean -fdx` deletes them. If one is lost, its run starts over (about 5 USD and 13 minutes
  for the first ticket, estimated from its run). The evidence is copied to `docs/runs/`.
- `~/Library/Caches/qa-factory/linkding/`: the clone, its environment and one worktree pair per
  ticket. `targets/linkding/fetch.py --ticket <ticket> [--prepare-e2e]` rebuilds them; Review and
  Ship put the generated tests back from the run folder.

## Next

0. From `docs/next-session.md`: exploration track 2 (the factory on Restate, and a run report),
   then track 3 (the deployed environment, linkding's Docker image on this laptop).

1. From track 1: the sequential run of the bundles ticket was not done (cap); the writer's
   placement of form tests in the API file follows the strategy loosely; a Fable call that runs
   out of budget still counts as "cannot decide" (it now cannot start below 1.50 USD, but can still
   overshoot); the raw writer transcript stays local because it holds this machine's hook output.
2. From the first run: the plan step proposes file names the writer must ignore (fixed by
   prompt, worth a schema); the review step's low findings (random titles in the API fixture)
   could feed back into the writer as a second round; Frame and Plan run before the change exists
   and read the code instead of a diff, which is right for a real ticket but confused the prompt.
3. After the loop runs twice: the agent-written Implement step, the Learn step, flaky quarantine
   and test selection, isso as the second application, and whether Temporal goes under the driver.
