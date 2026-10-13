# Status

Read this first. Update it last, in the same pull request as the work.

## Waiting on Oleg

1. Delete the three stale remote branches (the squash-merged heads of pull requests 16, 17, 18):
   `git push origin --delete claude/restate-driver-k4pqfg docs/inputs-2026-10-12 docs/track2-real-run`.
   The session's permission rules refused it.
2. Will tickets at work state the public contract (field names, values, labels, routes) before
   coding starts? Both linkding blind tickets and the isso ticket had it written from finished
   commits. If not, Plan has to fix the contract first.
3. Make Restate the default engine now, or keep it behind `--engine restate`? Recommended: keep it
   behind the flag; the plain driver is what the adoption guide uses.
4. Does the Console show the factory's spend (about 5.44 USD on 2026-10-12 and 5.4 USD on
   2026-10-13) against the Max plan's API credits?

## Where things stand, 2026-10-13

- **Ready for a real project.** `docs/adopt.md` is the procedure an agent follows on a fresh
  machine; it was tested by an agent that read nothing else and onboarded isso, and its 23
  findings are folded in. Section 1 is the table of what is ready, measured, and not built.
- **Second application shipped.** isso (werkzeug, API only, tests inside the source package):
  the no-cache ticket, blind, shipped as `59a58be` on `qa/isso-no-cache-comment-views`; 6 tests,
  3 prove the change on the old code, 3 regression guards, 0 missing names; 6 readable cases;
  suite 128 passed; 5.69 USD recorded (`docs/runs/2026-10-13-isso-no-cache-comment-views/`).
  Mutation could not run: mutmut 3.8.0 makes no mutant for the three changed functions
  (decorated), and the factory skips `__init__.py`, where the new function lives. The factory
  now records that as "not applicable" instead of sending the writer into a repair round that
  cannot pass (which the first attempt did, 2.2 USD and a kill).
- **The trust answer** for his meetings: `docs/trust.md` and
  https://claude.ai/artifact/JEQNo6pu9zVp6xbAR98HEt.
- **Factory changes:** browser tests optional in a recipe; `test_helpers` recipe field; mutation
  "no mutants" is a skip, not a failure. 227 factory tests, `just check` green.
- **Not built, said plainly:** the deployed-environment run (track 3), anything for mocks, mutation
  of code in `__init__.py`, the revert check on the developers' own tests.
- **Next:** `docs/next-session.md` has two kickoffs: A, onboard another application (his
  microservice on his side, or a public one); B, track 3.

## Where things stand, 2026-10-12

- **Track 2 is done.** The factory runs as a Restate workflow behind `--engine restate`. It was
  built in a cloud session and run for real on the laptop.
  - **The real run:** the bundles ticket, written blind a second time, went through all six steps
    on Restate in 19 min 23 s for 5.44 USD and shipped as `bf01f41` on
    `qa/linkding-bundle-filters-blind-2`. linkding's suite passed with the new tests (1280, plus 2
    browser tests).
  - **Resume after a crash:** killed mid-step, the service ran only the step in flight again (cloud
    and laptop).
  - **What Restate does not show:** its list shows a run waiting at the gate as "Running", like a
    working one, and it holds none of the QA evidence. `python -m factory report` covers that.
  - All measured (`docs/exploration.md`, "Track 2 results").
- **Factory runs on the laptop bill the Console API key**, not the subscription
  (`scripts/with-console-key.sh`, `docs/decisions.md` 2026-10-12). Cloud sessions build code;
  tickets run on the laptop.
- **Next: track 3**, the deployed environment (`docs/next-session.md`).
- The architecture page is republished with sections 12, 14 and 15 updated (version 7):
  https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa.
- 213 factory tests at that point; `just check` green with `restate-server` installed.

## Where things stood, 2026-10-10

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

- **Adoption** (2026-10-13, `docs/log.md`): `docs/adopt.md`; isso onboarded from it by an agent
  and one ticket shipped; `docs/trust.md` and its page; browser folder optional, `test_helpers`,
  mutation "no mutants" recorded as a skip (`factory/checks/mutants.py`, `factory/steps/verify.py`,
  13 new tests). 227 factory tests.

- **Track 2 on the laptop** (2026-10-12, `docs/runs/2026-10-12-restate-laptop/`,
  `docs/runs/2026-10-12-linkding-bundle-filters-blind-2/`):
  - The cloud branch was rescanned and merged (pull request 16).
  - Restate 1.7.13 was installed from Homebrew, and the stand-in proof was repeated, including a
    `kill -9` mid-Verify.
  - Screenshots of the UI were taken.
  - The bundles ticket ran for real on Restate, billed to the Console API key, and shipped.
  - `scripts/with-console-key.sh` was added.

- **Track 2, the build half** (2026-10-12, cloud session, `docs/runs/2026-10-12-restate-stub/`):
  Restate 1.7.13 from npm, `restate-sdk` 1.0.5 and `hypercorn` 0.18.0 as dev dependencies;
  `factory/restate_service.py` (`run --engine restate`, `restate serve|register|answer`),
  `factory/stub_steps.py`, `driver.run_step` shared by both engines, timeouts 30 + 30 minutes, a
  lock per step; `factory/report.py` (`report`). Tests: 11 with a fake Restate context, 1 against a
  real server (skipped without `restate-server`), 12 for the report. 212 factory tests.
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

- `.artifacts/runs/<ticket id>/`, the run folders: what a resume needs. Gitignored, so
  `git clean -fdx` deletes them; the evidence is copied to `docs/runs/`.
  - Finished: `linkding-sort-by-modified`, `linkding-sort-by-modified-blind` and
    `linkding-bundle-filters-blind-2`.
  - Stopped at its cap, resumable: `linkding-bundle-filters-blind`.
  - The Restate stand-ins: `restate-stub-1` and `restate-stub-laptop-2`.
  - If one is lost, its run starts over (about 5 USD and 15 to 20 minutes per ticket, estimated
    from the runs so far).
- `~/Library/Caches/qa-factory/linkding/`: the clone, its environment and one worktree pair per
  ticket. `targets/linkding/fetch.py --ticket <ticket> [--prepare-e2e]` rebuilds them; Review and
  Ship put the generated tests back from the run folder.
- `~/Library/Caches/qa-factory/restate/`: the Restate server's data (journals, kept a day after a
  run ends) and the service logs. Losing it loses only the journals of runs in flight.
- The Console API key, in this Mac's Keychain as `anthropic-console-key` (never in a file).

## Next

0. Adoption of a third application by `docs/adopt.md` (kickoff A in `docs/next-session.md`), or
   track 3 (kickoff B). Then: mutate non-empty `__init__.py` files; the revert check on the
   developers' own tests.

0a. Track 3, the deployed environment: linkding's Docker image on this laptop, a feature's readable
   cases as a thin suite run against it (`docs/next-session.md`). Docker runs here through colima
   (server 29.5.2, checked 2026-10-12).

1. From track 1: a Verify that stops at the spend cap after its checks passed has no way to
   resume with the readable cases; a re-run starts from a fresh writer (about 4 USD of the writer
   wasted). The sequential run of the bundles ticket was not done (cap); the writer's
   placement of form tests in the API file follows the strategy loosely; a Fable call that runs
   out of budget still counts as "cannot decide" (it now cannot start below 1.50 USD, but can still
   overshoot); the raw writer transcript stays local because it holds this machine's hook output.
2. From the first run: the plan step proposes file names the writer must ignore (fixed by
   prompt, worth a schema); the review step's low findings (random titles in the API fixture)
   could feed back into the writer as a second round; Frame and Plan run before the change exists
   and read the code instead of a diff, which is right for a real ticket but confused the prompt.
3. After the loop runs twice: the agent-written Implement step, the Learn step, flaky quarantine
   and test selection, isso as the second application, and whether Temporal goes under the driver.
