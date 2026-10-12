# The next session: track 2's laptop half, a real ticket on Restate

Paste this as the first message of the next session, on the laptop.

---

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md (its "Waiting on Oleg" list first,
then "Next, on the laptop"), docs/log.md (the 2026-10-12 entry), docs/decisions.md and
docs/exploration.md ("Track 2, the build half"). The exploration plan is approved, track 1 is done,
and track 2's build half was done in a cloud session on 2026-10-12; do not reopen any of them. This
session runs the rest of track 2.

**The question.** Is Restate worth running the factory on? The service, its tests and a stub proof
exist; what is missing is a real ticket under it, watched in the UI. The plain driver stays the
default until this run proves Restate out.

1. Step 0 of "Next, on the laptop": rescan the cloud branch `claude/restate-driver-k4pqfg` with the
   real term list, run `just check`, and merge its pull request. Nothing else starts before that.
2. Steps 1 to 3 there: Restate from Homebrew, the service with the real steps, the real ticket (the
   bundles ticket again as `bundle-filters-blind-2` if Oleg said yes to question 2, otherwise a third
   linkding ticket), the screenshots, resume after a kill (during a cheap step), the timeouts, the
   report.
3. Step 4 there: the results in docs/exploration.md, the architecture page's sections 12 and 14,
   and its republish.

**Cap:** one session, and the model spend of the one ticket run (about 5.5 USD, estimate). The track
ends with the commands and their output, or says plainly what did not run and why. Restate is
assessed by name, which rule 2 allows; no other tool is scored.

**Leave alone:** the finished runs `.artifacts/runs/linkding-sort-by-modified/`,
`.artifacts/runs/linkding-sort-by-modified-blind/` and the stopped
`.artifacts/runs/linkding-bundle-filters-blind/`, and their worktrees.

Build with Oleg's plugins as CLAUDE.md says. A test for every factory change. Branch per change,
`just check` green, squash PR with the output in the body, a `docs/log.md` entry and
`docs/status.md` last. Report to Oleg in plain English: what ran, what it showed, and whether
track 3 is ready to start. Never ask him to approve passing work; what is truly his goes at the end
as a short numbered list.
