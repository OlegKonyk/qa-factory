# The next session

Paste one of these as the first message of the next session.

## A. Onboard a new application (the adoption path)

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/adopt.md. That guide is the whole procedure;
docs/status.md says what exists and docs/trust.md what the factory claims. Onboard <application>
by following docs/adopt.md and nothing else, through all eight items of its checklist (section 8),
with the model calls billed through `scripts/with-console-key.sh` on this laptop (elsewhere,
`ANTHROPIC_API_KEY`). Cap: one ticket, about 6 USD (estimate). Fold every place the guide was wrong
or silent back into docs/adopt.md in the same pull request. A branch per change, `just check`
green, a squash PR with the output in the body, a docs/log.md entry, docs/status.md updated last.

Pointing the factory at a work repository is Oleg's call (CLAUDE.md, boundary). If the application
is his, he says so in this prompt; otherwise pick a public one.

## B. Track 3, the deployed environment

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md (its "Waiting on Oleg" list first),
docs/log.md, docs/decisions.md and docs/exploration.md. Tracks 1 and 2 are done; do not reopen
them. This session runs track 3.

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
