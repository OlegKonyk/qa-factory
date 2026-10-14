# Inputs

Oleg's direction, newest first, quoted as given (dictated, so expect transcription slips), each
with how it was read and what it changed. File an input here before working on it.

## 2026-10-14 · Review the roadmap: every person point exposed, what Restate is for, the research he never saw

> Please review the roadmap and current implementation plan. A couple of things I want to make
> sure we have in the works: if you think about a factory line, there are multiple points where
> people need to interact to correct or approve something. We need to have all those interfaces
> exposed. That restate tool: I still don't clearly understand what it's about or if it's needed.
> Also, I have never seen the research report that we did before on finding the latest online
> trends and recommendations on implementing software factory and AI SDLC. I want to make sure
> that we have the latest on that as well.

How it was read:

- **Three asks, no build.** A review of the roadmap against the brief's person points, a plain
  explanation of Restate with a recommendation on keeping it, and the research. He asked for
  exactly these, so this session produces no new factory code (rule 4's exception); it changes
  `docs/roadmap.md` and its page, and records the research.
- **"All those interfaces exposed."** Read against the brief's table (one "when a person steps in"
  row per step) and against what the factory emits today: a gate from Verify only, answered by a
  file or one HTTP call, nobody notified, no way to correct an artifact and resume. The review
  lists every point, what exists, and what the roadmap has to add.
- **"That restate tool."** Restate is the durable-execution engine standing in for the role
  Temporal has in his team's backbone (track 2, 2026-10-12). Explained in plain words with what
  it measured, and the choice of keeping it is his (`docs/roadmap.md`, questions).
- **"The research report I have never seen."** It exists only in the old lab (`~/dev/assay`,
  `docs/research/`, fetched 2026-10-06 to 08) and was never carried into this repository or put
  in front of him as a report. He is told what it covers, and a short fresh pass on software
  factory and AI SDLC practice is run and recorded, each claim labelled (rule 5).

## 2026-10-14 · Discuss the roadmap and the next work items

> let's discuss roadmap and come up uth next work items for factory

How it was read ("uth" is "with"):

- He asked for a plan, so a plan is this session's output (rule 4's exception); nothing is built.
  The first item is left ready to paste as the next session's kickoff.
- The roadmap is written from the record, not from new research: what `docs/adopt.md` section 1
  says is not built, what `docs/status.md` and `docs/log.md` left open, the brief's steps that do
  not exist yet, and his input of 2026-10-13 (his microservice adopting the factory, the meetings
  at work, mocks then the deployed run as verification points), which sets the near-term order.
- Where it goes: `docs/roadmap.md`, the "Next" of `docs/status.md` pointing at it, the kickoffs in
  `docs/next-session.md`, and a page with diagrams for him to review (his request of 2026-10-08).
- What is his: which direction comes first, and what only he knows about his service and the
  tickets at work. The swappable choices (the Restate default, which public application and which
  ticket) are decided by delegation or left to the session that builds them, with criteria.

## 2026-10-13 · Wrap up for adoption by a real project; answer "how can we trust the tests"; mocks as a verification point

> For QA factory and software factory in general, because this is still software factory with the
> heavy QA slice, the way I see it, there was some work done remotely. Let's make sure everything
> is merged. This is my goal.
>
> I have meetings coming up at work where we're going to be discussing some of this stuff. What I
> would like to do is wrap up work on our end here, so factory can be taken by a more-or-less real
> project, right? I will have a little microservice on my end. I want the microservice to adopt the
> QA factory on the other end. The setup will be done by agents, so make sure we have clear
> instructions, tested instructions, and clear expectations in terms of what is ready at this
> point. The team is pushing me to answer the main question: How can we trust tests that were
> written as part of the session where a feature or bug fix was implemented? This is actually a
> thought that I wanted to drop. I am a big fan of mocks, reliable mocks. We can get reliable mocks
> these days with AI and ways to maintain them.
>
> I was thinking about doing all the development and fixes on top of mocks, and then the real run
> on the deployed environment sort of validates the true implementation. One of the mechanisms.
> More mechanisms like this, or clear acceptance criteria on the input that become our
> verification points. We need to be ready for different scenarios like that.

> Also, we need to move fast. This is all POC-mode development, so let's get shit going fast.

How it was read:

- **"Everything merged."** The remote work is the cloud session's track 2 branch, merged as pull
  request 16; pull requests 17 and 18 followed on the laptop. All 18 pull requests are merged. The
  three remote branches still on GitHub are the merged heads of 16, 17 and 18 and hold nothing
  `main` lacks (checked with `git diff` against `main`); deleting them is a chore left for him,
  because the session's permission rules refuse `git push --delete`.
- **"Wrap up so a real project can adopt it, set up by agents."** The deliverable is a written
  procedure an agent can follow on a fresh machine (`docs/adopt.md`), proved by an agent that
  follows nothing but that procedure to onboard a second real application and run one ticket
  through to Ship. The second application is isso, decided on 2026-10-08. His microservice stays
  on his side: pointing the factory at an employer repository is his call (`CLAUDE.md`,
  boundary). The guide is written for that case: a small Python service, possibly with no browser
  tests at all, which the factory required until today.
- **"Clear expectations of what is ready."** A table in `docs/adopt.md`: what is built and measured,
  what is built and not measured, what is not built.
- **"How can we trust tests written in the session that implemented the change?"** The factory's
  answer, with the four runs' numbers and the limits, in `docs/trust.md` and on a page he can
  present. The short form: the factory never trusts them; a fresh session writes the tests (blind
  when the ticket allows it), and deterministic tools decide whether they prove anything.
- **Mocks, then the deployed run.** Read as two verification points for one set of acceptance
  tests: first inside the service's own suite with its dependencies mocked, where the revert check
  and mutation testing already run; then the same cases against the deployed environment with
  the real dependencies. The first point is what the factory does today; the second is track 3,
  not built. No mock machinery is built now: which dependencies his microservice has, and what a
  mock of them should be kept from (a recorded exchange, an OpenAPI document, the dependency's own
  test double), is not known here, and rule 3 says machinery waits for a run that needs it.
  Recorded as a recommendation he can overturn (`docs/decisions.md`).
- **"Clear acceptance criteria on the input that become our verification points."** Already the
  factory's shape: Frame restates each criterion as something a test can check and names its
  surface; track 1 showed the blind lane works when the ticket states the public contract. The
  guide makes that a requirement on the ticket.
- **"Move fast, POC mode."** One session: the guide, the isso run, the trust page, the records,
  one pull request. Track 3 is not started unless the isso run leaves room.

## 2026-10-12 · From the konyklabs workspace session: use the credits on the factory, continue in the cloud, keep going

Given in a session started in the konyklabs workspace, not in this repository; filed here after
the work, not before it, which breaks this file's rule once.

> Okay, what kind of useful work can we do for those $250? One of my main topics that I want to make progress on is this factory, right? QA factory, SDC factory, software factory. Can we make some progress on that using those credits?

> Do you see we have the project already locally for this? Could you locate it, and maybe we can set up the continuation up there in the cloud?

> Yeah, hey, let's keep going.

How it was read:

- **First message:** spend the one-time cloud-session credit (250 USD, until 2026-11-05) on this
  factory.
- **Second message:** continue track 2 from this repository in a Claude Code cloud session. That
  became pull request 16. The kickoff told it to build only, make no model calls, and leave the
  merge to the laptop, because the guard's term list exists only here.
- **Third message:** a yes to running the bundles ticket for real on Restate, billed to the Max
  plan's monthly API credits through a Console API key. That became pull request 17 and the
  2026-10-12 entry in `docs/decisions.md`.

## 2026-10-10 · A check-in during the runs

> While I'm here, just wanted to check if everything is going well and if you need any help from me.

How it was read: a check-in, no new direction. Answered with the state of the runs and that
nothing was needed from him; the cost of a sequential bundles run was named as not fitting the cap.

## 2026-10-10 · Kickoff: stronger models before people, then track 1

The prompt of `docs/next-session.md`, pasted unchanged as the session's first message.

How it was read:

- Build first, inside Verify: one repair round for the test writer when lint, the revert check
  or mutation fails; then a stronger model (`claude-fable-5-1`, headless, read-only) decides
  retry, the change is wrong, an environment problem, or cannot decide; only the last stops for
  a person. One fix round when Review requests changes. Rounds and spend capped per ticket.
- Then track 1: a blind mode, the sort ticket run blind under a new id, a second ticket from
  linkding commit 573b6f5 run blind, the sequential run of it only if the cap allows.
- Judgement calls made by the session, recorded in `docs/decisions.md`: "fail back to Implement"
  is a terminal failure with the stronger model's diagnosis, because Implement is the developers'
  real commit and cannot be redone; the Review fix round runs inside the Review step; after the
  join, a repair round in blind mode runs in the head worktree with the findings but no diff.

## 2026-10-10 · Stop asking: approve, nothing at work yet, stronger models instead of questions, salvage the lab, Docker

> Of course I approve the first run's test. Why wouldn't I approve this? Why do I have to approve
> this kind of stupid question? Factory work does not run on nothing. We are also trying to figure
> out how to do this shit. That's part of the whole thing. I want to understand how to run this
> crap.
>
> Test writer is asking questions. We need the system to advise on stronger models, too. If the
> factory is going to be stopping every turn to ask fucking questions, how far is that going to
> go? Leftovers: we pick ideas and pieces from there. We have put a lot of effort into it. Can we
> at least salvage something, or was it just wasted completely? If it was wasted, what the fuck,
> then? What deployed environment are you talking about? Of course, you will be running that on a
> fucking Docker image on this local

How it was read ("Factory work does not run on nothing" is read as "the factory at work does not
run on anything yet"):

- The first run is approved. More than that: the factory must not stop to ask a person when its
  checks pass. Approving passing work is not his job.
- Nothing at work runs a factory yet; working out how to run one is part of this project. So the
  orchestrator (Restate, Temporal or the plain driver) is ours to choose from running it, and
  track 2 is a real trial of running the factory on Restate, not a spike to match work.
- When an agent is unsure or a check fails, the factory asks a stronger model for advice, not a
  person. A person is asked only when that cannot resolve it.
- The old lab is kept, and its pieces are salvaged as the factory needs them; he wants to know what
  was salvaged so far.
- Track 3 runs linkding from its Docker image on this laptop; that was never in doubt.
- Feedback on the asking itself: no questions about passing work or obvious defaults.

## 2026-10-10 · Go with the exploration plan; persist it before the context is cleared

> Yes, I want you to go with this plan persisted because I want to clear context before we kick
> it off.

How it was read: the plan in `docs/exploration.md` is approved as written: three tracks in the
recommended order, track 1 first, one session each, about 25 USD of model spend in all
(estimate). That includes track 3 as written, with linkding's own Docker image on this laptop
standing for the deployed environment. He did not answer what the factory at work runs on, so
track 2 runs as a spike behind a flag and that question stays open. Nothing starts in this
session; the next session kicks off from `docs/next-session.md`. Changed: a decision entry, the
exploration file marked approved, the kickoff prompt, status, the page.

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
