# How software factories and AI-era delivery pipelines are run in 2026: what the published practice says, and what it changes here

**Date:** 2026-10-14, every page fetched that day. **Status:** done; it serves roadmap item 4
(every person point exposed) and item 6 (Ship as a pull request). Written in answer to Oleg's
input of 2026-10-14 (`docs/inputs.md`): he had never seen the earlier research and wanted the
latest. Short by rule 5 of `CLAUDE.md`: it answers what blocks the next build step and stops.

**How far to trust it.** Each claim carries one label. **Checked:** the primary page (paper
abstract, the company's own post, the project's README or documentation) was fetched and read on
2026-10-14. **Doc:** a vendor's or project's own page says so and nothing was run. **Not
verified:** a search snippet, a secondary blog or a podcast write-up. A company's number is its
claim, never a measurement. Nothing was installed or run.

## The research that already exists, and why he never saw it

The earlier research lives only in the old lab, `~/dev/assay/docs/research/` (GitHub
`OlegKonyk/assay`, tag `lab-end-2026-10-08`). It was written for the lab's comparisons between
2026-10-06 and 2026-10-08, was never carried into this repository, and was never put in front of
him as a report; `docs/reference/lab.md` lists it in one row ("skim for names only"). What each
file covers, so he knows what is there:

| File (in the lab) | Fetched | What it answers |
|---|---|---|
| `2026-10-06-authoring-landscape.md` | 2026-10-06 | How companies and products have a model write tests: Uber, Meta, Microsoft accounts; papers with validity numbers; browser-test products; who checks that a generated test can fail |
| `2026-10-06-regression-landscape.md` | 2026-10-06 | Running regressions when agents write the code: test selection, flaky-test handling without retries, record-and-replay, mutation testing at scale, how agent vendors verify changes before merge |
| `2026-10-06-factory-ui.md` | 2026-10-06 | One place to see and steer a factory: the code host (GitHub Agent HQ, Agentic Workflows), the tracker (Linear for Agents), vendor workbenches (Claude Code's agent view, cloud sessions), open workbenches, pipelines as code, factories sold as products |
| `2026-10-07-deterministic-layers.md` | 2026-10-07 | Thirteen deterministic test layers (store invariants, authorization tables, contract tests, property-based testing, migrations, accessibility) judged for a lab round that never ran |
| `2026-10-08-qa-seat.md` | 2026-10-07 | What the QA role becomes where agents write tests at scale, in seven points: the person prunes rather than writes; per-repository context pays and concentrates; "derive, then sign" (Meta ACH, Shopify Dispatch); authorization rules need a signed source; where attention goes is the design decision (Redwood, Meta RADAR); a model reading code is not a gate; signed evidence (in-toto, SLSA) |

None of them is about how a software factory or an AI-era delivery pipeline is run as a whole:
where the people sit, what is enforced, what the big platforms ship. That is what this pass adds.
The lab's labels were the same three as here.

## What the 2026 practice says, in six points

1. **Published factories put the person at two fixed gates, specification and merge, and keep
   every loop between them capped and automatic.** Dropbox's platform (Nova, about 1 in 12 pull
   requests): a person defines the task, the agent works inside guardrails, the result is
   validated, and a person makes "the final judgment before any code reaches production"
   (checked, Dropbox's own post of 2026-05-28; the share is the company's claim). Augment's guide
   names five stages, intake, specification, build, verification, shipping, "with specification
   approval and merge as the two human gates", and calls verification "the factory's binding
   constraint" whose review capacity has to be planned, not discovered (doc, a vendor that sells
   a factory product). StrongDM's account: "the humans design specifications, curate test
   scenarios, and watch the scores" (not verified, quoted through that guide). Stripe's Minions
   start from a Slack message and end as a pull request that passed the automated tests; every
   change is reviewed by a person and contains no human-written code; about 1,300 pull requests
   a week (not verified: secondary write-ups, the original post not fetched).
   **Here:** the brief's table of 2026-10-08 already has the same two gates and the capped loops.
   The factory has built only the Verify gates. Frame (the specification gate) and Ship (the
   merge gate) stop for nobody today.

2. **A process written in prompts is not enforced; a process run as code is.** A paper under
   review at ACM TOSEM proposes a protocol language for AI-SDLC processes and states the point
   directly: "process encoded in prompts is flexible but unenforceable", and in its language
   "protocol steps cannot be skipped, by construction". On SWE-bench Verified, the same bug-fix
   method gave no gain as prose instructions and a 14 to 22 point gain run as a validated,
   self-correcting process (checked, abstract of arXiv 2606.20615, v3 of 2026-08-16; the
   numbers are the authors'). A second paper frames the agent era around a "trustworthy change"
   that moves through verification, integration and acceptance, with "execution grants no
   acceptance authority": agents produce candidates and evidence, people keep acceptance
   (checked, abstract of arXiv 2609.04630, 2026-09-04; its claims are stated as hypotheses).
   **Here:** the driver is that enforcement. Steps are code, the checks are deterministic, a
   question can never approve failing work, and a person's answer is a file the record keeps.
   Nothing to change; worth saying in the meetings.

3. **Durable execution is the common answer to "a run that waits for a person".** The 2026
   comparisons (Temporal, Restate, Inngest, DBOS, Prefect) agree on the shape: the workflow's
   steps are journaled, a crash replays the journal, and a wait for an approval is a durable
   promise or signal that survives restarts and costs nothing while it waits (not verified: all
   are vendor or affiliate blogs). Restate's own documentation: a single Rust binary, a journal
   per invocation replayed after a crash, suspension while a handler waits for "a user approving
   an order" (checked, docs.restate.dev). The Temporal Agent Harness, the piece his team's
   webinar showed, is at 0.6.0, "very early and experimental", integrates Gemini, the OpenAI
   Agents SDK and PydanticAI, no Claude Code, and ships tool approvals that "pause inside the
   workflow and resume durably" and a browser UI (checked, the repository's README). Licences:
   Temporal MIT, Restate under the Business Source License (not verified; one comparison says
   so, Restate's repository page does not show it).
   **Here:** nothing has changed since the decision of 2026-10-08 (Temporal deferred) and the
   trial of 2026-10-12 (Restate behind a flag). What the engine buys is exactly the durable wait,
   so its value rises with the number of gates (roadmap item 4), not with the number of tickets.

4. **The pull request is the industry's approval surface, and the code host is becoming the
   factory's front.** GitHub Agent HQ (2026-02-04): assign an issue to Copilot, Claude or Codex,
   the agent works asynchronously with a log of what it did and why, submits a draft pull
   request, and a person reviews it; output is "reviewed, compared, and challenged, not blindly
   accepted"; organisation-wide policies on which agents and models are allowed, audit logs,
   an automated first-pass review before a developer sees the code (checked, GitHub's post;
   Claude and Codex in public preview). Claude Code on Anthropic's side: cloud sessions
   generally available since late September 2026 and routines that start a session on a
   schedule, an HTTP call or a GitHub event (not verified: secondary posts); a Code Review that
   runs as a check on a pull request, and hooks that block an action when the hook itself fails
   (checked, the Claude Code changelog, 2.1.290 to 2.1.299, October 2026).
   **Here:** roadmap item 6 (Ship as a pull request, approve on it) is the right destination,
   and it is the gate the field agrees on. A factory whose approvals live on pull requests plugs
   into whichever front the team adopts.

5. **Verifying agent-written tests means making them kill mutants, in every published account.**
   Uber's AutoCover (ICSE-SEIP 2026): a multi-agent generator whose validator runs the tests and
   mutation testing, with a "viable" rate (passing tests that add coverage) of about 80 % for
   Python, 40 % Go, 20 % Java, and developers accepting about 44 % of viable tests in the IDE
   (checked, the paper; the authors call coverage "an imperfect proxy for quality"). Meta's ACH
   starts from a stated concern, derives mutants, and generates tests that must fail on the
   mutant and pass on the original; over 70 % accepted (checked in the lab's sweep, 2026-10-07;
   the acceptance figure is through a secondary review). AdverTest (arXiv 2602.08146, v3 of
   2026-08-31): a test-writing agent and a mutant-writing agent in an adversarial loop guided by
   coverage and mutation score; 8.56 % more faults found than the best LLM method and 63.30 %
   more than EvoSuite on Defects4J (checked, abstract; the authors' numbers). A vendor's guide
   says the same in plain words: coverage cannot show a test asserts behaviour; run the suite
   against mutants and look at the survivors (doc).
   **Here:** the revert check plus mutmut on the changed functions is the published practice.
   AdverTest's loop is the shape of a repair round guided by surviving mutants; a candidate for
   roadmap item 8 (learn from each run), not now.

6. **Measure delivery, not volume.** The 2025 DORA report ties AI adoption to higher throughput
   and lower delivery stability; METR's trial found experienced developers 19 % slower with AI
   tools while believing they were faster; Spotify's verification controls lagged behind a
   doubling of merged changes (all not verified here: quoted through Augment's guide and the
   lab's sweep). Microsoft's own account: the top 10 reviewers wrote 61 % of all comments on
   878 agent pull requests (checked in the lab's sweep).
   **Here:** the person is the bottleneck the gates must not create. Passing work is approved by
   the factory (2026-10-10); a person is asked only at the two fixed gates and when a stronger
   model cannot decide. The numbers to keep per ticket are already recorded: spend, time, rounds,
   who answered what.

## What this changes in the roadmap

- **Item 4, every person point exposed, moves into Now.** The field's two fixed gates are the two
  the factory lacks. Built on the envelope, engine-agnostic, with "correct" as well as "approve".
- **Item 6, Ship as a pull request, is confirmed as the merge gate**, not only a destination.
- **Restate: no change.** Its value is the durable wait; decide the default engine when the
  pull-request gate exists.
- **Not taken:** a protocol language, Agent HQ, routines, the Temporal harness. None is needed
  for the next build step; each is recorded here with its date so a later session does not
  research it again.

## Sources

Fetched 2026-10-14 unless marked.

- Dropbox, "Beyond code generation: rethinking engineering productivity in the age of AI agents",
  2026-05-28, https://dropbox.tech/culture/beyond-code-generation-rethinking-engineering-productivity-in-the-age-of-ai-agents
- Augment Code, "What is a software factory?", https://www.augmentcode.com/guides/what-is-a-software-factory
  (vendor)
- Prifti, De Meo, Provetti, "Specifying AI-SDLC Processes: A Protocol Language for Human-Agent
  Boundaries", arXiv 2606.20615 v3, https://arxiv.org/abs/2606.20615
- Wang, Liu, "Software Engineering in the Agent Era: From Trustworthy Change to Human-Agent
  Software Organizations", arXiv 2609.04630, https://arxiv.org/abs/2609.04630
- Restate, "Durable execution", https://docs.restate.dev/concepts/durable_execution;
  repository https://github.com/restatedev/restate
- Temporal Agent Harness, https://github.com/temporal-community/temporal-agent-harness
- GitHub, "Pick your agent: use Claude and Codex on Agent HQ", 2026-02-04,
  https://github.blog/news-insights/company-news/pick-your-agent-use-claude-and-codex-on-agent-hq/
- Claude Code changelog, https://code.claude.com/docs/en/changelog (entries 2.1.290 to 2.1.299)
- Uber, "Automated Software Test Generation at Industry Scale Using a Multi-Agent Architecture
  and Workflow Integration", ICSE-SEIP 2026, https://homes.cs.washington.edu/~rjust/publ/auto_cover_icse_2026.pdf
- "Test vs Mutant: Adversarial LLM Agents for Robust Unit Test Generation", arXiv 2602.08146 v3,
  https://arxiv.org/abs/2602.08146
- Meta, "Mutation-Guided LLM-based Test Generation at Meta", arXiv 2501.12862 (read in the lab,
  2026-10-07)
- Stripe Minions, secondary only: https://infoq.com/news/2026/03/stripe-autonomous-coding-agents/
  and https://blog.bytebytego.com/p/how-stripes-minions-ship-1300-prs (not verified)
- Durable-execution comparisons, all vendor or affiliate blogs (not verified):
  https://cadenya.com/other-content/restate-vs-temporal-for-ai-agents,
  https://comuvia.ai/articles/durable-execution-for-ai-agents-temporal-vs-inngest-vs-restate-vs-prefect
