# Architecture

The picture is a published page: https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa (private to
Oleg), built by `docs/pages/architecture/build.py` and updated in place. It shows the flow, the
stages inside Verify, the revert check, what a person approves, how a run stops and resumes, where
everything lives, and the first run's numbers. This file keeps the two tables the page adds beyond
`docs/status.md`, so the substance survives without the page. As of 2026-10-13.

## Extension points: where a new use case attaches

| | Point | Today | Where it lives | Already on the record |
|---|---|---|---|---|
| A | Ticket source | A JSON file written by hand from an upstream pull request | `targets/<app>/tickets/` | Tickets written with ticket skills (brief) |
| B | Application recipe | linkding and isso: location, Python, test folders (browser optional), suite commands, strategy rule; `docs/adopt.md` is the procedure | `targets/<app>/app.json`, `strategy.md`, `fetch.py` | a greenfield app once the loop runs |
| C | Test surfaces | API tests through Django's test client and Playwright browser tests in Python, inside the app's own test classes | `factory/prompts/write_tests.md`, the strategy rule | Mostly API, one or two browser tests per feature |
| D | Checks | Lint, revert, mutation, suite, cases, in that order; a failure gets one repair round, then Fable 5.1's decision | `ATTEMPT_CHECKS` and `FINAL_CHECKS` in `factory/steps/verify.py`, `factory/checks/`, `factory/escalate.py` | Flaky quarantine and test selection when a run needs them |
| E | Gate channel | `question.md` out, `answer.json` in, one approver; only Verify raises a gate | `factory/driver.py`, `factory/steps/verify.py` | A gate at every step, correct as well as approve, a notification and a listing (roadmap item 4); approval on a pull request once the app is forked (item 6) |
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
| Applications | Two (linkding, isso); a new one needs a recipe, a strategy rule, a fetch script and tickets, by `docs/adopt.md` | The checks assume Python: ruff, pytest, mutmut, a pytest plugin reading Python tracebacks | a greenfield app next |
| People | Nobody when every check passes; a person only when Fable 5.1 cannot decide about a check that still fails, or a ticket asks by rule | No notification, no record of who answered beyond the file | Stronger models before people (10 Oct), built the same day |
| Retries | One repair round, one guided round, one Review fix round; caps per ticket in `rounds.json` (3 writer rounds, 2 Fable calls, 15 USD by default) | A repair round cost 3.17 USD once (measured); a Fable call about 1 USD | The loop back to Implement waits for an agent-written Implement |
| Machines | This laptop | Run folders and caches are local; a resume needs the run folder | Local first is a constraint of the brief |

## Use cases

Filed in `docs/inputs.md` on 2026-10-10; the exploration that would answer them is
`docs/exploration.md`.

| | Use case | Attaches at | Exists today | Missing | At scale |
|---|---|---|---|---|---|
| UC1 | Watch the factory work ("some skin ... so I can start observing stuff") | H, E | A record per step, `python -m factory status`, the question file, the static page | A live view of runs, steps and waiting gates; a view of each run's QA evidence | Tickets at once, people |
| UC2 | Every repository agent-friendly, with trusted end-to-end tests that also run on the deployed environment | B, C, F | Trusted API and browser tests inside the app's suite | Tests that run against a deployed URL (linkding's browser tests seed data through the ORM in a test server); an agent-friendly checklist | Applications, machines |
| UC3 | The loop for a small feature: QA after the change, or alongside it | G, D, H | QA after the change, in a fresh session reading the diff | An acceptance lane from the criteria, the join, the capped loop back to Implement | Time per ticket, retries |
