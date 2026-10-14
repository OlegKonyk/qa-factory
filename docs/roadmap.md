# Roadmap

Proposed 2026-10-14 in answer to Oleg's request to discuss the roadmap (`docs/inputs.md`). The
order of the first two groups is his to choose (question 1 below); everything else is a
recommendation he can overturn. The review page is
https://claude.ai/artifact/TesENWMdg67e3p15kwiaZX (private to Oleg), built from `docs/pages/roadmap/index.html`.
Every cost here is **estimated** from the runs so far, not measured.

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

## Now: make it adoptable by a real service (recommended first)

What his microservice and the meetings at work need first (his input of 2026-10-13).

### 1. Run the tests against a running application

The second verification point of his scheme: develop on mocks, then the same cases run against
the deployed application. Already approved on 2026-10-10; kickoff B in `docs/next-session.md`.

- **Build:** linkding from its own Docker image (a release that contains the feature) on this
  laptop through colima. One shipped feature's readable cases become a thin suite that takes a base
  URL and creates its data through linkding's REST API with a token, never the database.
- **Done when:** the suite runs against the container, with the command, the pass count and the
  time; what had to change from the in-suite tests and why; the agent-friendly checklist in
  `docs/exploration.md` tested against what it took.
- **Cost:** one session, about 5 USD (estimated).

### 2. Three factory fixes the last runs found

Code only, no model calls, so it fits a cloud session paid by the one-time credit (250 USD, until
2026-11-05).

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

## Next: from the QA part to the whole factory

### 4. The factory writes the change itself

- **Build:** Implement becomes an agent that writes the change test-first from Frame and Plan.
  In parallel, a fresh session writes the acceptance tests blind (already built). They meet on
  the deterministic checks; failures go back to Implement, capped, with the stronger model before
  a person.
- **A check with a known answer:** run it on tickets already shipped (linkding's sort and bundles,
  isso's no-cache). The developers' real commit and its tests are held back from every session;
  after the join, the developers' tests run against the agent's change. That is a deterministic
  check of the agent's code, not a score.
- **Cost:** one or two sessions to build; about 10 USD per ticket to run (estimated, nothing
  measured).

### 5. Ship as a pull request, approve on it

- **Build:** Ship pushes the `qa/<ticket>` branch to a fork on his GitHub account and opens a pull
  request with the readable cases and the run report in the body. When a rule asks for a person,
  the approval is the pull request's approval. A notification when the factory waits for a
  person.
- **Cost:** one session, little model spend (estimated).

## Later: when a run shows the need

6. **Tickets from an issue tracker**, with a readiness check in Frame that sends a ticket back
   when it does not state the public contract (field names, values, labels, routes). Moves up if
   tickets at work do not state it (question 3).
7. **The Learn step**: each run's escalations, review findings and repairs proposed as edits to
   the strategy rule and the prompts, by pull request. The brief's knowledge base starts here.
8. **Scale**: more than one ticket at once, Restate as the default engine, test selection when a
   suite gets slow, quarantine for flaky tests.
9. **Applications not in Python.** The checks read pytest output and run mutmut.

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
- A dashboard beyond Restate's UI and `python -m factory report`.

## Questions for Oleg

1. **Which first:** make it adoptable by a real service (items 1 to 3), or the factory writing the
   change itself (item 4)? Recommended: adoptable first; it is what his service and the meetings
   need, and item 4 is easier to trust once item 3 has shown a bug-fix ticket.
2. **His microservice:** is it the third application at his side, and what is its shape
   (framework, database, the kind of thing it calls: another HTTP service, a queue, a third-party
   API)? Only the generic shape enters the repository; names go to `.local/`. Or should the session pick a public application
   with the shape above? Recommended: a public one here; his at work from `docs/adopt.md` when he
   chooses.
3. **Tickets at work:** will they state the public contract before coding starts? If not, item 6
   moves into Now.
