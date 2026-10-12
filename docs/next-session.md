# The next session: exploration track 3, the deployed environment

Paste this as the first message of the next session.

---

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md (its "Waiting on Oleg" list first),
docs/log.md, docs/decisions.md and docs/exploration.md. Tracks 1 and 2 are done; do not reopen
them. This session runs track 3.

**The question.** Can the factory's tests run against a deployed environment? Use case UC2: trusted
end-to-end tests that also run on the deployed app.

1. Run linkding from its own Docker image on this laptop as the deployed app. Docker runs here
   through colima. The image must be a linkding release that contains the feature under test:
   1.47.0 contains the sort ticket's change (0490013). Check which release first contains the
   bundles change (573b6f5) before using that ticket.
2. Take the readable cases of one shipped feature, for example
   `docs/runs/2026-10-10-linkding-sort-by-modified-blind/testcases/`. Turn them into a thin suite
   that takes a base URL and creates its data through linkding's REST API with a token, never
   through the database. Run that suite against the container.
3. Measure:
   - which cases pass on the deployed app;
   - what had to change from the in-suite tests, and why;
   - how long the suite takes;
   - what the container needs: the image, a superuser, a token, the data.
   Test the agent-friendly checklist in `docs/exploration.md` against what it took.
4. Record the findings in docs/exploration.md. Update the architecture page's sections 10, 14 and
   15 (`python3 docs/pages/architecture/build.py`), read
   https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa, then republish the built file to that URL.

**Billing.** Any model call goes through `scripts/with-console-key.sh`, so it bills the Console API
key and not the subscription (`docs/decisions.md`, 2026-10-12). Under Restate, start the service
under that script, not the `run` command.

**Cap:** one session, and about 5 USD of model spend (estimate). The track ends with the commands
and their output, or says plainly what did not run and why.

**Leave alone:** the finished run folders under `.artifacts/runs/` and their worktrees.

Build with Oleg's plugins as CLAUDE.md says. The supervisor skills need him to arm them
(`docs/plugin-notes.md`), so when he has not, spawn its agents directly with written specs.

- A test for every factory change.
- A branch per change, with `just check` green.
- A squash PR with the output in the body.
- A `docs/log.md` entry, and `docs/status.md` updated last.

Report to Oleg in plain English: what ran, what it showed, and what is his to decide. Never ask him
to approve passing work. What is truly his goes at the end as a short numbered list.
