# Roadmap

Proposed 2026-10-14 in answer to Oleg's request to discuss the roadmap, and revised the same day
after his review (`docs/inputs.md`, both entries). The order of the first two groups is his to
choose (question 1 below); everything else is a recommendation he can overturn. The review page
is built from `docs/pages/roadmap/index.html`; its current link is in `docs/status.md`. Every
cost here is **estimated** from the runs so far, not measured.

## Where the factory is

The QA part runs end to end on two real applications. A ticket goes through Frame, Plan,
Implement, Verify, Review and Ship; five tickets have shipped (four on linkding, one on isso).
Tests are written by a fresh session, blind when the ticket allows it, and kept only when the
revert check and mutation testing say they prove the change. An agent onboarded isso from
`docs/adopt.md` alone. The team's question, how generated tests can be trusted, has a written
answer with numbers (`docs/trust.md`). What is not built is listed in `docs/adopt.md`, section 1.

Of the brief's seven steps, two are not the factory's own yet: the ticket is a JSON file written
by hand, and Implement is the developers' finished commit, not an agent's change. Ship stops at a
local commit.

## Where a person steps in: what the brief asks, what exists

The brief (`docs/brief.md`) names a person point per step. Oleg's review of 2026-10-14 asks that
every one of them is exposed: a run stops there when a rule says so, the person is told, they
approve or correct, and the run goes on with the record of who answered what. The published
practice of 2026 puts a person at the same two fixed gates, specification and merge
(`docs/research/2026-10-14-factory-landscape.md`, point 1), which are the two the factory lacks.

| Step | The brief: when a person steps in | Today | How it is exposed |
|---|---|---|---|
| Ticket | writes or fixes the ticket | a JSON file by hand; nothing sends one back | not at all (item 7) |
| Frame | criteria are ambiguous: clarifies them | Frame lists the ambiguities in its output and goes on | not at all |
| Plan | plan risk or unknown patterns: approves or adjusts | one prompt, no stop; a plan cannot be edited and resumed | not at all |
| Implement | plan missed or agent stuck: decides, unblocks, takes over | the developers' commit; nothing to stop for | waits for item 5 |
| Verify | too many rounds, environment, deviations: fixes or diagnoses | **built:** one gate when the stronger model cannot decide (answers: retry with guidance, recheck a round, fail with a note); one gate when a ticket or app sets `gate: person` (answer: approve) | `question.md` out, `answer.json` in; one HTTP call under Restate; nobody notified |
| Review | impasse, too many rounds, a risk gate: signs off | one fix round, then the step fails | not at all |
| Ship | by risk tier, approves the merge | a local commit | not at all (item 6) |

What is missing in one line: four of the seven points never stop; the person can approve or
refuse but never correct an artifact and resume; nobody is told when a run waits; and nothing
lists the runs that wait. Item 4 closes that.

## Now: make it adoptable by a real service (recommended first)

What his microservice and the meetings at work need first (his input of 2026-10-13).

### 1. Run the tests against a running application

The second verification point of his scheme: develop on mocks, then the same cases run against
the deployed application. Already approved on 2026-10-10; kickoff A in `docs/next-session.md`.

- **Build:** linkding from its own Docker image (a release that contains the feature) on this
  laptop through colima. One shipped feature's readable cases become a thin suite that takes a base
  URL and creates its data through linkding's REST API with a token, never the database.
- **Done when:** the suite runs against the container, with the command, the pass count and the
  time; what had to change from the in-suite tests and why; the agent-friendly checklist in
  `docs/exploration.md` tested against what it took.
- **Cost:** one session, about 5 USD (estimated).

### 2. Three factory fixes the last runs found

Code only, no model calls, so it fits a cloud session paid by the one-time credit (250 USD, until
2026-11-05). Kickoff B.

- **Mutation where mutmut makes no mutants.** The factory skips every `__init__.py`
  (`factory/steps/verify.py`), and mutmut 3.8.0 makes no mutant for most decorated functions
  (isso, 2026-10-13). Fix both, or replace the tool for that case if it cannot be fixed; decided
  when built.
- **Resume Verify after the spend cap.** When Verify stops at its cap after the checks passed, a
  re-run discards the passing tests and pays a fresh writer (about 4 USD, estimated from the
  bundles run). It should resume at the readable cases.
- **The developers' tests check also judges tests the change modified**, not only tests new at
  head.
- **Done when:** each has a factory test, and the isso ticket's checks, run again on its shipped
  tests with no writer call, report mutants for the changed code.
- **Cost:** one cloud session, no model spend.

### 3. A third application shaped like a small team service

Kickoff C.

- **The shape:** a web API service (FastAPI or similar), a `src/` layout, a database run in
  Docker, and at least one outside HTTP service it calls. Each of those is something linkding and
  isso do not have and his microservice probably does. Either his service (his call, question 2)
  or a public application with that shape, chosen by the session that onboards it.
- **The ticket:** a bug fix this time. All five tickets so far are features; the team's question
  says "a feature or a bug fix".
- **Mocks:** the outside service is mocked in the application's suite and real (or the
  application's own fake) in the deployed run, so the mock verification point becomes concrete.
  Mock machinery is built only if this run needs it (rule 3).
- **Done when:** onboarded by `docs/adopt.md` alone, one ticket shipped, every place the guide was
  wrong folded back in.
- **Cost:** one session, about 6 USD (estimated).

### 4. Every person point exposed

Added 2026-10-14 from his review. Built on the step envelope (status `needs_person` with a gate),
so both engines get it; the plain driver keeps exiting with the question, Restate keeps parking
the run. Kickoff D. Code with factory tests and one cheap proof run.

- **One gate contract for every step.** The gate carries its kind, who answers, the question,
  the context, and the answers it accepts, so a command or a page can render it without knowing
  the step. The triggers, from the brief:
  - Frame: a criterion it cannot make checkable stops the run with the ambiguities it already
    lists; the answer is the clarified criteria, or "proceed as read".
  - Plan: `plan` set to `person` in the ticket or app, or the plan reporting unknown patterns or
    risk; the answer is approve, or an edited plan file.
  - Verify: as today.
  - Review: still `request_changes` after the fix round, or a risk rule; the answer is sign off
    with a note, or send the findings back for one more round.
  - Ship: `ship` set to `person`; the answer approves the commit (the merge, once item 6 opens a
    pull request).
  - Implement: when item 5 makes it an agent's change.
- **Correct, not only approve.** An answer may carry a replacement artifact (a clarified
  criterion, an edited plan, a test case to drop); the step resumes with it. A command reopens a
  passed step after a person edits its artifact, archiving the later records, so a correction
  made after the fact runs through again without a fresh ticket.
- **Configured per step, not one flag.** `gates` in the app recipe or the ticket, per step:
  `auto`, `model` (the stronger model decides first, as Verify does today) or `person`. Replaces
  today's single `gate` field.
- **Told, listed, recorded.** A notification when a run stops for a person (a system
  notification on this laptop; a webhook URL in the recipe for anything else). A command that
  lists every run waiting with its question, which also answers Restate's list view showing a
  parked run as "Running". The answer file requires `by`; the run report shows who answered
  what, when, and the note.
- **Done when:** every gate has a factory test with a fake runner; a ticket with a deliberately
  vague criterion stops at Frame, is answered with the clarification, and runs through (Frame
  and Plan cost about 0.10 USD together, measured on the first run); the listing shows it while
  it waits; the run report names the answerer.
- **Cost:** one cloud session to build, no model spend; one short laptop run to prove, about
  1 USD (estimated).

## Next: from the QA part to the whole factory

### 5. The factory writes the change itself

- **Build:** Implement becomes an agent that writes the change test-first from Frame and Plan.
  In parallel, a fresh session writes the acceptance tests blind (already built). They meet on
  the deterministic checks; failures go back to Implement, capped, with the stronger model before
  a person. The Implement gate of item 4 is built here.
- **A check with a known answer:** run it on tickets already shipped (linkding's sort and bundles,
  isso's no-cache). The developers' real commit and its tests are held back from every session;
  after the join, the developers' tests run against the agent's change. That is a deterministic
  check of the agent's code, not a score.
- **Cost:** one or two sessions to build; about 10 USD per ticket to run (estimated, nothing
  measured).

### 6. Ship as a pull request, approve on it

The merge gate, which the published practice treats as the one fixed human gate besides the
specification (`docs/research/2026-10-14-factory-landscape.md`, points 1 and 4).

- **Build:** Ship pushes the `qa/<ticket>` branch to a fork on his GitHub account and opens a pull
  request with the readable cases and the run report in the body. When the Ship gate asks for a
  person, the approval is the pull request's approval; the answer file stays the fallback. The
  notification of item 4 carries the pull request's link.
- **Cost:** one session, little model spend (estimated).

## Later: when a run shows the need

7. **Tickets from an issue tracker**, with a readiness check in Frame that sends a ticket back
   when it does not state the public contract (field names, values, labels, routes). Moves up if
   tickets at work do not state it (question 3). The Ticket person point of the brief is this.
8. **The Learn step**: each run's escalations, review findings, answers at the gates and repairs
   proposed as edits to the strategy rule and the prompts, by pull request. The brief's knowledge
   base starts here. A repair round guided by surviving mutants (the adversarial loop of the
   research, point 5) is a candidate here.
9. **Scale**: more than one ticket at once, a durable engine as the default (Restate, or Temporal
   if that is what work runs on; question 4), test selection when a suite gets slow, quarantine
   for flaky tests.
10. **Applications not in Python.** The checks read pytest output and run mutmut.

## Restate: what it is and whether it is needed

In one paragraph, for the review of 2026-10-14. Restate is a durable-execution engine: one
server binary that keeps a journal of every step a workflow takes, so a crashed run resumes at
the step it was in, and a run that waits for a person parks at no cost and wakes on one HTTP
call. It stands in for the role Temporal has in his team's backbone; it was chosen for track 2
on 2026-10-10 because it is one process and one install, where Temporal is several processes
and a database, and the harness his team saw is still experimental (research, point 3). On the
laptop it ran one real ticket end to end, survived `kill -9` mid-Verify, and showed a page per
run; it does not show the QA evidence (the run report does), its list view shows a parked run as
"Running", and it ignores SIGTERM (all measured, `docs/exploration.md`, "Track 2 results"). It
holds about 250 lines of service code and 400 of tests, one dependency, and one more process
pair to keep running. The plain driver gives the same result by exiting and being re-run.

**Is it needed?** Not for one ticket at a time on one laptop; that is why it stays behind
`--engine restate`. It becomes worth its process pair when runs wait for people for days and
there are several of them at once, which is what item 4 creates and item 9 scales. Recommended:
keep it behind the flag, build item 4 on the envelope so both engines get every gate, and decide
the default engine when item 6 puts approvals on pull requests. Removing it is a one-session
chore that is cheap now and cheap later. His call, question 4.

## Small leftovers, taken when a session is in that code

Carried from the old "Next" of `docs/status.md`; none needs a session of its own.

- The plan step proposes test file names the writer must ignore (fixed by prompt; worth a field in
  its schema).
- Review's low findings (random titles in an API fixture) could feed the writer one more round.
- The writer's placement of form tests in the API file follows the strategy rule loosely.
- A stronger-model call can still overshoot what is left of the ticket's cap; it cannot start
  below 1.50 USD.
- The raw writer transcript stays on this machine because it holds the machine's hook output.
- The sequential run of the bundles ticket was never done (its cap); not planned.

## Left off on purpose

- Comparing writer models to cut the cost per ticket (rule 2; about 5.5 USD a ticket, measured).
- Mock machinery before a service with a real outside dependency needs it (rule 3).
- A dashboard beyond Restate's UI, `python -m factory report` and the gate listing of item 4.
- A protocol language for the process, GitHub Agent HQ, Claude Code routines and the Temporal
  harness: recorded with dates in the research so nobody looks them up again; none is needed for
  the next step.

## Questions for Oleg

1. **Which first:** make it adoptable by a real service (items 1 to 4), or the factory writing the
   change itself (item 5)? Recommended: adoptable first; it is what his service and the meetings
   need, and item 5 is easier to trust once item 3 has shown a bug-fix ticket.
2. **His microservice:** is it the third application at his side, and what is its shape
   (framework, database, the kind of thing it calls: another HTTP service, a queue, a third-party
   API)? Only the generic shape enters the repository; names go to `.local/`. Or should the session
   pick a public application with the shape above? Recommended: a public one here; his at work
   from `docs/adopt.md` when he chooses.
3. **Tickets at work:** will they state the public contract before coding starts? If not, item 7
   moves into Now.
4. **Restate:** keep it behind the flag until item 6 (recommended), or remove it now?
