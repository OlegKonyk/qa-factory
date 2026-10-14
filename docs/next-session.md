# The next session

Paste one of these as the first message of the next session. They follow the order of
`docs/roadmap.md` (items 1, 2 and 3); if Oleg puts an agent writing the change first (question 1
there), the kickoff for that is written then. B runs in a cloud session and can run beside A or C.

## A. Run the tests against a running application (roadmap item 1)

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md (its "Waiting on Oleg" list first),
docs/log.md, docs/decisions.md and docs/exploration.md. Tracks 1 and 2 are done; do not reopen
them. This session runs track 3, item 1 of docs/roadmap.md.

**The question.** Can the factory's tests run against a deployed environment? Use case UC2: trusted
end-to-end tests that also run on the deployed app. This is the second verification point of the
scheme in docs/trust.md (develop on mocks, validate on the deployed environment).

1. Run linkding from its own Docker image on this laptop as the deployed app. Docker runs here
   through colima. The image must be a linkding release that contains the feature under test:
   1.47.0 contains the sort ticket's change (0490013). Check which release first contains the
   bundles change (573b6f5) before using that ticket.
2. Take the readable cases of one shipped feature, for example
   `docs/runs/2026-10-10-linkding-sort-by-modified-blind/testcases/`. Turn them into a thin suite
   that takes a base URL and creates its data through linkding's REST API with a token, never
   through the database. Run that suite against the container.
3. Measure: which cases pass on the deployed app; what had to change from the in-suite tests, and
   why; how long the suite takes; what the container needs (the image, a superuser, a token, the
   data). Test the agent-friendly checklist in `docs/exploration.md` against what it took.
4. Record the findings in docs/exploration.md and docs/trust.md (the second verification point).
   Update the architecture page's sections 10, 14 and 15 (`python3 docs/pages/architecture/build.py`),
   read https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa, then republish the built file to that URL.

**Billing.** Any model call goes through `scripts/with-console-key.sh`. Under Restate, start the
service under that script, not the `run` command.

**Cap:** one session, about 5 USD of model spend (estimate). The track ends with the commands and
their output, or says plainly what did not run and why.

**Leave alone:** the finished run folders under `.artifacts/runs/` and their worktrees.

- A test for every factory change.
- A branch per change, with `just check` green.
- A squash PR with the output in the body.
- A `docs/log.md` entry, and `docs/status.md` updated last.

Report to Oleg in plain English: what ran, what it showed, and what is his to decide. Never ask him
to approve passing work. What is truly his goes at the end as a short numbered list.

## B. Three factory fixes, in a cloud session (roadmap item 2)

Start in the qa-factory repository. Read CLAUDE.md, then docs/roadmap.md (item 2),
docs/status.md and the 2026-10-13 entry of docs/log.md. Build only: no model calls, no
applications cloned, nothing run against linkding or isso. Oleg's plugins are not loaded in a
cloud session; write a spec per slice and use a general-purpose subagent where delegation helps.

1. **Mutation where mutmut makes no mutants.** The factory skips every `__init__.py`
   (`factory/steps/verify.py`, the filter on changed files), and mutmut 3.8.0 makes no mutant for
   most decorated functions or a decorator with an inner function (isso 7e91d59). Mutate non-empty
   `__init__.py` files; for decorated functions, find what mutmut 3.8.0 can do, from its source and
   documentation, and fix it, or replace the tool for that case if it cannot be fixed. Record the
   choice in docs/decisions.md.
2. **Resume Verify after the spend cap.** When Verify stops at its cap after every check passed,
   a re-run must keep the passing tests and continue at the readable cases, not start a fresh
   writer round (`factory/rounds.py`, `factory/steps/verify.py`).
3. **The developers' tests check judges modified tests too**, not only tests new at head
   (`factory/checks/devtests.py`).

A factory test for each fix; `just check` green. Push the branch and open the pull request; do
not merge it. The laptop session that merges it rescans it with the guard's term list (which
exists only on the laptop) and runs isso's mutation check again on its shipped tests, with no
writer call, to show mutants for the changed code.

## C. A third application shaped like a small team service (roadmap item 3)

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/adopt.md. That guide is the whole procedure;
docs/status.md says what exists and docs/trust.md what the factory claims. Onboard <application>
by following docs/adopt.md and nothing else, through all eight items of its checklist (section 8),
with the model calls billed through `scripts/with-console-key.sh` on this laptop (elsewhere,
`ANTHROPIC_API_KEY`). Cap: one ticket, about 6 USD (estimate). Fold every place the guide was wrong
or silent back into docs/adopt.md in the same pull request. A branch per change, `just check`
green, a squash PR with the output in the body, a docs/log.md entry, docs/status.md updated last.

Pointing the factory at a work repository is Oleg's call (CLAUDE.md, boundary). If the application
is his, he says so in this prompt; otherwise pick a public one with the shape of roadmap item 3:
a web API service (FastAPI or similar), a `src/` layout, a database run in Docker, and at least
one outside HTTP service it calls. Its ticket is a bug fix from the application's own history,
written blind. The outside service is mocked inside the application's suite; build mock machinery
only if this run needs it, and record what keeping the mock reliable took.
