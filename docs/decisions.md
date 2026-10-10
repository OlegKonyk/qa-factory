# Decisions

Oleg's decisions, dated, newest first. An entry is never edited afterwards; a later entry
supersedes it. Each entry says what was decided, the reasoning given, and what it changes.

## 2026-10-10 · One worktree pair per ticket, by delegation

**Decided.** Each ticket gets its own base and head worktrees of the application, at
`<worktrees>/<ticket id>/base` and `.../head` (`factory/driver.py`, `targets/linkding/fetch.py`).
The first run's worktrees were moved there with `git worktree move`, untracked tests included.
Review and Ship put back any generated test missing from the head worktree from the copy in the
run folder (`restore_tests` in `factory/steps/ship.py`).

**Reasoning.** With one shared pair per application, a second ticket checks the head worktree
out at another commit and its Verify cleans the test folders, so a run parked at a gate would
resume on the wrong code without its tests. A run may wait days for a person; nothing else may
touch its trees. Cost: a second checkout and, for browser tests, a second `npm install` and build
per ticket (`fetch.py --ticket <t> --prepare-e2e`).

## 2026-10-08 · Build decisions of the first path, made by delegation

Made by the first build session under the delegation of the same day; each can be overturned by
a later entry. What they settled, with the reason:

1. **Run folders live in `.artifacts/runs/<ticket id>/` inside this repository, gitignored**, with
   absolute paths in every record. One place to look, resumable from any working directory. The
   evidence a person needs is copied to `docs/runs/<date>-<ticket id>/` for the pull request.
2. **The answer file is consumed once.** When a re-run passes `answer.json` to the gated step, the
   driver moves it to `steps/0N-<step>.answerK.json`. A stale answer never answers a later gate.
3. **Models and caps, to be revisited on the numbers:** the test writer and the test-case writer
   run on Opus (`claude-opus-5-5`) with caps of 5.00 and 2.00 USD; Frame and Plan on Sonnet with
   0.50; Review on Opus with 1.00. Measured on the first run: 3.62, 1.28, 0.03, 0.07 and 0.58 USD.
4. **The gate rules of Verify.** The revert check fails when any new test is a crash or a missing
   name on the old code, or fails at head, or when no test proves behaviour; a test that passes on
   both is allowed and reported as a regression guard. Mutation fails the run only when mutmut
   could not run, when no mutant was checked, or when the generated tests kill no mutant on the
   changed lines; scores are reported, not thresholded, until more runs show what a threshold
   should be. The behaviour rule of the sorter counts an assertion anywhere in the traceback that
   passes through the test file or a declared test-support file, so Playwright's `expect` and
   the application's own assertion helpers count.
5. **The writer may only add new files under the two test folders.** Anything else it touched is
   reverted and the step fails. The plan's file names are advisory; the writer's placement is
   fixed by the strategy rule (`test_<feature>_api.py`, `e2e_test_<feature>.py`).
6. **Pieces copied from elsewhere:** the signoff plugin's `cases.py` (unchanged), the shape of the
   old lab's pytest plugin for the failure sorter (rewritten, 159 lines), the mutmut recipe from
   the lab's probe. Nothing else from the lab; its mutation wrapper, linter and sandbox were not
   copied (rule 3).
7. **The py-testing skills are not injected into the test writer's prompt.** They teach
   pytest-playwright fixtures and a request-context client; linkding's tests must join its own
   unittest-style suites, so the prompt points the writer at the application's helpers and says
   its conventions win. Recorded for the plugins project in `docs/plugin-notes.md`.

## 2026-10-08 · The plugins are the toolchain for building the factory

**Decided.** Sessions that build the factory use Oleg's plugins as their toolchain: `supervisor`
(triage, delegation to cheaper models with evidence contracts, review before a slice is accepted),
the `py-testing` skills for test code, `reviewing-diffs` before a pull request. Reason, his words:
"so we can use tokens and have code quality." The plugins get improved along the way through
`docs/plugin-notes.md`. The previous entry stands for the factory itself.

**What it changes.** A toolchain section in `CLAUDE.md`; `docs/next-session.md` says to build
with the plugins.

## 2026-10-08 · The plugins project is separate; the factory may use or copy pieces; lessons flow back

**Decided.** Oleg's Claude Code plugins (`~/dev/konyklabs/claude-plugins`) are a separate project
that he improves along the way. The factory does not depend on them. A step may use a plugin, or
take a copy of one into this repository, when that is the shortest route to a running path; the
decision is made per step, at build time, and recorded in the step's artifact. Every factory
session writes what it learned about the plugins into `docs/plugin-notes.md` (newest first: which
plugin, what was missing or wrong, what would have helped), for him to carry into that project.

**Supersedes** item 10 of the delegated decisions, where signoff and py-testing were "in the first
path" and the supervisor agents were the simplified steps. They are now candidates, not parts.
The Learn step of the factory stays as described there and is unchanged.

## 2026-10-08 · Rapid mode: a session merges its own pull request, nothing waits for Oleg

**Decided.** A session merges its own pull request once `just check` is green and its output is in
the body, including a pull request that changes `CLAUDE.md` or `hooks/`. No pull request waits for
his yes. He reads the merged result and overturns what he dislikes with a later entry here.

**Reasoning, his words.** "This is experimental stuff. This is rapid development mode. I don't
want you to wait for me for nonsense."

**What it changes.** The rapid mode rule in `CLAUDE.md`. Pull requests 1 and 2 are merged by this
session. The "Waiting on Oleg" list in `docs/status.md` keeps only things he alone knows.

## 2026-10-08 · The planning questions, decided by delegation

Oleg: "Please use your best judgment to answer these questions. When it comes to test
applications, you heard what I said: it's going to be a combination of both." Recorded here as his
decisions, made by delegation; each can be overturned by a later entry. The principle he gave: the
pieces are swappable, so what matters now is the QA step and what happens inside it.

1. **The contract between steps.** One input envelope (ticket, repository at base and head with a
   run recipe, the artifacts so far, the round number) and one output envelope (status pass, fail
   or needs_person; artifacts; reason; the gate's who, question and context). Artifacts are typed
   files in a run folder outside the session: plan, change, tests, verdict, test_cases, placement,
   review, decision. JSON-serializable, files by path. Cut down after the first real run.
2. **Target applications.** Both: linkding (Django, REST API and browser UI, 11 real 2026
   features with the developers' own tests) first, isso (Python, SQLite, browser widget) second.
   A greenfield target is added once the loop runs, shaped like the team's new work.
3. **Checks that prove a test is not misleading, in order.** Lint of generated tests; the revert
   check with the sorter that says why the test failed on the base commit (only a failed
   behaviour check counts); mutmut 3.8 on the functions the change touched; the application's
   own suite still green. Cheapest first, each can stop the run. The checks run on every new test
   in the change, the implementer's TDD tests included; QA writes tests only for what is still
   uncovered.
4. **What a person approves, and where.** Readable test cases in the format the signoff plugin
   writes, one Markdown page per test, kept beside the test as one artifact pair. Approved on the
   pull request that carries the tests and the cases; the PR approval is the answer the driver
   waits for, and a file in the run folder is the fallback.
5. **The regression suite.** Approved tests go into the application's own test folders under its
   own pytest configuration (API and browser tests in separate folders), merged by the Ship step.
   Flaky-test quarantine by randomised re-runs and test selection by impact come when a run shows
   the suite is slow or flaky, not before.
6. **The test strategy.** Default for simple web applications: most new coverage at the API level,
   one or two browser tests per feature for the path a user sees, unit tests left to the
   implementer's TDD. Closer to the honeycomb than the pyramid. Written as a short rule file per
   application that the QA step reads; every placement decision is recorded with its reason.
7. **Which AI writes the tests.** Claude Code, headless, a fresh session per step, run as a
   subprocess by the driver, with a spend cap per step measured and set in the first build
   session. Its prompt carries the ticket, the change, the application's strategy rule and the
   py-testing skills.
8. **Human gates QA owns.** Two: approve the test cases, and the Verify escalation (too many
   rounds, environment problem, deviation). The QA step may raise "this criterion cannot be
   tested" back to the ticket owner.
9. **The first end-to-end path.** One real linkding feature from its 2026 history. The ticket is
   written from the feature's description. Frame and Plan are one-prompt steps. Implement is
   simplified: the developers' real commit is the change. Verify runs fully. The driver stops,
   Oleg approves on the pull request, the driver resumes, the tests merge into linkding's suite
   and the suite runs green. Review and Ship are one-prompt steps. All on the plain Python driver.
10. **Plugins as factory parts; the factory improving itself.** In the first path: signoff writes
    the readable test cases and ranks the gaps; py-testing is loaded into the test writer. The
    simplified steps use the supervisor plugin's agents where that is the shortest route and a
    thin prompt otherwise. Review lenses (reviewing-diffs, prod-readiness) and the Learn step
    (every run's decisions, interventions and findings become decision artifacts; a Learn step
    proposes edits to the rules and skills as a pull request a person approves) come after the
    loop runs. Running the plugins headless inside a step is unverified until the first run.

**Still open, for Oleg, none of them blocking the build:** whether the factory at work is on
Temporal (decides whether Temporal goes under the driver later); whether the old lab's worktrees
and laptop-only branches are kept; his yes on `CLAUDE.md` (pull request 1 and the Temporal line
changed in this one).

## 2026-10-08 · Temporal is deferred, not dropped: the first path runs on plain Python

**Decided.** The first end-to-end path is built as plain Python: the step contract (one input
envelope, one output envelope, artifacts as files in a run folder), a driver that is a loop over
the steps and exits when a step needs a person, and re-running resumes at the last finished step.
Temporal is not under it. When the loop runs end to end on a real application, Oleg decides
whether Temporal goes under it.

**Reasoning, as agreed.** On one laptop with one ticket at a time, what Temporal gives (a run that
survives a crash, a gate that parks for days, retries, round caps) is replaced by a run folder and
a resume, and the only real loss is a live UI. What it costs is paid up front: workflow code may
not touch files, the network or the clock, so every repository-touching step becomes an activity
with serialized payloads; non-determinism on replay is a new class of bug; four processes run
before a ticket moves; and the Temporal Agent Harness, the piece that would supply gates and a UI,
is Pre-Alpha by its own classifier. Estimated, not measured: about one build session of plumbing
before the first real test exists.

**Kept open so the door stays open.** The envelope stays JSON-serializable and artifacts are
referred to by file path, which Temporal needs and which is good hygiene anyway. Each step is a
function of one input envelope to one output envelope, so a later Temporal wrapper is thin.

**The fact that decides it later.** Whether the factory at work is built on Temporal. If it is,
matching it is worth the plumbing because the QA step carries over. Not known in this session.

**What it changes.** `CLAUDE.md` says the factory "runs on this machine, on Temporal"; that line
is to be changed to say Temporal is deferred, in a pull request that waits for Oleg. Open question
3 in `docs/status.md` ("Temporal on this machine") is closed by this entry. Question 7 of the
planning session (the backbone on Temporal, harness or raw SDK) is closed by this entry; which AI
writes the tests is still open.

**Reference kept.** The Temporal Agent Harness (`temporal-community/temporal-agent-harness`,
0.6.0, MIT, Python 3.11 to 3.14) was read from source and not run. What it would give if adopted
later: a durable workflow per step with typed operations, human gates as durable waits, callback
tools that run on the laptop, one replayable event stream and a prebuilt browser UI. What it lacks:
a Claude Code inner loop (its integrations are Gemini, the OpenAI Agents SDK and PydanticAI).
Its own `docs/internal/what-the-harness-adds.md` and `docs/internal/core-concepts.md` are the two
files worth reading.
