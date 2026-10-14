# Decisions

Oleg's decisions, dated, newest first. An entry is never edited afterwards; a later entry
supersedes it. Each entry says what was decided, the reasoning given, and what it changes.

## 2026-10-14 · The roadmap's four questions, answered

**Decided, his words:** "adopt, public, no, keep."

1. **Adoptable first.** Roadmap items 1 to 4 (the deployed run, the three fixes, a third
   application, every person point) before item 5 (an agent writes the change).
2. **The third application is a public one**, chosen by the session that onboards it, from the
   shape in item 3. His service at work comes later, from `docs/adopt.md`, when he chooses.
3. **Tickets at work will not state the public contract before coding.** So the readiness check
   that sends a ticket back for the missing contract is built now, as the Frame gate of item 4;
   the tracker integration stays item 7, later.
4. **Restate stays**, behind its flag until item 6 as recommended. "If there is a better
   alternative, we can adopt that": no comparison is run (rule 2); a replacement is adopted when
   a run shows a need Restate cannot meet or when work settles on Temporal.

**Also his:** research continues, as a standing part of the roadmap, on two questions of his:
what makes a repository factory-friendly and agent-efficient, QA-centric; and which new tools
the factory can use. One short labelled pass per session, serving the next build step.

## 2026-10-14 · Always portable

**Decided, his words:** "this whole setup needs to be portable onto generic applications. If, on
the other machine, I want to give this a try on a real app, this repository needs to be ready for
that: have it ready with recipes describing what needs to be done."

- Rule 9 of `CLAUDE.md`: at every merge, the repository can be cloned on another machine and
  pointed at a generic Python application by an agent that reads `docs/adopt.md` and nothing
  else; a change that alters what a run needs updates the guide in the same pull request;
  anything that only works on this machine is named there.
- `docs/adopt.md` is the recipe and stays the one tested procedure (2026-10-13). The roadmap
  carries a table of where the rule is not yet true.

## 2026-10-14 · After his review of the roadmap, by delegation

Made by the session that answered his review of the same day (`docs/inputs.md`: every person
point exposed, what Restate is for, the research he never saw); each can be overturned by a later
entry.

1. **"Every person point exposed" is roadmap item 4, in Now.** The brief's table already names a
   person point per step; his review asks that all of them exist. Four of the seven never stop
   today, nobody is told when a run waits, and a person can approve or refuse but never correct
   an artifact and resume. The item is built on the step envelope (status `needs_person` with a
   gate), so the plain driver and Restate get every gate; one gate contract (kind, who, question,
   context, accepted answers), per-step configuration `auto | model | person` replacing the single
   `gate` field, a notification, a listing of waiting runs, and the answerer in the record. Item
   numbers after it shift by one; question 3's item is now 7.
2. **Restate stays behind `--engine restate`, with the reason restated.** Its value is the
   durable wait, which rises with the number of gates (item 4) and of runs at once (item 9), not
   with the plain path. The default engine is decided when item 6 puts approvals on pull
   requests. Removing it is his option (roadmap question 4); it is not done by delegation.
3. **Research is recorded in the repository, labelled, and dated.** `docs/research/` starts with
   `2026-10-14-factory-landscape.md`; the lab's five research files are pointed to from it with
   what each covers, not copied. What the pass found that is not needed now (a protocol language,
   Agent HQ, routines, the Temporal harness at 0.6.0) is recorded with dates so no session
   researches it again.
4. **The three pages recorded as published (architecture, trust, roadmap) could not be read from
   this session**, so the roadmap page is republished at a new link, recorded in
   `docs/status.md`. The old links stay in the record; which account published them is his to
   say.

## 2026-10-14 · The roadmap's swappable choices, by delegation

Made by the session that wrote `docs/roadmap.md` at his request (`docs/inputs.md`, 2026-10-14);
each can be overturned by a later entry. The roadmap's order is a recommendation, not a decision:
which group comes first is his (question 1 there).

1. **Restate stays behind `--engine restate`.** The plain driver is what the adoption guide uses,
   and Restate's gains (resume after a crash, a page per run) matter once runs are many or long.
   Revisit with roadmap item 8 (more tickets at once). Closes the open question of 2026-10-12.
2. **The third application is chosen by the session that onboards it**, from the shape in roadmap
   item 3 (a web API service, a `src/` layout, a database in Docker, an outside HTTP service it
   calls), unless he names his own. Its ticket is a bug fix, also chosen by that session.
3. **The three factory fixes run in a cloud session** paid by the one-time credit: they are code
   with factory tests and no model calls, which is what cloud sessions are for (2026-10-12).

## 2026-10-13 · Wrapping up for adoption, by delegation

Made by the session that wrote the adoption guide and ran isso, under his direction of the same
day (`docs/inputs.md`: wrap up so a real project can adopt the factory, set up by agents, with
tested instructions; move fast); each can be overturned by a later entry.

1. **The browser test folder is optional in a recipe.** `browser_tests_dir` and
   `browser_test_files` may be left out of `app.json`; every step then treats the application as
   API-only and the writer is told to write API tests only. Reason: a small service, and isso,
   have no Python browser tests, and the factory refused to run without them.
2. **The guide is the product, and it is tested by use.** `docs/adopt.md` is written for an agent
   on a fresh machine. It counts as tested only when an agent that reads nothing else onboards a
   real application and runs a ticket through; what that agent had to guess goes back into the
   guide. isso was that application (the second application, decided 2026-10-08).
3. **Nothing is built for mocks.** His scheme (develop and fix on mocks, the deployed run validates
   the real implementation) is read as two verification points for one set of acceptance tests;
   the first is what the factory does today, the second is track 3. What keeps a mock reliable is
   not decided and waits for the first service with real dependencies (rule 3).
4. **Track 3 stays next and did not start this session.** The deployed run is the one mechanism he
   named that is not built; it is reported as not built rather than squeezed in.
5. **The trust answer is a document and a page**, `docs/trust.md` and its published page, written
   from the four runs' numbers only. Nothing in it is estimated.
6. **Mutation that cannot run is reported, not repaired.** When mutmut makes no mutant for any
   changed function (mutmut 3.8.0 skips most decorated functions and decorators with an inner
   function; measured on isso 7e91d59), the mutation check records "not applicable" with the
   function names and the run goes on; before, the factory blamed the writer and spent a repair
   round that could not pass. The factory also still skips every `__init__.py`; isso keeps real
   code there. Mutating non-empty `__init__.py` files is the next fix, not done this session.
7. **The developers' own tests get the revert check too, as a report.** Verify runs it on the test
   files the change added or modified, for the tests new at head, and records the verdicts in
   `verify/developers_revert.json`; it never fails a run. `python -m factory devtests <run folder>`
   runs it on a finished run. Reason: it is the per-ticket answer to the team's question
   (`docs/trust.md`), measured on their own tests rather than argued.

## 2026-10-12 · Factory runs on the laptop bill the Console API key; cloud sessions build

**Decided, his words:** "Yeah, hey, let's keep going." He was answering the recommendation to run
the bundles ticket on Restate, billed to the Max plan's monthly API credits (200 USD) through a
Console API key, not to the subscription.

- **The factory's model calls are headless `claude -p` runs, so the API credits cover them.**
  Anthropic's Help Center (support.claude.com/en/articles/17154008) says: "API credits cover
  `claude -p` and the Claude Agent SDK when you run them yourself with an API key". The same page
  says the credits do not cover interactive Claude Code.
- **How:** `scripts/with-console-key.sh <command>` takes the key from this Mac's Keychain and adds
  the workspace header the key needs. With it, `claude auth status` reports `api_key` (measured).
  The Restate service runs the steps, so the service is started under the script.
- **Cloud sessions build; the laptop runs.** The one-time cloud-session credit (250 USD, until
  2026-11-05) pays for Claude Code cloud sessions, which build and test factory code. Real tickets
  run on the laptop, because they need the linkding worktrees and the run folders. It is also
  unverified whether a `claude -p` started inside a cloud VM authenticates and bills correctly.
- **The bundles ticket ran this way** (`docs/runs/2026-10-12-linkding-bundle-filters-blind-2/`,
  5.44 USD). Whether the Console shows that spend against the credits is for Oleg to confirm.

## 2026-10-12 · How the factory runs on Restate, by delegation

Made by the cloud session that built track 2's service, from what the stub runs showed
(`docs/exploration.md`, "Track 2, the build half"); each can be overturned by a later entry.

1. **Both engines share one step body.** `driver.run_step` reads and writes the step records; the
   plain driver loops over it, and the Restate workflow calls it inside each durable step. The run
   folder stays the record a person and the run report read; Restate's journal adds the resume
   inside one run. A side effect: `--until <step>` now also stops at a step that had already passed
   on an earlier run, where it used to run on past it.
2. **Inactivity and abort timeouts of 30 minutes each**, set on the workflow. The abort timeout is
   the hard limit on one step after the inactivity timeout fires (read from a 5 s + 5 s cut-off and
   the configuration, the edge not measured); 60 minutes in all covers a Verify with a repair round. A parked run holds a connection for up to 30 minutes before it suspends,
   which costs nothing that matters on one laptop.
3. **A lock per step in the run folder.** Restate retries a step it cut off while the old attempt
   still runs; the new attempt waits for the old one and then skips from its record. Without it, a
   step over the limit would run twice at once in one worktree.
4. **The workflow key is the ticket id**, and `--key` names another for a second run of a ticket
   (a key runs once). Answers go to `POST /factory/<key>/answer` with the answer file's JSON.
5. **The plain driver stays the default** until a real ticket has run on Restate (step 3 of track 2,
   on the laptop).

## 2026-10-10 · What the first blind runs changed in the checks, by delegation

Made by the session that ran track 1, from what the run on linkding 573b6f5 showed; each can be
overturned by a later entry.

1. **The revert check puts the test helpers back too.** The copy of the old code now gets the
   base version of every declared test-support file, not only of the changed source. The helpers
   are part of the code before the change; with the developers' new helpers, every test of that
   ticket failed on the old code while importing them, before any assertion. A test that needs a
   helper argument the change added is still reported, now as the missing name it is.
2. **The writer is blamed only for what it changed.** Files already changed before its session
   (the preparation's `npm install`) are neither held against it nor undone.
3. **A stronger-model call starts only with 1.50 USD or more left on the ticket.** With less, the
   step fails on the spend cap instead of asking a person.
4. **A third answer to the escalation question: recheck.** `{"decision": "recheck", "round": n}`
   runs the checks again on round n's tests with no writer call, for after a fix to the
   environment or to the factory. When the factory itself caused the stop, the session that fixed
   it may give this answer and records that it did; it never answers retry and never approves.

## 2026-10-10 · How Verify escalates, and what blind mode hides, by delegation

Made by the session that built them, under his decision of the same day ("stronger models before
people"); each can be overturned by a later entry.

1. **The order inside Verify.** A failure of lint, the revert check or mutation that the tests
   caused gets one repair round: a fresh writer session with the findings, then the checks again
   from lint. Anything still failing, and any failure the tests did not cause (the writer's own
   error, the application's suite, mutmut not running), goes to the stronger model
   (`claude-fable-5-1`, headless, read-only, its own budget of 3 USD per call). It answers
   `retry` (one guided writer round with its guidance), `change_is_wrong`, `environment` or
   `cannot_decide`. Its answer is kept as `verify/escalation-<k>.json` in the run folder.
2. **"Fail back to Implement" is a failure with the stronger model's diagnosis**, not a loop. In
   this path Implement is the developers' real commit; nothing can redo it. When the factory
   writes the change itself, this becomes the loop back.
3. **Only `cannot_decide` stops for a person.** The answer to that question is a file:
   `{"decision": "retry", "guidance": "..."}` runs one more guided round; any other decision fails
   the step with the person's note. A question can never approve failing work.
4. **The Review fix round runs inside the Review step.** On `request_changes`, the writer gets the
   findings for one round, Verify's checks and the test cases run again, and Review runs once
   more. The driver did not change.
5. **Caps per ticket, kept in `<run folder>/rounds.json`** so that a re-run does not reset them:
   3 extra writer rounds (repair, guided, review fix), 2 stronger-model calls, 15 USD of model
   spend in Verify and Review. A ticket or the application may set its own (`"caps"`). The spend
   cap is hard: every call's `--max-budget-usd` is what is left, and no call starts below
   0.50 USD. The two blind tickets of track 1 set 8 USD.
6. **Blind mode** (`"qa_mode": "blind"`): Frame, Plan and the first test writer run in the base
   worktree; their prompts carry no diff, none of the developers' tests and no `base`, `head` or
   `source` field of the ticket; their sessions are denied reading the application's clone, this
   ticket's head worktree, every other ticket's worktrees and the factory's own repository, and
   denied git. The writer's session is saved as a transcript and audited for any call that named
   a hidden path or ran git. After the join, a repair round runs in the head worktree with the
   findings but still no diff: the join is the point where QA meets the code, and the repair is
   the factory's normal escalation, not part of the blind measurement.
7. **A third mutation set, the developers' tests alone,** as the baseline for a ticket that has no
   sequential run to compare with. It costs mutmut time, not model spend.

## 2026-10-10 · The factory does not stop to ask when its checks pass; stronger models before people

**Decided, his words:** "Of course I approve the first run's test. Why do I have to approve this
kind of stupid question?" "We need the system to advise on stronger models, too. If the factory is
going to be stopping every turn to ask questions, how far is that going to go?"

- **Approval of passing work is automatic.** When every Verify check passes, Verify approves on its
  own and records `approval.json` (by: factory). A ticket or application may set `"gate": "person"`
  for a risk rule that wants a human. Built in this change (`factory/steps/verify.py`).
- **A stronger model before a person.** When a check fails or an agent is unsure, the step gets one
  capped fix round, then asks a stronger model for a decision; a person is asked only when that
  cannot resolve it. Not built yet; it is the first item of the next session.
- **The first run is approved.** It ran through Review and Ship on his answer.
- **Nothing at work runs a factory yet.** Working out how to run one is part of this project, so
  the orchestrator is ours to choose from running it. Track 2 is a real trial of running the
  factory on Restate. Temporal stays the deferred alternative; it is not compared unless he asks.
- **The lab is kept**, and salvaged piece by piece (`docs/reference/lab.md`, "Salvaged so far").
- **Track 3 runs linkding from its Docker image on this laptop.**

**Supersedes** item 8 of the delegated planning decisions (approving the test cases as a human gate
QA owns) and the person-as-default part of item 4. The approval on a pull request stays possible as
a configured gate. The open question "whether the factory at work is built on Temporal" is closed.

## 2026-10-10 · The exploration plan is approved

**Decided.** Oleg: "Yes, I want you to go with this plan." The three tracks of
`docs/exploration.md` run in order, one session each: (1) the feature loop measured with
acceptance tests written blind from the ticket, (2) the factory as a Restate workflow with its UI
plus a run report of our own, (3) a feature's readable cases run against linkding started from its
own Docker image on this laptop. Cap: about 25 USD of model spend in all (estimate). Each track
ends with a command that runs on linkding and a measured number, or is reported as not done.

**Read into it, overturnable.** Track 3's stand-in for the deployed environment (linkding's Docker
image on this laptop) is approved with the plan. Track 2 is a spike behind a flag; the plain
driver stays the default, because what the factory at work runs on is still unanswered.

**What it changes.** `docs/next-session.md` kicks off track 1. Restate is assessed by name, which
rule 2 allows; no other tool is scored.

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
