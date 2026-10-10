# Architecture

The picture is a published page: https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa (private to
Oleg), built by `docs/pages/architecture/build.py` and updated in place. It shows the flow, the
stages inside Verify, the revert check, what a person approves, how a run stops and resumes, where
everything lives, and the first run's numbers. This file keeps the two tables the page adds beyond
`docs/status.md`, so the substance survives without the page. As of 2026-10-10.

## Extension points: where a new use case attaches

| | Point | Today | Where it lives | Already on the record |
|---|---|---|---|---|
| A | Ticket source | A JSON file written by hand from an upstream pull request | `targets/<app>/tickets/` | Tickets written with ticket skills (brief) |
| B | Application recipe | linkding only: location, Python, test folders, suite commands, strategy rule | `targets/linkding/app.json`, `strategy.md`, `fetch.py` | isso second; a greenfield app once the loop runs |
| C | Test surfaces | API tests through Django's test client and Playwright browser tests in Python, inside the app's own test classes | `factory/prompts/write_tests.md`, the strategy rule | Mostly API, one or two browser tests per feature |
| D | Checks | Lint, revert, mutation, suite, cases, in that order; each returns a report or stops the run | `CHECKS` in `factory/steps/verify.py`, `factory/checks/` | Flaky quarantine and test selection when a run needs them |
| E | Gate channel | `question.md` out, `answer.json` in, one approver | `factory/driver.py` | Approval on a pull request once the app is forked |
| F | Destination | A commit on `qa/<ticket>` in the local worktree, then the full suite | `factory/steps/ship.py` | A pull request to the app's repository |
| G | Change source | The developers' real commit | `factory/steps/implement.py` | An agent writes the change test-first, after the loop runs |
| H | Orchestration | One Python process, steps in order, one ticket at a time, a run folder per ticket | `factory/driver.py` | Temporal under the driver: deferred until the loop runs |

## Where it is fixed today

Facts for the scaling discussion, not proposals. Measured on the first run unless marked
estimated.

| Dimension | Today | What gives first | Decided or open |
|---|---|---|---|
| Tickets at once | One per process, in order; 13.8 min from Frame to the approval | Two tickets need two processes and nothing schedules them; each ticket already has its own worktrees | Open; Temporal deferred until the loop runs |
| Spend per ticket | 5.58 USD, 3.62 of it the test writer (Opus) | About 560 USD for 100 tickets a month (estimated: the first run times 100) | Models and caps by delegation, revisit on the numbers |
| Time per ticket | Writer 414 s, mutation 159 s, cases 116 s, suite 93 s | The whole suite runs every time; mutation runs twice | Test selection by impact when a run shows the suite is slow |
| Disk | Per ticket: head worktree 61 MB (47 MB node_modules), base 6 MB, run folder 48 MB; per app: environment 294 MB; shared: browsers 1.1 GB | node_modules and the two app copies per run folder grow with every ticket | Open |
| Applications | One; a new one needs a recipe, a strategy rule, a fetch script and tickets | The checks assume Python: ruff, pytest, mutmut, a pytest plugin reading Python tracebacks | isso second, then a greenfield app |
| People | One approver, by file, on this laptop | No notification, no record of who answered beyond the file | Approval on pull requests once the app is forked |
| Retries | None; a Verify failure or a review finding stops the run | Each retry is a fresh Verify, about 5 USD and 13 min (estimated from the first run) | The brief's capped loop back to Implement; not built |
| Machines | This laptop | Run folders and caches are local; a resume needs the run folder | Local first is a constraint of the brief |

## Use cases

None recorded yet. Each one Oleg names is filed in `docs/inputs.md` and gets a card on the page:
in his words, the points it attaches at, what exists, what is missing, which rows above it hits,
and the questions only he can answer.
