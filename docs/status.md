# Status

Read this first. Update it last, in the same pull request as the work.

## Waiting on Oleg

1. Will tickets at work state the public contract (field names, values, labels, routes) before
   coding starts? Track 1's blind tests met the change with no mismatch, but both tickets were
   written from finished commits. If not, Plan has to fix the contract first.
2. Run the bundles ticket again, from a fresh blind writer, as the real ticket on Restate? About
   5.5 USD (estimate from the two blind runs). It stopped at its 8 USD cap after its checks passed,
   and a failed Verify re-runs from the start: nothing resumes after a cap stop yet. The new run
   would also give a second blind sample of the same ticket. Its ticket is ready
   (`targets/linkding/tickets/bundle-filters-blind-2.json`). Recommended: yes. If no, the laptop
   session writes a third ticket from linkding's 2026 history instead.

## Where things stand, 2026-10-12

- **The factory runs on Restate, behind a flag, proven with stub steps** (cloud session,
  `docs/exploration.md`, "Track 2, the build half"). One workflow per ticket, each step a durable
  step calling the same step body as the plain driver, the gate a promise answered over HTTP. Killed
  mid-step, it resumed with only the step in flight run again; the Restate server killed while a
  run waited at the gate lost nothing. A step longer than Restate's timeouts ran twice at once
  until a lock per step was added. All measured, with stub steps, no model calls.
- **`python -m factory report <run folder>`** writes the QA evidence page of a run; generated for
  the three committed runs (`docs/runs/*/report.md`).
- **The pull request of this work is open, not merged**: the cloud session had no guard term list,
  so the laptop rescans and merges it (below, "Next, on the laptop", step 0).
- 212 factory tests; `scripts/check.sh` green (`docs/log.md`, 2026-10-12).

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

- `.artifacts/runs/<ticket id>/`, the run folders: what a resume needs. Three exist:
  `linkding-sort-by-modified` and `linkding-sort-by-modified-blind` (finished),
  `linkding-bundle-filters-blind` (stopped at its cap, resumable). Gitignored, so
  `git clean -fdx` deletes them. If one is lost, its run starts over (about 5 USD and 13 minutes
  for the first ticket, estimated from its run). The evidence is copied to `docs/runs/`.
- `~/Library/Caches/qa-factory/linkding/`: the clone, its environment and one worktree pair per
  ticket. `targets/linkding/fetch.py --ticket <ticket> [--prepare-e2e]` rebuilds them; Review and
  Ship put the generated tests back from the run folder.

## Next

0. Track 2's laptop half (below, "Next, on the laptop"), then track 3 (the deployed environment,
   linkding's Docker image on this laptop).

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

## Next, on the laptop

What the cloud session could not do. Run in `~/dev/qa-factory`, in this order.

**0. Rescan, check and merge the cloud branch.** The cloud had no term list, so its guard passed
everything.

```
git fetch origin claude/restate-driver-k4pqfg
B=origin/claude/restate-driver-k4pqfg
terms=$(mktemp); sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e '/^$/d' ~/.config/konyklabs/blocklist.txt > "$terms"
{ git diff -U0 main...$B | grep '^+'; git diff --name-only main...$B; git log --format=%B main..$B; } \
  | grep -n -i -f "$terms" && echo BLOCKED || echo clean
```

Read the pull request's title and body for the same terms too. Then `git checkout
claude/restate-driver-k4pqfg && uv sync && just check`, and squash-merge the pull request.

**1. Install and start Restate on macOS.**

```
brew install restatedev/tap/restate-server restatedev/tap/restate
restate-server --base-dir ~/Library/Caches/qa-factory/restate &      # UI at http://localhost:9070
uv run python -m factory restate serve &                             # the real steps, port 9080
uv run python -m factory restate register
PATH=$(brew --prefix)/bin:$PATH just check                           # now runs the live Restate test too
```

The stub proof can be repeated first, at no model cost:
`uv run python -m factory restate serve --port 9081 --steps factory.stub_steps`, register it with
`--uri http://127.0.0.1:9081`, then `uv run python -m factory run docs/runs/2026-10-12-restate-stub/ticket.json
--engine restate --key stub-laptop-1`. Register the real service on 9080 again afterwards.

**2. The real ticket (step 3 of track 2), on question 2's answer.** If yes:

```
uv run python targets/linkding/fetch.py --ticket targets/linkding/tickets/bundle-filters-blind-2.json --prepare-e2e
uv run python -m factory run targets/linkding/tickets/bundle-filters-blind-2.json --engine restate
curl -s -X POST localhost:8080/factory/linkding-bundle-filters-blind-2/status
```

The ticket sets `"gate": "person"`, so the run parks after Verify even when its checks pass: that
is the run waiting at a gate to screenshot. The session answers it itself over HTTP and records
that it did (Oleg is not asked to approve passing work):
`curl -X POST localhost:8080/factory/linkding-bundle-filters-blind-2/answer -H 'content-type: application/json' -d '{"approved": true, "by": "session", "note": "gate set for the Restate screenshot"}'`.
Leave `.artifacts/runs/linkding-bundle-filters-blind/` as it is. If no, write a third ticket from
linkding's 2026 history, without the gate field unless a screenshot still needs one.

**3. What to measure.**

- Screenshots of `localhost:9070`: the invocation while Verify runs, and while it waits at the gate
  (`suspended` after 30 minutes, `running` before that).
- Resume after a kill: kill the service (`kill -9 <pid>` of the python process, not `pkill -f`)
  during Frame or Plan, which are cheap, restart it, and read `restate invocations describe <id>`:
  the finished steps replay from the journal and only the step in flight runs again. Do not kill it
  during Verify: that repeats the test writer's spend.
- Time: each step's duration from its record, Verify's wall time against the 30 + 30 minute
  timeouts, and the delay from the service coming back to the step restarting (15 s measured in the
  cloud). Spend: `uv run python -m factory summary .artifacts/runs/linkding-bundle-filters-blind-2`.
- The QA evidence: `uv run python -m factory report .artifacts/runs/linkding-bundle-filters-blind-2`.

**4. Step 5's rest.** Add the laptop's results to `docs/exploration.md`; update the architecture
page's sections 12 and 14 (`python3 docs/pages/architecture/build.py`), read
https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa, then republish the built file to that URL.
