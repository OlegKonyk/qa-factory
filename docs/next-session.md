# The next session: exploration track 2, watching the factory run

Paste this as the first message of the next session.

---

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md (its "Waiting on Oleg" list first),
docs/log.md, docs/decisions.md and docs/exploration.md. The exploration plan is approved and track 1
is done (docs/exploration.md, "Track 1 results"); do not reopen either. This session runs track 2.

**The question.** Is Restate worth running the factory on? Nothing at work runs a factory yet, so
this is a real trial, not a spike to match something (decisions, 2026-10-10). The plain driver
stays the default until Restate proves out.

1. Read "Restate, from its documentation" and "Notes for whoever runs the tracks" in
   docs/exploration.md. Install the server (`brew install restatedev/tap/restate-server`) and the
   Python SDK into the factory's dev dependencies.
2. Build the smallest factory service that works, behind a flag, beside `factory/driver.py`: one
   Restate workflow per ticket, each of the six steps a durable step calling the existing step
   function, the person-gate (when a ticket sets `"gate": "person"`, or Verify's escalation
   question) as a durable promise resolved by an HTTP call. Raise the inactivity and abort timeouts
   to fit a Verify of about 15 minutes. Tests for every factory change.
3. Run a real ticket through it and measure: what the UI at localhost:9070 shows for a running
   step and for a run waiting at a gate (screenshots), resume after killing the service mid-step,
   and the timeouts. If Oleg answered yes to question 2 in docs/status.md, the bundles ticket is
   the run to watch: its Verify starts over from a fresh blind writer, so give it a new id (for
   example `linkding-bundle-filters-blind-2`, its own worktrees by `fetch.py --ticket <t>
   --prepare-e2e`) and keep the stopped run as evidence; otherwise write a third ticket from
   linkding's 2026 history.
4. A run report of our own, generated from the run folder (tests, readable cases, revert
   verdicts, surviving mutants, rounds, spend): the QA evidence Restate does not show.
   `python -m factory summary` already computes the numbers.
5. Record the findings in docs/exploration.md and update the architecture page's section 12 and
   14 (`python3 docs/pages/architecture/build.py`, then republish the built file to
   https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa by passing that URL; read it first).

**Cap:** one session, and the model spend of the one ticket run (about 5 USD, estimate). The track
ends with the commands and their output, or says plainly what did not run and why. Restate is
assessed by name, which rule 2 allows; no other tool is scored.

**Leave alone:** the finished runs `.artifacts/runs/linkding-sort-by-modified/` and
`.artifacts/runs/linkding-sort-by-modified-blind/` and their worktrees.

Build with Oleg's plugins as CLAUDE.md says; the supervisor skills need him to arm them
(`docs/plugin-notes.md`), so spawn its agents directly with written specs when he has not. A test
for every factory change. Branch per change, `just check` green, squash PR with the output in the
body, a `docs/log.md` entry and `docs/status.md` last. Report to Oleg in plain English: what ran,
what it showed, and whether track 3 is ready to start. Never ask him to approve passing work; what
is truly his goes at the end as a short numbered list.
