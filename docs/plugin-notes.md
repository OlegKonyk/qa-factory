# Plugin notes

What factory sessions learned about Oleg's Claude Code plugins (`~/dev/konyklabs/claude-plugins`),
for him to carry into that project. Newest first. One entry per observation: the plugin, what was
missing or wrong, what would have helped, and the run that showed it.

## 2026-10-14 · supervisor and py-testing agents driven by a Workflow script, six slices in parallel

**Plugins:** supervisor (`senior-implementer`, `reviewer`), py-testing (`test-implementer`).
**Run:** the "Now" items of the roadmap (`docs/log.md`, 2026-10-14, second entry).

- The agents were spawned by a Workflow script (`agentType`), not through the supervisor's
  skills, because Oleg asked for workflows. Three branches ran in parallel, each slice as
  implementer, then reviewer, with a fix pass when the reviewer said "fix". All eight slices came
  back "accept" on the first review; no fix pass fired. The supervisor's hook stayed dormant, so
  nothing priced the run: the Workflow tool's own count (about 767k subagent tokens for twelve
  agents on the first run) is the only number.
- **What would have helped:** a reviewer output field for *spec gaps* and an *evidence check* (does
  the report paste what the spec asked, is any claim contradicted by the diff). Both were added in
  the script's schema and caught real things: a report that summarised test output instead of
  pasting it, a stage name set in a different function than the report said. Worth making part of
  `supervisor:reviewer`'s contract.
- `py-testing:test-implementer` ran with `model: opus` over its Sonnet default and the Playwright
  skills preloaded; it found a markup defect in linkding (a label pointing at a hidden input) and
  recorded it. The override works; the agent's description could say so.
- The implementers' reports followed the contract (files, commands with output, deviations, left
  alone) without being told twice. One ran an 11-minute mutation command in the foreground; a
  line in the contract about backgrounding long commands would save wall time.
- Two slices in different worktrees edited `docs/adopt.md` and `factory/steps/verify.py`; the
  spec's "hands off" list kept the rebase clean. A decomposition skill that emits that list per
  slice from the file ownership would make this routine.

## 2026-10-13 · supervisor: an implementer slice and a guide-following agent, both from written specs

**Plugin:** supervisor. **Run:** the adoption session (`docs/log.md`, 2026-10-13).

Still dormant, so `supervisor:implementer` was spawned directly with a spec
(`docs/specs/2026-10-13-adoption/s1-browser-optional.md`). It delivered in one pass, reported two
stale comments it had not been asked to fix and two places it left alone with reasons; that
report shape (deviations, things left alone) is worth making the default. The second agent of
the session was not a plugin agent: an Opus session told to follow `docs/adopt.md` and nothing
else, and to list every place the guide was wrong. That "follow the document blind and report
the gaps" job is a reusable shape for any procedure meant for agents; a skill that spawns it with
the document path and the report format would have saved writing the brief.

## 2026-10-12 · All plugins: not available in a cloud session

Cloud sessions (claude.ai/code) do not load Oleg's plugins, so the Restate build of track 2 used a
general-purpose subagent with a written spec (`docs/specs/2026-10-12-restate-and-report/`) instead
of `supervisor`, and no `py-testing` or `reviewing-diffs` skills.

## 2026-10-10 · supervisor: the builders and reviewers in one workflow, reviewers given the builders' reports

**Plugin:** supervisor. **Run:** the escalation and blind-mode build (pull request 13).

Still dormant, so its agents were spawned directly, this time from one Claude Code workflow script:
three `supervisor:implementer` builders in parallel on disjoint files, then
`supervisor:senior-implementer` on the slice that depended on them, then one `supervisor:reviewer`
per slice. Each reviewer's prompt carried the builder's structured report (files, pasted
evidence, deviations), which closes the gap noted on 2026-10-08. The four reviewers' blocking
findings were all real (a stale spend record, a Review re-run that could pass failing tests to
Ship, stale test cases, an audit that flagged every run). Two things worth carrying over:

- Parallel builders in one working tree see each other's half-finished files: two builders
  reported whole-suite failures that belonged to the third. The spec said "paste it and do not fix
  it", which worked; a delegate skill could say the same by default.
- The senior implementer listed nine deviations from the spec, each with its reason, and three
  gaps it saw outside the spec. Two of those gaps were the reviewer's blocking findings. A report
  field for "gaps outside the spec" is worth making standard.

## 2026-10-08 · py-testing: the skills do not fit a suite that must join an application's own tests

**Plugin:** py-testing (`testing-playwright-api`, `testing-playwright-browser`). **Run:** the first
run on linkding.

The skills teach pytest-playwright fixtures (`page`, `context`), `APIRequestContext`, page
objects and storage-state reuse. linkding's tests are unittest-style Django classes:
`LinkdingApiTestCase` for the API and a `LiveServerTestCase` subclass that owns its own Playwright
browser for the browser tests. A test written the skills' way would not run under the
application's configuration, so the writer's prompt does not carry the skills; it points at the
application's helpers and says its conventions win. What would help: a short section in each
skill on "joining an existing suite" (detect the house style first; when the suite is
unittest-based, use its base classes and only take the locator and web-first assertion practice
from here), and a skill or checklist for writing tests from a feature description against an
unfamiliar application.

## 2026-10-08 · supervisor: the implementer and reviewer agents worked well spawned directly

**Plugin:** supervisor. **Run:** the first-path build session.

Four slices went to `supervisor:implementer` (three) and `supervisor:senior-implementer` (one)
from written specs; all four returned with the evidence pasted. One stopped on a real spec
contradiction instead of guessing, as its contract says. Four `supervisor:reviewer` passes found
three blocking defects (a stale answer file answering later gates, relative run paths, mutants of
methods never mapped to lines) and several minor ones; every blocking one was real. The
reviewers noted they received no implementer evidence: the conductor passed the spec, not the
implementer's report. A delegate skill that hands the reviewer the implementer's report alongside
the spec would close that gap.

## 2026-10-08 · supervisor: a session cannot arm it, so an unattended build cannot use its skills

**Plugin:** supervisor. **Run:** the first-path build session (branch `feat/first-path`).

`/supervisor:triage` was refused by the plugin's own hook: "supervisor is dormant; its skills run
only after the user arms it with /supervisor:start <task> or /supervisor:on. Ask, do not arm it
yourself." In an unattended session nobody is there to arm it, so the triage and delegate skills
were unavailable. The session kept the substance of the toolchain by spawning the plugin's agents
directly (`supervisor:implementer`, `supervisor:senior-implementer`, `supervisor:reviewer`) with
written specs and an evidence contract; while dormant the hook neither pins nor denies those
spawns. What would have helped: a way for a project to arm the supervisor from its settings or
`CLAUDE.md` (an "armed by default in this repository" switch), or a documented headless mode.

## 2026-10-08 · signoff: the case linter was copied into the factory

**Plugin:** signoff, skill `recording-test-cases`. **Run:** the first-path build session.

The factory needs the test-case skeleton check inside the Verify step, headless, after a model
writes the cases. The skill's `cases.py` is standard-library and self-contained, so it was copied
unchanged to `factory/checks/cases.py` and run as a subprocess. Nothing was missing; the copy is
noted here so the plugin's version stays the source of truth and a later change there can be
carried over.

