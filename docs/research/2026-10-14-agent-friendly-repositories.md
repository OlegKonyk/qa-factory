# What makes a repository factory-friendly and agent-efficient, and which tools are worth using: the 2026 practice, QA at the centre

**Date:** 2026-10-14, every page fetched that day. **Status:** done; it serves roadmap item 3 (the
third application's shape and onboarding), item 1 (the deployed run) and the checklist in
`docs/exploration.md`, which it extends. Written in answer to Oleg's input of 2026-10-14
(`docs/inputs.md`): continue the research; what makes a repository factory-friendly and
agent-efficient; any innovative tools we can use. Short by rule 5 of `CLAUDE.md`.

**How far to trust it.** Each claim carries one label. **Checked:** the primary page (the
company's own post or its verbatim republication, the project's README or documentation, the
paper's abstract) was fetched and read on 2026-10-14. **Doc:** a vendor's or project's own page
says so and nothing was run. **Not verified:** a search snippet, a secondary blog, a curated
list. A company's number is its claim. Nothing was installed or run. Tool verdicts follow rules 1
and 2 of `CLAUDE.md`: AI writes, deterministic tools check; no comparisons, pick and replace in
use.

## What makes a repository factory-friendly, in six points

1. **One short agent file at the root with exact, runnable commands, and nothing an agent can
   read from the code.** AGENTS.md is now stewarded by the Agentic AI Foundation under the Linux
   Foundation, read by Codex, Jules, Cursor, Copilot's coding agent, Gemini CLI and two dozen
   others, with "more than 60,000 open-source projects" using one; the nearest file in the tree
   wins, so a monorepo nests them (doc, agents.md). Claude Code reads `CLAUDE.md`, which can
   import the shared file with `@path`; its own guidance: "Bloated CLAUDE.md files cause Claude
   to ignore your actual instructions!", include the commands Claude cannot guess, the test
   runner, the repository etiquette and the environment quirks, and exclude what it can read
   from the code (checked, code.claude.com, best practices). Stripe applies its agent rule files
   "conditionally by subdirectory rather than as global rules" (checked, Stripe's post as
   republished). **Here:** the checklist's item 1 and the strategy rule are this file; the
   onboarding of item 3 should read the application's agent file first and write one if there is
   none.

2. **A check the agent can run that returns pass or fail, and evidence instead of assertion.**
   Anthropic's guidance in its own words: "Give Claude a check it can run: tests, a build, a
   screenshot to compare. It's the difference between a session you watch and one you walk away
   from." and "Have Claude show evidence rather than asserting success: the test output, the
   command it ran and what it returned". A hook is deterministic where an instruction file is
   advisory; a Stop hook can refuse to end a turn until a script passes (checked). **Here:** the
   factory's shape, by its rules: the writer's session ends in the revert check, mutation and
   the suite, and the run folder is the evidence. Nothing to change; the sentence belongs in the
   meetings.

3. **Feedback in seconds locally, the big suite selected in CI, rounds capped.** Stripe's agents
   run "selected lints on each git push in under 5 seconds" on the devbox before CI, CI runs
   selected tests from a suite of over 3 million, failures with known fixes are fixed
   automatically, the rest go back to the agent, and CI is capped at "often one, at most two CI
   runs"; the principle is "if it's good for humans, it's good for LLMs, too" (checked, Stripe's
   post as republished; the numbers are Stripe's). A consultant's four-dimension model says the
   same from the small end: a suite under 5 minutes, coverage above 70 % on domain logic and
   endpoints rather than 100 % everywhere, a short entry file that maps to deeper docs, clear
   layers, and varied fast signals, "The model is rarely the bottleneck. The codebase is." (not
   verified: one practitioner's post). **Here:** the checklist's item 7 gains a number (lint in
   seconds, the suite in minutes, or selectable) and the factory's caps per ticket are this
   practice. Test selection by impact (roadmap item 9) is what makes a slow suite agent-usable.

4. **A standard, isolated, pre-warmed environment per run.** Stripe's agents use the engineers'
   own devboxes: isolated, "pre-warmed", about 10 seconds to start, with the code and services
   loaded, cut off from production and the internet (checked, as above). Thoughtworks moved Dev
   Containers to Trial on 2026-04-15 because they "have found a compelling new use case as
   sandboxed execution environments for coding agents" (checked, the radar entry). Hosted
   sandboxes have settled on microVMs for untrusted agent code (not verified: vendor roundups).
   **Here:** the portable form of checklist item 1 ("one command to bring the app up with seeded
   data") is a dev container or compose file in the application's repository; the factory's fetch
   script per application is the stand-in. Item 3's application should have one or get one.

5. **Context arrives through tools, not through prose in the prompt.** Stripe's agents pull
   docs, tickets and build status through a central MCP server with over 400 tools before a run
   starts (checked, as above). Anthropic: "CLI tools are the most context-efficient way to
   interact with external services" (checked). **Here:** the cheapest version is a ticket that
   states the public contract, which is item 4's readiness check; a tracker tool comes with item
   7. For browser tests, see the Playwright CLI below.

6. **Reliability is a property of the system around the model.** A 2026 monograph with 206
   reliability records: "Many apparent model failures originate elsewhere in the system", in
   the harness, the execution environment, retrieval, state, verification and observability
   (checked, abstract of arXiv 2608.13867, 2026-08-14). **Here:** when a run fails, the record
   has to say which layer failed; the stronger model's four answers (retry, the change is wrong,
   the environment, cannot decide) are that sorting.

## Agent-efficient, with QA at the centre: what the test writer needs from the repository

Beyond the six points, specific to writing and checking tests. The first three were already on
the checklist and the sources confirm them; the fourth is new.

- **Test data through the public API, never the database** (checklist item 5), so the same case
  runs inside the suite and against a deployed URL; linkding's browser tests fail this.
- **Selectors by role and label, test ids where roles are not enough** (item 4); Playwright's
  own "healer" agent exists because selectors break (doc, below).
- **A strategy rule** that says which kind of test goes where (item 3), and the test helpers
  named (item 2), so the writer and the checks know them.
- **A machine-readable API description** (OpenAPI for a FastAPI service, a schema for GraphQL):
  it is the contract the Frame gate checks a ticket against, it feeds property-based API checks
  (Schemathesis below), and it is what a tracker tool would hand the agent. New on the checklist.

## Tools looked at, with a verdict each

| Tool | What it is | Label | Verdict under rules 1 and 2 |
|---|---|---|---|
| Playwright test agents (planner, generator, healer) | First-party: `npx playwright init-agents --loop=claude`; the planner explores the app and writes a Markdown plan, the generator writes tests checking selectors live, the healer replays a failing test, finds equivalent elements, patches, reruns, and skips the test when it believes the feature is broken. Examples are TypeScript only; Python not stated | checked, playwright.dev | **Watch.** The factory's writer already produces Python browser tests inside the app's suite. The healer's loop is the shape of a selector-repair round for item 9's quarantine; not needed before a run shows selector breakage |
| Playwright CLI (`@playwright/cli`, Apache-2.0, about 14,000 stars) | A command line that drives a browser for coding agents: open, click, fill, snapshot, find, screenshot, route; "Token-efficient. Does not force page data into LLM", positioned by its authors as the better fit for agents than the Playwright MCP server. Node 18+, works against any site | checked, the README | **Try in the next browser-test run** (item 1 or 3): give the writer's session the CLI for exploring the running app and measure the writer's tokens and cost against the bundles run (3.62 USD, measured). Adopt if cheaper; drop if not |
| Dev Containers | A `devcontainer.json` that brings the application up, now a Trial-ring tool for sandboxing agents | checked, Thoughtworks | **Adopt as the checklist's form of "one command to bring the app up"**: item 3's application should have one; `docs/adopt.md` names it as the preferred shape for a fetch script |
| AGENTS.md | The cross-tool agent file; Claude Code imports it from `CLAUDE.md` | doc, agents.md | **Adopt in the checklist:** read it first when onboarding; write one when missing, with the commands the factory needed |
| Schemathesis (MIT) | Property-based API checks generated from an OpenAPI or GraphQL document, with a pytest decorator and stateful operation chains inferred from the schema | checked, the README | **Record, do not adopt now.** It is a check, not a test writer, so it is closer to a linter than to the generators rule 1 bans, but it is a non-AI generator of inputs. When item 3's service has an OpenAPI document, the session may run it once as a check and report; Oleg decides whether it joins the checks |
| mutmut | 3.8.0, released 2026-09-12, Python 3.10 to 3.15; the current release | checked, PyPI | **Keep.** No newer release changes what it can mutate; roadmap item 2 stands (decorated functions, `__init__.py`) |
| Mutahunter (AGPL-3.0) | Mutants generated by a model, language-agnostic, Java example; no release, last visible activity 2025 | checked, the README | **No.** AI inside the check, and no sign of maintenance |
| Qodo-Cover (AGPL-3.0) | AI unit-test generation that keeps a test only if coverage rises | checked, the README | **No.** "No longer maintained" since 2025-06-15; coverage, not mutation, as the keep rule |
| Keploy | API tests and mocks recorded from real traffic | not verified, a curated list | **Look at it when item 3 asks what keeps a mock reliable** (his mock scheme, 2026-10-13); nothing before |
| Pynguin, EvoMaster | Non-AI test generators | not verified | Out by rule 1 |
| Durable engines other than Restate | Temporal, Inngest, DBOS, Prefect | not verified | Nothing new since the morning's pass; Restate kept (his answer of 2026-10-14) |

## What this changes

- **The checklist in `docs/exploration.md`** grows from eight items to twelve: an agent file,
  lint in seconds and a suite in minutes or selectable, a container recipe, a machine-readable
  API description; the existing items are kept with their numbers.
- **Roadmap item 3** reads the agent file first and scores the application against the
  checklist before the ticket; what it lacks is recorded, not fixed, unless the run needs it.
- **Roadmap item 1 or 3** tries the Playwright CLI in the writer's session and measures.
- **`docs/adopt.md`, section 3,** points at the checklist.
- **Nothing for Restate, mutmut or the checks.** The published practice is what the factory
  does; the gap is in the repositories it runs on, which is what he wanted to learn.

## Sources

Fetched 2026-10-14.

- agents.md (the specification site), https://agents.md/
- Claude Code best practices, https://code.claude.com/docs/en/best-practices
- Stripe, "Minions: Stripe's one-shot, end-to-end coding agents" (Alistair Gray; original at
  stripe.dev, read as republished at
  https://www.engineering.fyi/article/minions-stripe-s-one-shot-end-to-end-coding-agents)
- Thoughtworks Technology Radar, Dev Containers, 2026-04-15,
  https://www.thoughtworks.com/radar/tools/dev-containers
- Jarmak, "Engineering Reliable Coding Agents: Evaluating and Operating the System Around the
  Model", arXiv 2608.13867, https://arxiv.org/abs/2608.13867
- Galarza, "Four dimensions of agent-ready codebase design", 2026-03-25,
  https://www.damiangalarza.com/posts/2026-03-25-four-patterns-that-separate-agent-ready-codebases/
  (not verified)
- Playwright test agents, https://playwright.dev/docs/test-agents
- Playwright CLI, https://github.com/microsoft/playwright-cli
- Schemathesis, https://github.com/schemathesis/schemathesis
- mutmut on PyPI, https://pypi.org/project/mutmut/
- Mutahunter, https://github.com/codeintegrity-ai/mutahunter
- Qodo-Cover, https://github.com/qodo-ai/qodo-cover
- awesome-ai-testing (a curated list; the Keploy and Pynguin rows), https://github.com/tugkanboz/awesome-ai-testing
  (not verified)
