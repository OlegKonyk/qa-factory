# Brief

What the factory has to do, from Oleg's inputs (`docs/inputs.md`). Generic on purpose: raw
material stays in `.local/handoff/`. Requirements are his words; nothing below the requirements is
decided.

## The factory

A software factory based on the latest ideas in the industry, built on Temporal and run entirely
on this machine (whether Temporal runs well locally is not verified yet).

The flow, from a team diagram of the factory's backbone (2026-10-08):

| Step | What the agent does | When a person steps in |
|---|---|---|
| Ticket | Tickets are written to be agent-ready, with the help of ticket skills | A person writes or fixes the ticket |
| Frame | Turns the requirements into a solution | Acceptance criteria are ambiguous: a person clarifies them |
| Plan | Plans the change | Plan risk, or the existing patterns are unknown: a person approves or adjusts |
| Implement | Writes the change test-first | The plan missed, or the agent is stuck: a person decides, unblocks or takes over |
| Verify | Automated QA. Pass goes on; fail goes back to implement, a capped number of rounds | Too many rounds, environment problems, deviations: a person fixes or diagnoses |
| Review | Reviews the change; findings go back to implement, capped | Reviewer impasse, too many rounds, a risk gate: a person signs off |
| Ship | Merges and ships | By risk tier, a person may approve the merge |

Around the flow:

- **Every step runs in a fresh agent session**, with its artifacts kept outside the session
  (work notes, the tracker, the code host).
- **Each step has configurable deterministic and AI gates** that can stop the run and hand it to a
  named person: the run stops, the owner is notified, they answer or take over, and a fresh
  session resumes with the updated artifacts. The decision is recorded: who, why, the context.
- **A knowledge base every step can query** ("did we already record the answer?"), for the
  repository and for the organisation. Recorded decisions, human interventions and review findings
  flow into a decision store; the useful ones are promoted to a curated repository knowledge base,
  and from there to an organisation one. The promotion rules are not defined yet.

## The QA part: what it must do

From his input of 2026-10-08:

1. **Reliably generate test coverage** for API tests and Playwright (browser) tests.
2. **Validate that the tests are not misleading**: a test that passes must be checking something
   real.
3. **Produce human-readable test cases**, or some other artifact a person can read and approve.
4. **Make approved tests part of the ongoing regression suite.**
5. **Place coverage deliberately, not blindly**: decide where tests are added from a test strategy
   (the pyramid, the inverted pyramid, the honeycomb, or whatever is decided).
6. **AI generates; deterministic tools verify.** mutmut is in use and stays. GitHub Spec Kit is
   "maybe, inconsequential".

## Constraints carried from earlier inputs

These came during the lab and still stand unless he says otherwise:

- Local first: the factory has to run on this machine.
- Reputable, ready-made pieces first, with a UI on top. The UI question is for the whole factory;
  QA fits inside it.
- The stack at work is Python, pytest, Playwright, AWS.
- Users: engineers who stay in one repository, engineers who move across many (infrastructure), and
  QA engineers, who use the tooling too.

## Decided

`docs/decisions.md`, dated, newest first. Temporal is deferred until the loop runs; the ten
planning questions were decided on 2026-10-08. `docs/status.md` lists what is still open.
