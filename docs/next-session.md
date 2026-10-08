# The next session: build the first end-to-end path

Paste this as the first message of the next session.

---

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md, docs/decisions.md and
docs/reference/lab.md. Everything below is decided; do not reopen it.

Build the first end-to-end path and run it on linkding. Rule 3: one working path before any
supporting machinery. Rule 4: the session ends with the command and its output.

The path, on a plain Python driver (no Temporal):

1. Fetch linkding the way the old lab did (`targets/linkding/`, branch `feat/coverage-material`
   in ~/dev/assay; copy the fetch script if it is the shortest route) and pick one real 2026
   feature with the developers' own tests. Its description becomes the ticket.
2. The driver: a loop over the seven steps, one run folder per ticket, one JSON record per step,
   stop on `needs_person`, resume on re-run from the last finished step. The step contract is in
   docs/decisions.md, item 1 of the delegated decisions; keep it that small.
3. Frame, Plan, Review and Ship are one-prompt steps. Implement is the developers' real commit
   applied as the change.
4. Verify, built fully: Claude Code headless in a fresh session writes pytest API tests and
   Playwright browser tests for the feature, placed by the per-application strategy rule; then
   lint, the revert check with the failure sorter, mutmut 3.8 on the changed functions, and
   linkding's own suite, in that order, each able to fail the run; then readable test cases in
   the signoff format beside the tests; then the driver stops with a question for Oleg.
5. In this first path the answer is a file in the run folder (decision 4's fallback): the driver
   stops with a question file, Oleg writes the answer file, the re-run resumes, merges the tests
   into linkding's test folders, and runs its suite green. The pull-request answer comes once
   linkding is forked under his account; do not fork in this session.

Copy from the old lab only when the step in front of you needs it: the mutation wrapper, the
revert check and lint, the failure sorter, the headless runner, the feature descriptions. Read
docs/reference/lab.md for where they are and which have failing tests. Never resume the lab's
plans.

Measure and record: the spend per step, the time per check, the mutation score on the changed
functions, and whether the plugins (signoff, py-testing) run headless inside a step. Label every
number measured or estimated.

Branch `feat/first-path`, `just check` green, squash PR with the output in the body. Update
docs/status.md last. Report to Oleg in plain English: what ran, what it showed, what is his to
decide.
