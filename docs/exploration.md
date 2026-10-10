# Exploration: observing the factory, Restate, the feature loop, the deployed environment

Proposed 2026-10-10 in answer to Oleg's input of that day (`docs/inputs.md`). **Not decided:** the
plan waits for his yes. The review surface is section 10 onward of
https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa.

## The answer to "does this sound like a plan"

Yes, on one condition. The old lab died doing exactly "explore for a while"
(`docs/reference/lab.md`). So each track ends with a command that runs on linkding and a measured
number, inside a cap. A track that cannot show that is reported as not done, and no tool is scored
beyond Restate, which he named.

## The tracks

| Track | Use case | Work | Produces | Cap |
|---|---|---|---|---|
| 1 · The loop, measured | UC3 | Acceptance tests written blind, from the ticket and the base code only, joined to the developers' commit; revert check and mutmut on them; the sort ticket and "Filter bundles by reading or sharing state" (573b6f5) | A blind mode in Verify, and its numbers beside the sequential run | One session, about 10 USD (estimate) |
| 2 · Watch it run | UC1 | The six steps as one Restate workflow per ticket, the gate as a promise, the UI at `localhost:9070`; the plain driver stays the default; a run report from the run folder for the QA evidence | A run he can watch; the timeouts and resume-after-kill, measured | One session |
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
Temporal, which is deferred (`docs/decisions.md`). The fact that decides both is what the factory
at work runs.

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

1. Yes, no, or reorder the three tracks.
2. What the factory at work runs on (Temporal, Restate, neither yet), and whether the colleague
   meant Restate for it. Decides whether track 2 is a spike or the start of the orchestrator.
3. Whether linkding's own Docker image on this laptop may stand for the deployed environment in
   track 3.
