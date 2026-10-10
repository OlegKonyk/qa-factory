# Exploration: observing the factory, Restate, the feature loop, the deployed environment

Proposed 2026-10-10 in answer to Oleg's input of that day (`docs/inputs.md`). **Approved the same
day** (`docs/decisions.md`): the three tracks run in order, track 1 first. The review surface is
section 10 onward of https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa.

| Track | State |
|---|---|
| 1 · The loop, measured | done 2026-10-10: results below |
| 2 · Watch it run | next: `docs/next-session.md` |
| 3 · The deployed environment | after track 2 |

## Track 1 results, 2026-10-10

**The question.** Can QA start as soon as the ticket is ready, in parallel with the
implementation? **The answer from two tickets: yes, when the ticket states the public contract.**
Tests written blind, from the ticket and the code before the change only, met the developers'
real change with no contract mismatch on either ticket: every test passed with the change. On
the sort ticket they were exactly as strong as tests written after the change; on the bundles
ticket they killed every mutant on the changed lines. What went wrong was the factory's own
checks, not the blind tests (below). All numbers are measured, from one run each; nothing is
averaged. The commands and records are in `docs/runs/2026-10-10-*` and the side-by-side table in
`docs/runs/2026-10-10-track-1-comparison.md` (`python -m factory summary <run folders>`).

**The sort ticket** (linkding 0490013), the same ticket and models as the run of 2026-10-08:

| | Written after the change (8 Oct) | Written blind (10 Oct) |
|---|---|---|
| Tests written | 6: 4 API, 2 browser | 4: 3 API, 1 browser |
| Pass with the change | 6 | 4 |
| Fail without it, on an assertion | 5 | 3 |
| Pass on both (the unknown-sort fallback, a regression guard) | 1 | 1 |
| Fail without it for a missing name, or crash | 0, 0 | 0, 0 |
| Mutants killed on the changed lines | 10 of 10 | 10 of 10 |
| Mutants killed in the whole function | 27 of 108 | 27 of 108 |
| The developers' own tests, same function | 98 of 108 (with the generated) | 98 of 108 alone, 10 of 10 changed lines |
| Test writer | 414 s, 3.62 USD, 39 turns | 304 s, 3.62 USD, 40 turns |
| Verify | 800 s, 4.90 USD | 818 s, 4.63 USD (140 s of it the new developers-only mutation run) |
| Model spend, whole ticket | 5.47 USD | 5.48 USD |
| Repair rounds, stronger-model calls | none | none |
| Shipped | `d1c4de7` | `737c758` on `qa/linkding-sort-by-modified-blind`, suite green |

The blind writer's session was audited: 39 tool calls, none touching the hidden code or git.

**The bundles ticket** (linkding 573b6f5, "Filter bundles by reading or sharing state"), blind only:

| | Written blind |
|---|---|
| Tests written | 13: 9 through the REST API and the bookmark list, 2 through the bundle form, 2 browser |
| Pass with the change | 13 |
| Fail without it, on an assertion | 12 (after the revert-check fix; see below) |
| Pass on both (a bundle with no state set matches everything, a regression guard) | 1 |
| Fail without it for a missing name, or crash | 0, 0 |
| Mutants killed on the changed lines of `_filter_bundle` | 16 of 16 (the developers' tests: 16 of 16) |
| Mutants killed in the whole function | 64 of 82 (the developers' tests: 77 of 82) |
| Test writer | 448 s, 4.08 USD, 25 turns; audit: 24 tool calls, none touching the hidden code or git |
| What the escalation spent | a repair round, 317 s and 3.17 USD; one Fable 5.1 call, 1.10 USD |
| Recheck of the same tests after the fix | 312 s, no model spend |
| Model spend, whole ticket | 8.47 USD |
| Shipped | no: the factory stopped at the ticket's 8 USD cap before writing the readable cases |

**What went wrong, all in the factory, all fixed (pull request 14):**

1. The revert check judged the blind tests on the old code with the developers' *new* test helper
   file, which uses a name the change adds. All 13 tests failed while importing it and were counted
   as "missing name". The repair writer found the cause and worked around it by copying the helpers
   into its own files. The check now puts the test helpers back to their old version too; the same
   round-1 tests, judged again with no writer call, gave the 12 and 1 above.
2. The repair round was then failed for "touching application code": `package-lock.json`, which
   the preparation's `npm install` had changed before any writer ran. Now only the writer's own
   changes count.
3. Fable 5.1 got the 0.75 USD left under the cap, ran out after 4 turns and gave no answer, which
   counted as "cannot decide" and stopped the run for a person. A call now needs 1.50 USD left.
4. The repair writer created a git worktree in the shared clone to test the old code. It may not
   any more.

**Limits of this answer.** Two tickets, one run each. Both tickets stated the public contract
(parameter values, field names, labels) because they were written from the finished commits; a
ticket written before the code may not, and then Plan has to fix the contract or the blind lane
will hit mismatches. The blind writer worked in the same session order as before (Verify after
Implement); blind means it saw nothing of the change, not that it ran at the same time. The
sequential run of the bundles ticket was not done: track 1's cap was about 10 USD and the two
blind runs spent 13.96 (4.27 of it the escalation running live).

## The answer to "does this sound like a plan"

Yes, on one condition. The old lab died doing exactly "explore for a while"
(`docs/reference/lab.md`). So each track ends with a command that runs on linkding and a measured
number, inside a cap. A track that cannot show that is reported as not done, and no tool is scored
beyond Restate, which he named.

## The tracks

| Track | Use case | Work | Produces | Cap |
|---|---|---|---|---|
| 1 · The loop, measured | UC3 | Acceptance tests written blind, from the ticket and the base code only, joined to the developers' commit; revert check and mutmut on them; the sort ticket and "Filter bundles by reading or sharing state" (573b6f5) | A blind mode in Verify, and its numbers beside the sequential run | One session, about 10 USD (estimate) |
| 2 · Watch it run | UC1 | The six steps as one Restate workflow per ticket, a person-gate (when one is configured) as a promise, the UI at `localhost:9070`; a real trial of running the factory on Restate, with the plain driver kept until it proves out; a run report from the run folder for the QA evidence | A run he can watch; the timeouts and resume-after-kill, measured | One session |
| 3 · The deployed environment | UC2 | linkding from its own Docker image on this laptop as the deployed app; a feature's readable cases as a thin suite with a base URL and data through the REST API, run against the container | The same cases passing on a deployed app; the checklist below, tested | One session |

Recommended order: track 1 first. It answers the question everyone asks with a number. In all,
about 25 USD of model spend (estimate), then a decision page. Ready-made pieces enter by use:
Playwright's test agents when a TypeScript repository appears, Playwright MCP inside track 3 if
the writer needs a live browser.

## The feature loop, recommended shape

Not the same session. Once Frame and Plan have fixed the criteria and the public contract
(parameter names, labels, routes), two fresh sessions run in parallel: one writes the change and
its unit tests test-first, the other writes the acceptance tests from the criteria without seeing
the code. They join on the deterministic checks; failures go back to Implement, capped. A coverage
pass then writes tests for the mutants that survive on the changed lines. Regression is the app's
suite with the new tests. After the approval and the merge, the same cases run against the
deployed environment.

Why: tests written with the code share its blind spots. In the first run, the developers' tests
for the sort feature, written with the code, fail on the old code only because a name is missing;
the factory's tests, written after it from the ticket, fail because the order is wrong. Risk of
the blind lane: a contract mismatch (a test using a parameter value the code did not choose).
Plan fixing the contract first is the guard; track 1 measures how often it still happens.

## What makes a repository agent-friendly for this loop

Drawn from the sources below and from what the first run needed; item 5 is the one linkding fails.

1. One documented command to build and start the app with seeded data, in the repository's agent file.
2. Test helpers named in a strategy rule, so the factory and its checks know them.
3. A strategy rule: which kind of test goes to which level.
4. Selectors by role and label first, test ids where roles are not enough.
5. Test data created through the public API, not the database, for every test that must also run
   against a deployed environment. linkding's browser tests create data through the ORM inside a
   `LiveServerTestCase`, so they cannot run against a deployed URL as written.
6. A base URL, test accounts and cleanup for each environment.
7. Lint, the suite and mutation on changed code runnable locally in minutes.
8. Logs an agent can read when a test fails.

## Restate, from its documentation (no Restate code has run here)

Read on 2026-10-10: the repository README and LICENSE (github.com/restatedev/restate), and
docs.restate.dev pages on installation, service configuration, durable steps (Python), awakeables
(Python) and introspection.

- **Install and run:** "a single self-contained binary"; `brew install restatedev/tap/restate-server`;
  the UI is bundled at `http://localhost:9070`.
- **SDKs:** TypeScript, Java and Kotlin, Python, Go, Rust.
- **Human waits:** a handler creates an awakeable (`ctx.awakeable(type_hint=str)`) and suspends on
  it; an HTTP call to `/restate/awakeables/<id>/resolve` resumes it. Workflows also have durable
  promises, resolvable once.
- **Status:** the CLI and SQL views show pending, ready, running, backing-off, suspended (waiting on
  external input) or completed. What the UI shows exactly was not read; the spike sees it.
- **Long steps:** inactivity timeout 1 minute (then Restate asks the handler to suspend), abort
  timeout 10 minutes after that, both by default; settable per service or handler in Python
  (`inactivity_timeout`, `abort_timeout`). How a `ctx.run` already in progress reacts is not
  documented. Our Verify ran 800 s, so the defaults would not fit it as one step.
- **Retention:** journals kept 24 hours after completion by default (`journal_retention`).
- **Crash recovery:** replay from the journal; results of finished durable steps are stored and not
  recomputed.
- **License:** Business Source License 1.1; production use allowed except a "Public Restate
  Platform Service"; each release changes to Apache 2.0 four years after it ships.
- **What it does not give:** a view of the QA evidence (tests, cases, verdicts, mutants). A run
  report of our own is still needed.

Verdict: useful for watching runs and for waits that last days; the same kind of piece as
Temporal, which is deferred (`docs/decisions.md`). Nothing at work runs a factory yet, so the
choice is ours, made from running track 2.

## Sources, one claim each

Labels: **read** (primary page read on 2026-10-10), **docs** (product documentation read),
**summary** (only search summaries seen; primary page not opened or refused the request).

| Source | Claim | Label |
|---|---|---|
| Anthropic, Claude Code best practices, https://code.claude.com/docs/en/best-practices | "Have one Claude write tests, then another write code to pass them"; "A fresh context improves code review since Claude won't be biased toward code it just wrote"; give the agent a check it can run, and a second agent to refute the result | read |
| Meta, TestGen-LLM, FSE 2024, https://arxiv.org/abs/2402.09171 | Generated tests kept only if they build, pass repeatedly and add coverage; 73% of recommendations accepted | summary |
| Meta, ACH, FSE 2025, https://arxiv.org/abs/2501.12862 | Few mutants specific to a concern, then tests that kill them; 73% of tests accepted | summary |
| Google, Practical Mutation Testing at Scale, https://arxiv.org/abs/2102.11378 | Mutants on changed code only, shown in code review; useful share rose from 15% to 89%; mutation adequacy is not a goal | summary |
| Spotify, background coding agents part 3, https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3 | Deterministic verifiers plus an LLM judge that vetoes out-of-scope changes; worst failure is a change that passes CI and is wrong | summary |
| OpenAI, harness engineering, https://openai.com/index/harness-engineering/ | All code written by Codex; human QA capacity became the bottleneck; the application was made readable to agents | summary (the page refused the fetch) |
| Microsoft, Playwright test agents, https://playwright.dev/docs/test-agents | Planner, generator, healer (may skip a test it judges broken); `npx playwright init-agents --loop=claude`; TypeScript runner | docs |
| Playwright issue 38610, https://github.com/microsoft/playwright/issues/38610 | Python support for the test agents is an open feature request | summary |

## Questions for Oleg

1. ~~Yes, no, or reorder the three tracks.~~ Yes, as written (2026-10-10).
2. ~~What the factory at work runs on.~~ Nothing yet; working out how to run a factory is part
   of this project (2026-10-10). Track 2 is a real trial of running the factory on Restate.
3. ~~Whether linkding's own Docker image may stand for the deployed environment.~~ Approved with
   the plan (2026-10-10).

## Notes for whoever runs the tracks

Track 1, things the first run's code makes easy to get wrong:

- **Blind means blind in every step before the join.** Frame and Plan run with the head worktree
  as their working directory today (`factory/headless.py`, `one_prompt`), so they can read the
  implementation. In blind mode Frame, Plan and the test writer must run in the base worktree, and
  the writer's prompt must carry no source diff and none of the developers' tests.
- **The writer cannot see its tests pass.** At the base commit the feature does not exist; its
  tests should fail there for the missing behaviour, and lint must still pass. Passing is checked
  only at the join, in the head worktree.
- **Leave the first run as it is.** It is finished and shipped. Use a distinct ticket id (for example
  `linkding-sort-by-modified-blind`); worktrees and run folders are per ticket id.
- **Compare like with like.** Report blind beside the sequential run of 2026-10-08
  (`docs/runs/2026-10-08-linkding-sort-by-modified/summary.json`): tests written, pass at head,
  fail at base on an assertion, missing-name and crash counts, mutants killed on changed lines,
  spend and time per stage.
- **The second ticket** is linkding commit 573b6f5, "Filter bundles by reading or sharing state",
  upstream pull request 1308; its base is the commit's parent. It touches a model, a migration,
  the REST API, a form and templates, so its contract (field names, filter values, labels) has to
  be stated in the ticket for a blind writer to have a chance.

Track 2: the Restate facts above; raise the inactivity and abort timeouts to fit an 800 s step;
measure resume after killing the service mid-step; screenshot what the UI shows for a run waiting
at the gate. Track 3: the container must run a linkding release that contains the feature under
test (1.47.0 contains 0490013); data goes in through the REST API with a token, never the database.
