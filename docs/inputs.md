# Inputs

Oleg's direction, newest first, quoted as given (dictated, so expect transcription slips), each
with how it was read and what it changed. File an input here before working on it.

## 2026-10-10 · A UI to observe the factory, Restate, the feature loop, and an exploration period

> This is really, really interesting stuff. I will spend more time on it later today. Overall, I
> like where we are moving. I want to ask for a couple more things. I would like to start having
> some skin for this whole thing so I can start observing stuff. A colleague recently brought this
> up. https://restate.dev/ How useful it would be for our use case.
>
> Also, the major question that everyone has every time I start talking about the software
> factory that we are building is: my current plan is that every repo that we're going to be
> dealing with will be agent-friendly. That's the basis: it needs to be capable of authoring
> end-to-end tests that can be trusted and then executing those end-to-end tests on the deployed
> environment eventually. It's going to be the same. I don't know how to do it.
>
> Imagine that we are putting up a small feature, a straightforward small feature. The
> implementation part of the factory will implement the feature. Then, the time for QA stuff:
> regression plus new coverage. Is it the same session, or is it happening in parallel as the
> feature is being developed? That can also be useful. How to organize that loop is my question.
>
> I would like to rely on the results of reputable companies. A lot of people are doing the same
> crap these days, so I want to make sure that you scan the internets and help me adopt some good
> ideas. I would like to find something that is ready out of the box and useful for these kinds of
> use cases on the QA side of things.
>
> Let's approach it from this angle as well, plus the questions that I asked you. I would like to
> run this experimentation and exploration for a little while. Let me know if this sounds like a
> plan.

How it was read:

- "Some skin" is read as a UI on top of the factory, the brief's "with a UI on top": a place to
  watch runs, steps and gates. Restate is named by him, so its usefulness is assessed by name
  (rule 2 allows it).
- These are the use cases he had in mind (`docs/architecture.md`): observing the factory; every
  repository agent-friendly, able to author trusted end-to-end tests and run them against a
  deployed environment; and the loop for a small feature: does QA (regression plus new coverage)
  run after implementation in the same session, or in parallel while the feature is built.
- He asks for a scan of what reputable companies publish and for ready-made QA pieces, then an
  exploration period. Research stays short and labelled (rule 5); each exploration track has to
  end in something that runs on a real application (rules 3, 4, 6), so the period does not repeat
  the lab. The plan and its questions go to him; he decides (rule 8).

## 2026-10-10 · A visual walkthrough of the architecture, then his use cases and how they scale

> Cool. Now you need to create some visuals for me and a good artifact so I can consume the
> current architecture and current setup, and discuss some more use cases that I have in my mind.
> We're going to have to support them, and not only support but explore how that can be done in
> a scalable way.

How it was read: a published page with diagrams that explains what the factory is today (the
flow, what happens inside Verify, how a run stops and resumes, where every piece lives, what a
new application needs, what the first run measured) and shows honestly where today's design is
fixed to one laptop, one ticket and one application. The use cases are his and not yet told; the
page prepares the discussion with a way to place each one on the architecture, and records them
as he gives them. No use case is designed or decided before he names it.

## 2026-10-10 · Persist the state so a session can walk him through it

> Please make sure the current state is properly persisted. Sometimes I want to sit together with
> you so you can explain to me what we tried, what we have, and we can decide on next steps.

How it was read: nothing a later session needs may live only in a conversation or a scratch
folder. The repository has to hold what exists (`docs/status.md`), what was decided
(`docs/decisions.md`) and also what was tried, including what failed and why, so that a fresh
session can sit with him and explain it, then help him pick the next step. The parked run on
linkding is part of "the current state": it has to survive whatever the next session does.
Changed: a session log (`docs/log.md`); the build specs and the first run's records copied into
`docs/`; one worktree pair per ticket so a second ticket cannot disturb a parked one; a line in
`CLAUDE.md` that every session leaves that record.

## 2026-10-08 · Start the first build session

> let's start!

How it was read: run `docs/next-session.md` as written: build the first end-to-end path and run
it on linkding. Changed: nothing beyond that prompt; the session's result is pull request 6.

## 2026-10-08 · The plugins are the toolchain for building the factory

> Hey, listen. We will be building a factory, right? That itself, I want to use those plugins
> [to build it] so we can use tokens and have code quality.

How it was read: the sessions that build the factory use his plugins as their toolchain: the
supervisor plugin to triage work and delegate implementation to cheaper models with evidence
contracts and to review a slice before it is accepted, the py-testing skills for test code, the
review checklist before a pull request. That is how tokens are saved and code quality kept, and
how the plugins get improved along the way (`docs/plugin-notes.md`). The previous entry stands
for the factory itself: it may use or copy a piece when a step needs one. The earlier reading of
"does not have to be used as part of the factory" as "do not use them" was wrong. Changed: a
toolchain rule in `CLAUDE.md`; `docs/next-session.md`.

## 2026-10-08 · The plugins are a separate project, improved along the way, not a factory part

> What about plugins? Have you established that we will be using the toolchain so it can be
> improved as well? [...] No, no, no. What I mean by plugins is my other project, right? I want to
> improve it along the way. It does not have to be used as part of the factory. We will be
> building a factory where the factory can use some of that if needed, or take a version of it.

How it was read: his Claude Code plugins (`~/dev/konyklabs/claude-plugins`: supervisor, signoff,
py-testing, prod-readiness and the rest) are their own project. The factory does not depend on
them. A step may use one, or copy a version of one, when that is the shortest route. What a
factory session learns about a plugin (a gap, a fix, a skill that would have helped) is written
down for him to carry into that project. Changed: item 10 of the delegated decisions is
superseded; `docs/next-session.md` and `docs/status.md` follow.

## 2026-10-08 · Rapid mode: sessions merge their own pull requests, nothing waits for Oleg

> No, it's the other way around. I want you to keep merging shit. Don't wait for me. This is
> experimental stuff. Don't create. This is rapid development mode. Okay, let's establish that and
> be very clear. I don't want you to wait for me for nonsense, okay?

How it was read: a session merges its own pull request once `just check` is green, including
pull requests that change `CLAUDE.md` or `hooks/`. Nothing waits for his yes. He reads the result
and overturns what he dislikes. "Don't create" is read as "don't create waits". Changed: the rapid
mode rule in `CLAUDE.md`; pull requests 1 and 2 merged in this session; recorded in
`docs/decisions.md`.

## 2026-10-08 · Temporal deferred; existing plugins as factory parts; a self-improving factory

> Let me ask you this: what if we drop Temporal? Is it going to slow us down, or the other way
> around? I'm trying to see if Temporal introduces unnecessary friction for us.

Then, on the answer (defer, not drop):

> I agree with you. Let's record that as a part of the plan. After that, give me an updated page
> for any decisions that you think I can make. And also, we have our plugins, like supervisor
> stuff. I want to see if we can use that tooling to also improve that. It's going to be like a
> self-improving little factory.

How it was read:

- Temporal is deferred, not dropped: the first path is plain Python with a run folder and a
  resume; Temporal is reconsidered when the loop runs. Recorded in `docs/decisions.md`.
- His existing Claude Code plugins (supervisor, signoff, py-testing, prod-readiness, the review
  checklist) are candidate factory parts, not things to rebuild. Which ones, and where, is a
  decision for him; added to the review page.
- "Self-improving" is the diagram's learning subflow: decisions, interventions and review
  findings recorded on every run, and the useful ones promoted into the rules and skills the next
  run reads. Shape proposed on the review page; built after the loop runs (rule 3).

## 2026-10-08 · Correction of the correction: the whole factory, QA built fully, the rest simulated

> Still not correct. I will be very, very brief, so my words cannot be interpreted in multiple
> ways. We are building a factory, the whole freaking thing, with a concentration on QA. I need to
> at least simulate other parts of the factory, like simplified versions of that, right? Also, are
> those blog posts of any use? Also, the Temporal open source thing.

How it was read:

- The product is the whole factory from the diagram, running on this machine. The QA step is
  built fully. The other steps (frame, plan, implement, review, ship) exist as simplified
  versions, enough to run a ticket through the loop.
- The earlier correction still holds for Temporal: it is one of the tools, and the factory is kept
  generic enough that another harness could replace it.
- He asked for an assessment of the blog post and of the Temporal Agent Harness. Answered in the
  session, recorded in `docs/decisions.md` once he decides.

## 2026-10-08 · Correction: the product is the QA floor; Temporal is one tool among several

> Factory branch. I don't know if that's the right term. Did you look into the temporal solution
> at all? [the agent-harness repository and its blog post]. Be clear: Temporal is one of the
> tools, the QA piece, the QA floor of the factory. Let's put it that way. It's to be somewhat
> generic so it can work with other external harnesses. Continue defining. No, no. Some of these
> points are not correct. Review this whole plan, and let's sync up again once you have a better
> understanding. [the backbone diagram again] This diagram is another sort of view from another
> point, but it's all the same factory ideas.

How it was read:

- The product is the QA floor of the factory, not the factory. The factory's backbone (the
  diagram's Frame, Plan, Implement, Verify, Review, Ship) is built by the team; the floor is what
  the Verify step runs, and what feeds the regression suite.
- Temporal and its agent harness are one orchestration the floor must plug into. The floor stays
  generic: a core that knows nothing about Temporal, and thin adapters, Temporal first, others
  later. The earlier reading ("a factory bench on Temporal, with QA as the first built step and
  stubs for the rest") overreached and is withdrawn.
- The two links are the Temporal Agent Harness repository and its announcement post. The second
  short link from the slide is recorded as that repository on his word.
- The harness was read from its 0.6.0 source, not run. What it offers a QA agent: typed
  operations with pydantic input and output, repository-touching work as activity tools on a
  worker or callback tools on the laptop, human approvals and callbacks as durable waits, one
  event stream a UI replays. It is Pre-Alpha by its own classifier, which is the reason the core
  stays independent of it.
- "Factory branch" is not understood; asked.

## 2026-10-08 · Planning session: expectations first, no code until they are agreed

> I want you to pick up from our previous session and prepare stuff for us. Very important: take
> everything that you got from previous work with a grain of salt. What I want you to do, and what
> I want you and me to do, is make sure we're on the same page in terms of expectations.
>
> In addition to the notes from previous sessions, this is the brain dump that I can describe in
> three sentences, pretty much. At my job, we are building, as a team, a software factory, right?
> Pretty much stuff that you can find online, like the latest fad, right? Everyone builds a
> software factory. I am a software engineer, and I am responsible for validation and adding test
> coverage, so this is a multiple-facet effort.
>
> - The factory itself, the version that I hopefully can run locally. We have pretty powerful
>   laptops. Hopefully, it can be run locally as a working bench.
> - You hopefully have information from Temporal links and stuff. I watched their presentation.
>   Very impressive. I was hoping maybe we can build something like that locally on a local stack,
>   because I believe they do have a local stack for Temporal.
> - The framework itself: we are a primarily Python-based shop. I will need to have both pytest
>   API tests and Playwright UI tests. Our applications under test are not complicated. The
>   problem is those are old legacy systems plus some greenfield work. The framework itself,
>   you're going to have to help me define the interfaces that the other parts of the factory
>   will work with.
>
> Let's work on the high-level expectation definition before we move any further. Once you
> analyze the information that we have, let's make sure that is done before any actual code is
> written. The previous iteration failed miserably. We wasted a lot of tokens, so this time we
> need to use our brain a little bit more.

How it was read:

- Three facets, in his order: (1) the whole factory, runnable on one laptop as a working bench;
  (2) that factory shaped like what Temporal showed in its webinar, on Temporal's local
  development stack; (3) the test framework: pytest for API tests, Playwright for browser tests,
  against applications that are simple but old, plus some new ones.
- The third facet adds something the open questions did not have: the framework's interfaces,
  meaning what the other steps of the factory (frame, plan, implement, review, ship) hand to QA
  and get back. That is a contract question, and it was added to the planning session as a ninth
  item.
- "Grain of salt" applies to the eight open questions themselves: they are re-read with him, not
  taken as the agenda.
- Nothing is built in this session. The output is his recorded decisions (`docs/decisions.md`),
  an updated `docs/status.md`, and the prompt for the first build session.

## 2026-10-08 · Build the product on Temporal; prepare the repository so the lab's mistake does not repeat

> Okay. So now we need to. I don't want to lose all this work, okay? I don't want to lose this
> work, but I also don't want to get the next session misled. This is what we're going to do. I'm
> dropping you a couple of documents so you can take a look. That's another brainstorming session
> of the ideas for the software factory. What I want you to do: we will build the exact product.
> We will build a software factory on top of Temporal, everything local. Hopefully, that's
> possible, and we do concentrate on the QA part of the business.
>
> I need to be able to reliably generate test coverage for API and Playwright tests. I want to
> validate that tests are not misleading. I want to produce human-readable test cases, or
> whatever, some artifact that can be observed and approved by a person. Make that a part of the
> ongoing regression suite.
>
> We're not going to be blindly adding coverage. We will be assessing where it should be added
> based on the inverted pyramid, pyramid, honeycomb, whatever the hell we decide.
>
> One thing: this is just a preparation session. We're not making any decisions or anything. I
> want us to prepare the repository so shit like this does not happen again, where we burn tokens
> for days evaluating some stupid old tools, okay?

Then, while the repository was being prepared:

> We still want to have this as a reference because so much work was done. Maybe we can salvage
> something. In a new repo, let's have some references.

The "couple of documents" are three photos: two slides from a Temporal webinar (its resource links
and community page) and the team's diagram of the factory's backbone. The photos are in
`.local/handoff/2026-10-08-factory-backbone/` only. The diagram's flow, in generic words, is in
`docs/brief.md`.

Asked where the product lives, he chose a new repository, with the lab left intact as an archive.

What it changed:

- This repository exists. Its `CLAUDE.md` states the product and the rules that keep it one.
- `docs/brief.md` is written from this input and the diagram.
- `docs/reference/lab.md` points into the old lab at its final tag, with what may be salvaged.
- Nothing about the factory's design is decided. `docs/status.md` lists the open questions.

## 2026-10-08 · AI generates, deterministic tools verify

> Let me restate what I need. We are building a software factory based on the latest ideas in the
> industry. I need to work on the test generation and verification part of the system. Yes, I want
> to use deterministic tools, but not something that you pull out of your ass that does zero
> useful work, like this Py and Gwinth shit. It's 2026. I'm not going to be doing code generation
> without AI. AI is for code generation, but tools like Mutmut: perfect, great tool. We're using it
> already, and we're going to use it still. GitHub Spec, yeah, maybe. That's inconsequential, but
> I don't want you to worry about this. I want you to tell me: what did you hear at the beginning
> that took you this route of building this fucking laboratory that produces zero useful code?

"Py and Gwinth" is Pynguin, a test generator that uses no AI; "GitHub Spec" is GitHub Spec Kit.

What it changed: rules 1 and 2 of `CLAUDE.md`. The answer to his question is in
`docs/reference/lab.md`, "Why it produced no useful code".

## 2026-10-06 · Kickoff (in the old lab)

> We have a very exciting project to work on. At my workplace, we are tasked to build an AI
> software factory, the popular thing out there. I want you to organize this project properly.
> The goal is to build a set of prototypes to see what is possible these days. [...] I will be
> responsible for the QA slice of all this. I want us to concentrate on that specifically, because
> a lot of other things will be inherited from the developer solutions, but the QA piece needs to
> be defined by us. [...] I would like to have a handful of distinct solutions to touch them, feel
> them, and make a decision.

Kept here because its misreading is the reason this repository has the rules it has.
