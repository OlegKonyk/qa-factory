# How can we trust tests written in the session that implemented the change?

The question Oleg's team asks (`docs/inputs.md`, 2026-10-13). This is the factory's answer, from
what has run here, with every number measured on real applications unless marked. The page form
for a meeting is https://claude.ai/artifact/JEQNo6pu9zVp6xbAR98HEt (private to Oleg).

## The short answer

You cannot, and the factory does not try to. A test written in the same session as the change
shares the change's blind spots: it was written to pass against the code as it was just written.
Measured on linkding's sort feature (2026-10-08): the developers' own tests, written with the
code, fail on the code before the change only because a name is missing, not because the order is
wrong. They prove the code is new. They do not prove what it does. The old lab measured the same
on isso, 2026-10-07: in 3 of 4 recent features, the developers' new tests failed the old code
before any assertion ran.

So the factory does three things instead:

1. **A different session writes the acceptance tests.** A fresh headless Claude Code session with
   its own prompt, its own budget, and no memory of the implementation. In blind mode it works in
   a copy of the code before the change, with the change, every other copy of the code and git
   hidden from it, and its session transcript audited afterwards for any attempt to look.
2. **Deterministic tools decide whether the tests prove anything.** Not a model's opinion:
   - the revert check runs every new test twice, with the change and with the change taken out
     (the source files and the test helpers put back to their old version). A test counts only
     if it passes with the change and fails without it on an assertion. A test that fails without
     the change on a missing import, attribute or name is rejected: it proves the code is new,
     nothing more;
   - mutation testing (mutmut 3.8.0) on the functions the change touched, with the generated tests
     alone, with the developers' tests added, and with the developers' tests alone. A test set that
     kills no mutant on the changed lines fails the check;
   - lint of the generated tests: ruff, no test without an assertion, no sleeps, no mocking of the
     application's own code;
   - the application's whole suite with the new tests in place.
3. **A person approves something readable.** One test case in plain words per automated test, in
   a fixed skeleton a linter checks, committed beside the tests. The automated test is the proof;
   the case is what a product owner reads.

When a check fails, the factory does not ask a person first: one repair round in a fresh session,
then a stronger model (Fable 5.1, read-only, capped) decides retry, the change is wrong, or an
environment problem. A person is asked only when it cannot decide. Rounds and spend are capped
per ticket.

## What the runs showed

Four tickets on linkding (a Django bookmark manager with a REST API and browser pages), 2026-10-08
to 2026-10-12, and one on isso (a werkzeug comment server, API only) on 2026-10-13. "Blind" means the tests were written from the ticket and the code before the change
only; the writer never saw the change.

| Ticket | Written | Tests | Pass with the change | Fail without it, on an assertion | Fail without it for a missing name, or crash | Mutants killed on the changed lines | Spend, time |
|---|---|---|---|---|---|---|---|
| Sort by modified date | after the change | 6 | 6 | 5 (+1 regression guard) | 0 | 10 of 10 | 5.58 USD, 13.5 min |
| Sort by modified date | blind | 4 | 4 | 3 (+1 regression guard) | 0 | 10 of 10 | 5.48 USD, 15 min |
| Filter bundles by state | blind | 13 | 13 | 12 (+1 regression guard) | 0 | 16 of 16 | 8.47 USD, stopped at its cap before the readable cases |
| Filter bundles by state, again | blind | 7 | 7 | 7 | 0 | 16 of 16 | 5.44 USD, 19.4 min |
| isso: no-cache headers on comment routes (a second application, 2026-10-13) | blind | 6 | 6 | 3 (+3 regression guards the contract asked for) | 0 | not applicable: mutmut makes no mutant for the three changed functions (decorated) | 5.69 USD recorded, Verify 7.5 min |

- A regression guard is a test that passes on both versions (for example, the fallback for an
  unknown sort value). It is allowed and reported as such; it is not counted as proof.
- On the sort ticket the blind tests were exactly as strong as the tests written with the change
  in view: 27 of 108 mutants killed over the whole function, 10 of 10 on the changed lines, both
  ways.
- The developers' own tests on the same functions: 98 of 108 and 77 of 82 over the whole function.
  They cover more of the function because they also cover the code that was already there; on
  the changed lines they tie with the generated tests.
- Every blind writer's transcript was audited: 39, 24 and 24 tool calls, none touching the hidden
  code or git.
- What went wrong in the four runs was the factory's own checks, not the tests: the revert check
  once judged the tests with the new helpers in place, a repair round was failed for a file
  `npm install` had changed, the stronger model once ran out of budget. All three are fixed and
  each is recorded in `docs/log.md`.

The run report (`python -m factory report <run folder>`) puts every test's two results, the
mutants that survived, the cases, the rounds and the spend on one page per ticket.

## Where this answer stops

- One application, four runs, two of them the same ticket. Blind writers vary run to run: 13
  tests and then 7 on the same ticket, both killing every mutant on the changed lines, 78 % and
  62 % over the whole function. One pair is not a trend.
- Both blind tickets stated the public contract (routes, fields, values, labels) because they were
  written from finished commits. A ticket written before the code may not; then the blind lane
  hits mismatches and the plan step has to fix the contract first. Unmeasured.
- No bug-fix ticket has run. The tests so far are acceptance tests of a feature.
- Mutation scores are reported, not thresholded. The only hard rule is "kills something on the
  changed lines". What a threshold should be waits for more runs.
- Mutation testing has a blind spot of its own: mutmut 3.8.0 makes no mutant for most decorated
  functions, and the factory skips code in `__init__.py`. On the isso ticket every changed
  function was one of those, so the revert check was the only proof the tests exercise the
  change. The report says so; it does not pretend a score.
- The factory today needs the developers' finished commit. Blind means the writer did not see the
  change, not that it ran at the same time as the implementation.
- Approval is a file in the run folder, Ship is a local commit on a `qa/` branch. A pull request
  and a notification are not built.
- Nothing has run against a deployed environment yet.

## The scenarios Oleg raised

**Tests in the implementing session.** Keep them as the developer's unit tests, and let the
factory's checks judge them like any other test. Since 2026-10-13 the revert check runs on the
developers' own new tests too, as a report (`python -m factory devtests <run folder>` on a
finished run; `verify/developers_revert.json` in a new one). Measured on the three tickets whose
worktrees are on this laptop, all written by the applications' own developers with the change:

| Ticket | Developers' new tests | Fail on the old code on an assertion | Fail only for a missing name | What they reach for |
|---|---|---|---|---|
| linkding, sort by modified date | 2 | 0 | 2 | `BookmarkSearch.SORT_MODIFIED_ASC`, a constant the change adds |
| linkding, filter bundles by state | 5 | 0 | 5 | `BookmarkBundle.FILTER_STATE_YES`, a constant the change adds |
| isso, no-cache headers | 2 | 0 | 2 | `NO_CACHE_HEADERS`, imported from the code under test |
| The factory's blind tests on the same three tickets | 4, 7, 6 | 3, 7, 3 | 0, 0, 0 | the public surface: query strings, JSON fields, header values spelled out |

Nine of nine developers' tests fail on the old code before any assertion runs, because they use
names the change introduces. They do check behaviour once the names exist (they pass with the
change, and they kill mutants: 98 of 108 and 77 of 82 on the linkding functions). What they cannot
do is tell "the feature is missing" from "the feature is wrong", and a reviewer reading them
cannot tell either without running them against the old code. That is the measured content of
"tests written with the code share its blind spots". Three tickets, two applications, nine tests:
a pattern, not yet a law.

**Develop on mocks, validate on the deployed environment.** Read as two verification points for
one set of acceptance tests:

1. In the service's own suite, with its dependencies mocked the way the suite already mocks them.
   This is where the factory runs today: the revert check, mutation testing and the suite all run
   here, and they are what makes the tests trustworthy at this point.
2. The same cases against the deployed environment, with real dependencies, reached by a base URL
   and creating their data through the public API. This is the second point. It is not built
   (track 3 of `docs/exploration.md` is the plan for it on linkding's Docker image). The tests
   written at point 1 can only run at point 2 if they create data through the API and not the
   database; `docs/exploration.md` lists what that takes of the repository.

Keeping mocks reliable is a separate problem the factory has not touched: what a mock is kept
from (a recorded exchange, the dependency's interface document, the dependency's own test
double) and what checks it against the real service. Nothing is built or decided. Recommendation:
wait for the first service with real dependencies, see how its suite mocks them, and add the
check that run shows is missing (rule 3 of `CLAUDE.md`).

**Acceptance criteria on the input as verification points.** Already the shape: the Frame step
restates every criterion as something a test can check and names its surface (API, browser,
unit, none), and lists what a test writer would have to guess. Track 1 showed the blind lane
holds when the ticket states the public contract; `docs/adopt.md` makes the contract a field of
the ticket. A criterion the factory cannot test is reported back on the ticket, not silently
skipped.

**Other scenarios the same mechanisms cover, and what each would need:**

| Scenario | What the factory does today | What is missing |
|---|---|---|
| A bug fix | the same loop; the ticket's contract is the wrong and the right behaviour | a run on one bug ticket |
| A change with no HTTP surface (a library, a job) | mutation and the revert check work on any pytest suite | a strategy rule for unit-level tests; the writer prompt assumes an API folder |
| A service with external dependencies | the suite runs as it is, mocks included | the deployed run; a mock-freshness check |
| A TypeScript or other non-Python service | nothing | the checks read pytest tracebacks and run mutmut; a second toolchain |
| Tests the team wrote by hand | mutation testing reports them as a set; the revert check reports their verdicts | a run on the team's own tickets |

## What to take to the meeting

1. Tests from the implementing session prove the code is new, not what it does. Measured: 9 of 9
   developers' tests on three tickets fail on the old code only for a name the change adds.
2. Trust comes from a separate session plus deterministic checks: fails without the change on an
   assertion, kills mutants on the changed lines, the suite stays green, a readable case per test.
3. On four runs the blind tests met the real change with no mismatch and were as strong as tests
   written with the change in view. Limits: one application, four runs, contracts stated.
4. The deployed-environment run and anything about mocks are not built. The adoption guide
   (`docs/adopt.md`) says what is ready and what a service needs to use it.
