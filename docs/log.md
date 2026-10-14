# Log

What each session tried, newest first: what it set out to do, what worked, what failed and how
it was resolved, and what it left open. `docs/status.md` says what exists now and
`docs/decisions.md` what was decided; this file keeps the path that led there, so a later session
can walk Oleg through it. Numbers are measured unless marked otherwise.

Before 2026-10-08: the old lab, three days that produced no factory code
(`docs/reference/lab.md`), then the planning session that wrote the brief and the decisions.

## 2026-10-14 · The roadmap reviewed: person points, Restate, the research

**Asked.** Oleg (`docs/inputs.md`, second entry of 2026-10-14): review the roadmap; every point
where a person corrects or approves must be exposed; what Restate is and whether it is needed;
the research on software factories and AI SDLC practice he never saw, and the latest on it.

**Done.** No factory code, as asked (rule 4's exception). Three things:

- **The person points.** The brief's seven "when a person steps in" rows were set against the
  code: only Verify raises a gate (`factory/steps/verify.py`, two places: the stronger model
  cannot decide; `gate: person`). Frame lists ambiguities and goes on, Plan never stops and a plan
  cannot be edited and resumed, Review fails after its fix round, Ship commits locally. Nobody is
  notified, nothing lists waiting runs, an answer can approve or refuse but not correct. Written as
  a table in `docs/roadmap.md` and a diagram on its page; closed by a new item 4 in Now (one gate
  contract, a gate per step from the brief, correct as well as approve, per-step configuration,
  notification, listing, the answerer recorded), kickoff D in `docs/next-session.md`. Later items
  renumbered by one.
- **Restate.** Explained in one paragraph in `docs/roadmap.md` and on the page, with what track 2
  measured and its footprint (205 lines of service, 45 of stubs, 396 of tests, one dependency, a
  server and a service process). Recommendation unchanged: behind the flag until item 6; removal
  is his question 4.
- **The research.** It exists only in the old lab (`~/dev/assay/docs/research/`, five files,
  fetched 2026-10-06 to 08) and was never shown to him; `docs/reference/lab.md` had it in one row.
  A fresh pass was run with five web searches and eleven page fetches, no agents (rule 7):
  `docs/research/2026-10-14-factory-landscape.md`, six points, each claim labelled checked,
  documentation only, or not verified. The one finding that changes the roadmap: the published
  factories put the person at specification and merge, the two gates the factory lacks.

**Then, his third input of the day:** always portable to a generic application on another machine.
Filed, made rule 9 of `CLAUDE.md`, and a portability table added to `docs/roadmap.md` with what
is not yet true (no full run off this Mac; the key from the Keychain here).

**What failed.** The three links recorded as published pages (architecture, trust, roadmap) could
not be read from this session: the Artifact tool answered "not found" for the roadmap and the
architecture pages, and the account's list of 45 artifacts holds none of the three. The roadmap
page was republished at a new link (`docs/status.md`). Whether the earlier pages were published
from another account is for Oleg to say; the built files are in `docs/pages/` either way.

**Left open.** His four questions (`docs/status.md`). Nothing was run against an application.

## 2026-10-14 · The roadmap

**Asked.** Oleg (`docs/inputs.md`, 2026-10-14): discuss the roadmap and the next work items.

**Done.** A plan, no factory code, as asked. Written from the record only, no new research:
`docs/adopt.md` section 1 (what is not built), the leftovers in the old "Next" of
`docs/status.md`, the brief's steps that are not the factory's own yet, and his input of
2026-10-13, which sets the near-term order. `docs/roadmap.md` has nine items in three groups and
three questions for him; its page is https://claude.ai/artifact/TesENWMdg67e3p15kwiaZX (one local
render at desktop and phone width before publishing: the step diagram was clipped at desktop
width and was made to scale). `docs/next-session.md` now holds kickoffs for items 1 to 3 in
roadmap order; item 2 is written for a cloud session. The small leftovers of the first runs moved
into the roadmap. Restate stays behind its flag, by delegation (`docs/decisions.md`).

**Housekeeping.** The remote branches the status asked him to delete were already gone, and
`git push --delete` of the two newer ones answered "remote ref does not exist"; `git fetch
--prune` cleared the stale tracking refs. GitHub holds only `main`.

**Left open.** His three questions (`docs/status.md`). Nothing was run against an application.

## 2026-10-13 · Wrap up for adoption: the guide, isso onboarded from it by an agent, the trust answer

**Asked.** Oleg (`docs/inputs.md`, 2026-10-13): make sure the remote work is merged; wrap up so a
real project can adopt the factory, set up by agents, with tested instructions and clear
expectations; answer the team's question "how can we trust tests written in the session that
implemented the change"; file his thought on mocks and verification points; move fast.

**Ran, in order** (all measured):

1. *Merge state.* All 18 pull requests merged; the three remote branches left on GitHub are the
   squash-merged heads of 16, 17 and 18 (`git diff` against `main` shows nothing main lacks).
   Deleting them was refused by the session's permission rules; left for Oleg.
2. *The guide.* `docs/adopt.md` written for an agent on a fresh machine. Then `supervisor:implementer`
   made the browser test folder optional in a recipe (spec
   `docs/specs/2026-10-13-adoption/s1-browser-optional.md`, 10 new tests), because isso has no
   Python browser tests.
3. *isso from the guide alone.* An Opus agent that read nothing but `docs/adopt.md` and
   `targets/linkding/` onboarded isso: a setuptools project with a werkzeug API, tests inside the
   source package, no browser tests, no release tag newer than its 2026 commits. It chose upstream
   7e91d59 (no-cache headers on the comment routes), checked the contract on both commits with a
   probe through the test client, and wrote `targets/isso/`. Checklist steps 1 to 3 passed first
   time: `fetch.py` all `ok` twice; `run --until implement` passed (Frame and Plan 0.33 USD on the
   subscription; the guide had said "no model call", wrong).
   - **It reported 14 gaps in the guide**, then 9 more after the run; all folded into
     `docs/adopt.md`. The first was a blocker: the writer prompts hardcoded `helpers.py`, and isso
     has `fixtures.py`. Fixed with a `test_helpers` recipe field (1 test).
4. *The isso run, first attempt.* The blind writer (Opus, 249 s, 1.88 USD) wrote 6 API tests: all
   pass with the change; 4 fail on the old code on an assertion (`None != 'no-store'`); 2 pass on
   both, as the contract asked (unchanged bodies, other routes). Lint clean.
   - **What failed: the factory.** mutmut 3.8.0 generated 1039 mutants in `isso/views/comments.py`
     and none for the three changed functions (two decorated, one a decorator with an inner
     function); the function that sets the header lives in `isso/utils/__init__.py`, which the
     factory skips. Asked for mutants that did not exist, mutmut aborted ("Filtered for specific
     mutants, but nothing matches", exit 1); the factory read that as "the tests never reach the
     changed functions", marked it repairable, and started a repair round that could not pass.
   - The session killed the run during that round (the killed call's cost is not in
     `rounds.json`), fixed the check (`mutants.classify_exit`: "no mutants" is reported and the
     mutation verdict skipped, not repaired; 2 tests), raised the ticket's cap to 10 USD, and
     re-ran. A re-run after a failed Verify starts a fresh writer round (round 3).
5. *The isso run, second attempt: shipped.* Round 3's blind writer (Opus, 274 s, 2.12 USD) wrote
   6 API tests again: all pass with the change; 3 fail on the old code on an assertion; 3 pass on
   both as the contract asks (unchanged bodies, error responses and other routes without the
   header). Lint clean. Mutation recorded as not applicable (the three changed functions have no
   mutants). isso's suite green with the tests (128 passed). 6 readable cases (168 s, 1.10 USD),
   lint clean. Review approved (64 s, 0.27 USD). Ship committed `59a58be` on
   `qa/isso-no-cache-comment-views`. Verify 7 min 31 s; the ticket's recorded spend 5.69 USD
   (plus the killed round-2 call, unrecorded). Evidence in
   `docs/runs/2026-10-13-isso-no-cache-comment-views/`.
6. *The trust answer.* `docs/trust.md` and its page, from the four linkding runs' numbers: the
   developers' own tests on the sort feature fail on the old code only for a missing name (the
   measured case of "tests written with the code"), the mechanisms, the table of runs, the limits,
   and his scenarios (mocks then the deployed run as two verification points; criteria as
   verification points).

7. *The revert check on the developers' own tests* (pull request 20, after Oleg asked for one more
   thing worth showing). `factory/checks/devtests.py`: the two-tree revert run on the test files
   the change added or modified, for the tests new at head; an informational check in Verify
   after the revert check, and `python -m factory devtests <run folder>` for a finished run.
   Run on the three tickets with worktrees here, no model spend: 9 of 9 developers' tests
   (2 + 5 + 2) fail on the old code only for a missing name, each a constant the change adds
   (`SORT_MODIFIED_ASC`, `FILTER_STATE_YES`, `NO_CACHE_HEADERS`); 0 on an assertion. The
   factory's blind tests on the same tickets: 3, 7 and 3 on an assertion, 0 missing names.
   Two things found on the way: the pytest plugin writes its records relative to the tree, so
   the work folder must be absolute; the first run's Implement record names the worktree path
   from before worktrees moved per ticket, so the command resolves the trees from the recipe
   when the recorded path is gone. 4 tests. In `docs/trust.md` and on its page.

**Left open.** Track 3 (the deployed run) not started. Mutating non-empty `__init__.py` files.
The developers' tests check counts only tests new at head; tests the change modified in place are
not judged.

## 2026-10-12 · Track 2 on the laptop: the cloud branch merged, Restate installed, the bundles ticket run for real

**Asked.** Oleg: "let's keep going". That answered the recommendation to run the bundles ticket on
Restate, billed to the Console API key. The session ran from the konyklabs workspace, not from a
session started in this repository. It did step 0 onward of the laptop hand-back the cloud session
left in `docs/status.md`.

**Ran, in order** (all measured):

1. *The cloud branch (pull request 16).* Rescanned with the real guard term list: 0 hits in added
   lines, file names, commit messages and the PR text. `scripts/check.sh` gave 212 passed, 2
   skipped. Merged as `f79a8ca`.
2. *Restate on macOS.* `brew install restatedev/tap/restate-server restatedev/tap/restate`
   installed 1.7.13. The server runs on `~/Library/Caches/qa-factory/restate`, and all ports were
   free. `just check` now runs the live Restate test: 213 passed, 1 skipped.
3. *The stand-in proof, repeated.* `stub-laptop-1` ran end to end and was answered over HTTP.
   `stub-laptop-2` was killed with `kill -9` 4 s into Verify, and only Verify ran again.
   - **What failed first:** a plain `pkill` (SIGTERM) did not stop the service. The step finished,
     the process kept its port, and the restart failed with "Address already in use". Only
     `kill -9` works.
   - **Screenshots** of the UI were taken with Playwright's Chromium from linkding's environment,
     headless (`docs/runs/2026-10-12-restate-laptop/`).
4. *The key.* The Console API key went into the Keychain (`anthropic-console-key`).
   - **First attempt:** the entry was empty (0 characters read back), because the paste into
     `security add-generic-password -w` did not take. A `read -rs` followed by `-w "$K"` worked:
     106 characters.
   - **The check:** with the key, `claude auth status` reports `api_key`, and one `claude -p
     --model haiku` call billed 0.0003 USD. Claude Code warned that the API key takes precedence
     over the claude.ai login.
   - Now `scripts/with-console-key.sh`.
5. *The real ticket.* The service on 9080 was started under the key, then registered.
   `bundle-filters-blind-2` was prepared with `fetch.py --prepare-e2e` and submitted with
   `--engine restate`.
   - **Verify** passed every check in round 1 (16 min 7 s) and parked at the ticket's gate.
   - **The session answered the gate** under the 2026-10-10 decision; Oleg was not asked. The
     answer names the session.
   - **Review** approved with six low findings, and **Ship** committed `bf01f41`; linkding's suite
     passed.
   - **Totals:** 19 min 23 s and 5.44 USD (`docs/runs/2026-10-12-linkding-bundle-filters-blind-2/`).

**Then:**
- **The architecture page:** sections 12, 14 and 15 and the header were updated and republished as
  version 7. The live version was read first, and it matched a build of `main`.
- **Track 3:** its kickoff is in `docs/next-session.md`.

**Left open.** Whether the Console shows the 5.44 USD against the API credits; that is for Oleg to
check (`docs/status.md`, question 3).

## 2026-10-12 · Track 2, the build half, in a cloud session: the factory on Restate, and the run report

**Asked.** Steps 1, 2 and 4 of `docs/next-session.md` and the text of step 5, in a cloud session
(claude.ai/code, an Ubuntu 24.04 x86_64 VM, a fresh clone): install Restate, build the workflow
behind a flag, prove it with stub steps (end to end, kill mid-step, a gate answered over HTTP),
build the run report. The real ticket, the UI screenshots and the architecture page stay for the
laptop.

**The cloud differences, as measured here** (the next cloud session starts from these):

1. *No plugins.* None of Oleg's plugins is installed; the report was built by a general-purpose
   subagent from a written spec (`docs/specs/2026-10-12-restate-and-report/r1-report.md`).
2. *No `just`, no Homebrew.* `uv sync` then `scripts/check.sh` works. Tests that need the linkding
   clone skip (`test_lint.py`: "the linkding clone is absent"), as does the slow mutation test.
3. *No guard term list.* `hooks/guard.sh` prints "WARN: ... missing or empty, so the term scan was
   skipped" and passes; `core.hooksPath` is not even set in a fresh clone. So the pull request is
   opened and **not merged**: a laptop session rescans the branch with the real list and merges.
4. *No GraphQL for GitHub.* The pull request was opened with the session's GitHub tool, not `gh pr`.
5. *No model calls.* None was made: no `python -m factory run` on a real ticket, no `claude -p`.
   Model spend of the factory in this session: 0 USD.
6. *Network.* npm and PyPI reachable. The Restate server came from npm on the first try
   (`@restatedev/restate-server` 1.7.13, 8 s); the Docker client is installed but no Docker daemon
   runs (`failed to connect to the docker API at unix:///var/run/docker.sock`); the GitHub release
   binary answered HTTP 200 but was not needed. The VM has no IPv6: the server's first start failed
   binding `[::]:8080` ("Address family not supported by protocol") until `--bind-ip 127.0.0.1`.

**Ran, in order** (all numbers measured; commands and output in `docs/runs/2026-10-12-restate-stub/`):

1. *Install:* the npm packages for the server and CLI into `~/restate`; `uv add --dev restate-sdk
   hypercorn` (1.0.5 and 0.18.0; the SDK does not pull in an HTTP server).
2. *Build:* `driver.run_step` factored out of the driver's loop, unchanged in behaviour except
   `--until` (decisions, 2026-10-12); `factory/restate_service.py`, `factory/stub_steps.py`, the
   `--engine restate` flag and `python -m factory restate serve|register|answer`. In parallel, a
   subagent built `python -m factory report` from its spec; reviewed and accepted as delivered.
3. *First start of the service failed:* the SDK evaluates handler annotations at registration, so
   `restate` has to be imported at module level, not inside a function.
4. *End to end with a kill:* stub ticket, Verify 40 s, gate set. Killed the service 4 s into
   Verify; restarted it; only Verify ran again. Killed the Restate server while the run waited at
   the gate; its restart first failed on a Unix socket path too long for the scratch folder, then
   came up with `--listen-mode tcp` and the run was still waiting. Answered over HTTP; Review and
   Ship ran; result `pass`; a second answer got 409.
5. *Timeouts at seconds scale:* inactivity 5 s and abort 5 s cut a 25 s step off at 15 s, and
   Restate's retry ran a second Verify beside the first. Fixed with a lock per step and re-run: one
   Verify. The fix was first "re-run" twice on the old service, which had ignored SIGTERM and kept
   the port (the new one exited); `kill -9` and a check of the port fixed that. Inactivity 5 s and
   abort 60 s: the 25 s step finished on its first attempt, and the parked run showed `suspended`.
6. *Tests:* 11 with a fake Restate context (steps, gate and replay, a declined answer, a failing
   step, a step that raises, the answer handler, the lock, the timeouts, the command line), one
   against a real server (kill mid-step, gate, HTTP answer, 409; 9 s), 12 for the report, one for
   `--until`. The lock test was checked to fail without the lock. 212 factory tests.
7. *A mistake on the way:* `pkill -f 'factory restate serve'` matched the shell running it and
   killed that too; the service died as intended, the transcript of that command was lost, and the
   rest kills by process id.

**Not done.** Step 3 (a real ticket under Restate), the UI screenshots, the architecture page's
sections 12 and 14 and its republish: all need the laptop. The branch is
`claude/restate-driver-k4pqfg`, not `feat/<slug>`: the cloud session may push only to the branch
it was given.

## 2026-10-10 · Track 1: the feature loop measured, and what it found in the factory

**Asked.** Track 1 of `docs/exploration.md`: can QA start as soon as the ticket is ready? Tests
written blind, joined to the developers' commit, checked by the factory's existing checks.

**Ran, in order** (all numbers measured; the records are in `docs/runs/2026-10-10-*`):

1. *Two tickets.* `sort-by-modified-blind.json` (the first run's ticket, a new id, its provenance
   moved out of the description into `source`, which blind prompts never see) and
   `bundle-filters.json` / `bundle-filters-blind.json`, written from linkding 573b6f5 with its
   public contract stated: the two fields, their three values, the labels, the routes. Worktrees
   by `fetch.py --ticket <t> --prepare-e2e`.
2. *The sort ticket blind,* first `--until plan` (Frame 12 s 0.13 USD, Plan 15 s 0.17 USD, both
   in the base worktree), then to the end: the writer 304 s 3.62 USD, 4 tests, its 39 tool calls
   audited clean; 3 fail without the change on an assertion, 1 passes on both; 27 of 108 and 10 of
   10 mutants, the same as the run of 2026-10-08; suite green; Review approved, Ship `737c758`.
   902 s, 5.48 USD.
3. *The bundles ticket blind:* the writer 448 s 4.08 USD, 13 tests, all passing with the change,
   all counted "missing name" on the old code. Repair round (317 s, 3.17 USD): the writer found the
   cause, the developers' new `bookmarks/tests/helpers.py` uses `BookmarkBundle.FILTER_STATE_OFF`,
   and worked around it by copying the helpers into its files; it also created and removed a git
   worktree to test the old code; then the round was failed for `package-lock.json`, which the
   preparation's `npm install` had changed. Fable 5.1 got the 0.75 USD left under the 8 USD cap,
   stopped after 4 turns at 1.10 USD with no answer, and the run stopped for a person.
4. *The fix* (pull request 14, reviewed by a `supervisor:reviewer`, whose blocking finding was
   also fixed: a recheck could have taken a round the writer's own checks rejected): the four
   defects, and a `recheck` answer.
5. *The recheck:* a first attempt ran on the old branch with no answer file (the rebase was
   refused by an uncommitted file; nothing changed). Then the session answered `recheck` for round
   1, saying Oleg was not asked; round 3 judged the unchanged round-1 tests: 12 fail without the
   change on an assertion, 1 passes on both, no missing name, no crash; 16 of 16 mutants on the
   changed lines, 64 of 82 in `_filter_bundle` (the developers' tests 77 of 82); suite green. The
   step then stopped at the 8 USD cap before the readable cases, as designed. 312 s, no spend.

**Found along the way.** `--max-budget-usd` is checked between turns, so a call overshoots by up
to one turn (0.75 asked, 1.10 spent). The raw stream-json transcript of a headless session holds
this machine's hook output, so only the tool calls are copied into `docs/runs/`. The summary had
counted only the last Verify record's spend; it now reads the ticket's `rounds.json`.

**Not done.** The sequential run of the bundles ticket (the cap). The bundles ticket's readable
cases, Review and Ship (its cap; question 2 in `docs/status.md`).

## 2026-10-10 · Stronger models before people, and blind mode, built

**Asked.** `docs/next-session.md`: first the fix round and the stronger model's advice in Verify,
then track 1 (blind mode, two tickets, the numbers).

**Built** (specs in `docs/specs/2026-10-10-escalation-and-blind/`, decisions in
`docs/decisions.md`): the repair round, the stronger model's four decisions, the Review fix round
and per-ticket caps (`factory/rounds.py`, `factory/escalate.py`, `factory/steps/verify.py`,
`factory/steps/review.py`); blind mode (`factory/blind.py`, `factory/headless.py`); a run summary
(`python -m factory summary <run folder>...`, `factory/summary.py`). 172 factory tests.

**How.** The supervisor plugin is still dormant, so its agents were spawned directly from the
specs, in one workflow: three `supervisor:implementer` builders in parallel (caps and the
stronger model, blind plumbing, the summary), then `supervisor:senior-implementer` for the Verify
and Review loop, then one `supervisor:reviewer` per slice.

**Measured before building** (Claude Code 2.1.296): a deny rule needs the absolute form
`Read(//abs/path/**)` (a single slash is read relative to the settings file and denied nothing);
with it, a headless session's Read of a hidden folder and its `git log` are both denied, while
linkding's interpreter, which lives inside the hidden clone, still runs pytest and ruff. A cold
headless Fable 5.1 call with a schema cost 0.61 USD.

**The reviewers found four real defects, fixed with tests:** Review's spend record was
overwritten by a stale copy after the fix round (two ledgers on one file); a re-run of Review
after a failed or stopped fix round would have reviewed, and passed to Ship, tests whose checks
had not passed (Verify's report now records how it ended, and Review refuses anything but a pass);
old test cases stayed beside a fix round's new ones; the blindness audit flagged every run
because the writer must run linkding's interpreter from inside the hidden clone.

## 2026-10-10 · His answers: the first ticket ships, and the factory stops asking

**Asked.** He approved the first run and objected to being asked: approving passing work is not
his job, the factory should ask stronger models before people, nothing at work runs a factory yet
(learning to run one is the point), keep and salvage the lab, and of course Docker on this laptop.

**Done.**
- The first run resumed on his answer: Verify passed on it, Review approved (three low findings,
  51 s, 0.47 USD), Ship committed `d1c4de7` on `qa/linkding-sort-by-modified` and ran linkding's
  suite green (1294 passed, 2 browser passed, 32 s). The first time Review and Ship ran as steps.
- Verify now approves on its own when every check passes (`approval.json`, by: factory); a ticket
  may set `"gate": "person"`. Two tests. 102 factory tests.
- Decisions recorded; `CLAUDE.md` says never to ask him to approve passing work or confirm an
  obvious default; `docs/reference/lab.md` lists what the factory has taken from the lab and what
  is next to take.
- `docs/next-session.md` now starts with the fix round and the stronger model's advice, then
  track 1.

**Not done.** The fix round and the stronger-model advice are specified, not built.

## 2026-10-10 · The exploration plan approved and persisted

**Asked.** Go with the plan, persisted, so the context can be cleared before the kickoff.

**Done.** The approval recorded (`docs/decisions.md`), `docs/exploration.md` marked approved with
notes for whoever runs the tracks (blind mode has to keep Frame and Plan in the base worktree too;
the first run stays parked under its own ticket id), `docs/next-session.md` rewritten as the
kickoff of track 1, status and the architecture page updated.

**Not done.** Track 1 has not started; it starts in a fresh session.

## 2026-10-10 · Use cases, a scan of published practice, Restate, the exploration plan

**Asked.** A UI to observe the factory; how useful Restate is; how to organize QA for a small
feature (same session or in parallel); what reputable companies publish and what is ready-made;
whether an exploration period sounds like a plan (`docs/inputs.md`).

**Done.** His three use cases placed on the architecture page and in `docs/architecture.md`. A
short scan, each claim labelled: Anthropic's Claude Code best practices and Restate's docs were
read; Meta's two test-generation papers, Google's mutation testing paper, Spotify's agent
verification post and OpenAI's harness engineering post were seen through search summaries only
(OpenAI's page refused the fetch); Playwright's test agents docs were read. Findings: Restate is a
single local binary with a bundled UI, human waits as promises, BSL 1.1, and default timeouts
(1 minute inactivity, 10 minutes abort) that a 7-minute step needs raised; it shows execution, not
QA evidence. Playwright's test agents are TypeScript only. Published practice supports tests and
code in separate sessions and mutation on changed code. linkding's browser tests cannot run
against a deployed URL as written, because they seed data through the ORM. The plan, three capped
tracks, is in `docs/exploration.md` and on the page.

**Not done.** No Restate code ran; no experiment ran. Both wait for his yes.

## 2026-10-10 · The architecture page

**Asked.** Visuals and a page to take in the current architecture and setup, then discuss the use
cases he has in mind and how to support them at scale (`docs/inputs.md`).

**Done.** A published page with four diagrams (the flow, inside Verify, the revert check, where
everything lives), two charts of the first run (time per stage, spend per call), a stop-and-resume
table, the extension points A to H and the "where it is fixed today" table, built by
`docs/pages/architecture/build.py`. One look in headless Chromium (Playwright 1.62.0, light,
dark and phone width) found two crowded labels and charts too small side by side; fixed once,
then published. The two tables are kept as text in `docs/architecture.md`.

**Not done.** No use case is on the page yet; they are his to name.

## 2026-10-10 · Persisting the state

**Asked.** Make sure the current state is persisted, so a session can sit with Oleg and explain
what was tried, what exists, and what to decide next (`docs/inputs.md`).

**Found.** The code, the decisions and the run's evidence were in the repository. Missing: this
log, the specs the modules were built from (only in a scratch folder, lost when the session
ends), the run's full records (only in the gitignored run folder), and the inputs of 2026-10-08.
One real hazard: the parked run shared linkding's worktrees with every other ticket, and the
next-session prompt told the next session to run a second ticket, which would have moved the
head worktree to another commit and deleted the first run's generated tests.

**Done.**
- Pull request 7: one worktree pair per ticket; the first run's worktrees moved with
  `git worktree move`; Review and Ship restore generated tests from the run folder if the
  worktree lost them. Checked without a model call: the run resumes to the same gate (three
  steps skipped, the Verify question, exit 2).
- This log; the specs under `docs/specs/2026-10-08-first-path/`; the run's records under
  `docs/runs/2026-10-08-linkding-sort-by-modified/records/`; a line in `CLAUDE.md` that every
  session leaves this record.

**Still only on this machine.** The run folder `.artifacts/runs/linkding-sort-by-modified/`
(gitignored; `git clean -fdx` deletes it) is what a resume needs; if it is lost, the run starts
over at about 5 USD and 13 minutes (estimated from the first run). The linkding clone, its
environment and the worktrees under `~/Library/Caches/qa-factory/linkding/` are rebuilt by
`targets/linkding/fetch.py`.

## 2026-10-08 · The first build session: the first path, run on linkding

**Asked.** `docs/next-session.md` of that day: build the first end-to-end path on a plain Python
driver and run it on one real linkding feature, Verify built fully, the rest simple.

**Built.** The driver and the six steps, the four checks of Verify, the headless Claude Code
runner, linkding's fetch script, run recipe, strategy rule and first ticket; 99 tests of the
factory's own. Pull request 6. What each piece does is in `docs/status.md`.

**Tried, in order.**

1. *The application copy.* The lab's cached linkding clone served as a local mirror for the
   factory's own clone at `~/Library/Caches/qa-factory/linkding/`, on release 1.47.0, with a uv
   environment: Python 3.13.15, Django 6.0.7, pytest 9.0.3, Playwright 1.62.0, mutmut 3.8.0.
2. *The feature.* From the lab's eleven 2026 server features, "Add sort by modification date
   option" (upstream pull request 1363, commit 0490013): small, visible both in the REST API and
   in the browser, and the developers' own tests fail on the old code only because a name is
   missing (the lab measured this), so tests the factory writes have to do better than that.
3. *mutmut on linkding, before any code.* It failed twice.
   - "could not find any test case for any mutant": pytest-django's project discovery put the
     original source ahead of mutmut's mutated copy on the import path. Fixed with
     `-o django_find_project=false`.
   - "unable to open database file": linkding's task queue keeps its database under `data/`
     relative to the code, which does not exist in mutmut's copy. Fixed by creating
     `mutants/data/assets`, `favicons` and `previews` before the run.
   - Third run, the changed function with the developers' tests: 454 mutants generated, 108
     checked, 98 killed, 10 survived, 115 s.
4. *Browser tests, before any code.* `npm install`, `npm run build`, `collectstatic`,
   `playwright install chromium`; one existing linkding browser test file: 16 passed in 11.8 s.
5. *Building with the plugins.* `/supervisor:triage` was refused: the plugin is dormant until
   Oleg arms it, and an unattended session cannot. The session wrote one spec per piece
   (`docs/specs/2026-10-08-first-path/`) and spawned the plugin's builder agents directly, four in
   parallel, then one of its reviewer agents per piece (`docs/plugin-notes.md`).
6. *A builder stopped instead of guessing.* The mutation spec contradicted itself on where a
   mutant's line offset counts from. The builder asked; the answer was "from the `def` line".
7. *The failure sorter, twice wrong for linkding.*
   - The lab's rule needed the failing assertion's innermost frame to be in the test file. Every
     Playwright `expect` failure and every failure inside linkding's own test helpers would have
     counted as a crash. The rule became: an AssertionError, and the test file or a declared
     test-support file anywhere in the traceback.
   - pytest reports a unittest-style failure before it hands over the exception, so linkding's
     `self.assertEqual` failures arrived with no traceback and would also have counted as
     crashes. Fixed in the plugin, with a test.
8. *Headless calls.* A 0.05 USD cap failed on the first call: a cold call costs about 0.10 USD
   because the system prompt is written to the cache. Caps start at 0.50. A suspected refusal of
   headless calls from inside a Claude Code session did not reproduce.
9. *Four reviews, three blocking defects, all fixed before the run.* An answer file was never
   used up, so one approval would have approved every later gate. Run paths were relative, so
   the test-case writer, which runs inside linkding's worktree, would have written the cases into
   linkding. Mutants of class methods were never mapped to source lines, so the "kills nothing on
   the changed lines" gate could not fire for a change made only in methods. Minor ones: lint
   passed silently when ruff was missing; the headless runner crashed on a missing binary; cost
   records could name a helper model instead of the one asked for.
10. *The plan wanted to edit an existing test file.* The Plan step put its tests into linkding's
    existing `test_bookmarks_api.py`; the test writer may only add new files. Both prompts now
    say the placement rule wins.
11. *Frame and Plan run before the change exists*, so their prompt had no diff and they read the
    code instead. Right for a real ticket; the prompt still mentions a diff.

**The run.** Frame, Plan, Implement, then Verify in 800 s for 4.90 USD: Opus wrote four API tests
and two browser tests in 414 s for 3.62 USD; five of the six fail on the old code because the
order is wrong, and one (an unknown sort value still falls back to the default) passes on both,
reported as a regression guard; mutmut: the generated API tests kill 27 of 108 mutants of the
changed function and all 10 on the changed lines, 98 of 108 together with the developers' tests;
linkding's suite green (1294 tests, and 83 browser tests with 1 skipped); six readable cases,
lint clean. The run stopped at the gate. Review, run by hand on the same files, approved with two
low findings: random titles in the API fixture, and the fallback test proves no new behaviour.

**Not done.** Review and Ship have not run as driver steps on linkding; they wait behind the gate.
The answer is a file, not a pull request, because linkding is not forked under Oleg's account.
The build session's own model spend was not measured.

**Left open for Oleg.** The gate (approve, or decline at the cost of a fresh Verify, about 5 USD
and 13 minutes); whether review findings should go back to the test writer within a round before
he is asked; the second ticket.
