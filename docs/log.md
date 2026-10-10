# Log

What each session tried, newest first: what it set out to do, what worked, what failed and how
it was resolved, and what it left open. `docs/status.md` says what exists now and
`docs/decisions.md` what was decided; this file keeps the path that led there, so a later session
can walk Oleg through it. Numbers are measured unless marked otherwise.

Before 2026-10-08: the old lab, three days that produced no factory code
(`docs/reference/lab.md`), then the planning session that wrote the brief and the decisions.

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
