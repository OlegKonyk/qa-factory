# The next session: exploration track 1, the feature loop measured

Paste this as the first message of the next session.

---

Start in ~/dev/qa-factory. Read CLAUDE.md, then docs/status.md, docs/log.md, docs/decisions.md and
docs/exploration.md. The exploration plan is approved (decisions, 2026-10-10); do not reopen it.
This session builds the stronger-model escalation, then runs track 1.

**First, before track 1: stronger models before people** (decisions, 2026-10-10, "The factory
does not stop to ask when its checks pass"). Verify already approves on its own when every check
passes. Build the rest, smallest version that works, with tests:

- When lint, the revert check or mutation fails because of the generated tests, the writer gets
  the findings for one repair round in a fresh session, and the checks run again from lint.
- If a check still fails, a stronger model (`claude-fable-5-1`, headless, read-only tools) gets
  the check reports and decides one of: retry with its guidance (one more round), the tests are
  right and the change is wrong (fail back to Implement), or an environment problem (fail with its
  diagnosis). Its answer is recorded in the run folder. Only "cannot decide" stops for a person.
- When Review requests changes, the writer gets its findings for one fix round, then Verify's
  checks run again.
- Rounds and spend are capped per ticket and recorded.

**Then track 1. The question.** Can QA start as soon as the ticket is ready, in parallel with the
implementation? Measure it: acceptance tests written blind, from the ticket and the old code only,
then joined to the developers' real commit and checked by the factory's existing checks.

1. Add a blind mode to the factory, the smallest change that works (a ticket field such as
   `"qa_mode": "blind"` is one way). In blind mode Frame, Plan and the test writer run in the
   base worktree, and the writer's prompt carries the ticket and the strategy rule but no source
   diff and none of the developers' tests. The tests are then placed in the head worktree, and
   lint, the revert check, mutmut on the changed functions, linkding's suite and the readable
   cases run unchanged. Read "Notes for whoever runs the tracks" in docs/exploration.md first.
2. Run it on the sort ticket under a new id (`linkding-sort-by-modified-blind`), so the finished
   first run is left as it is. Compare with the sequential run of 2026-10-08.
3. Write the second ticket from linkding commit 573b6f5 ("Filter bundles by reading or sharing
   state", upstream pull request 1308, base is its parent), stating its public contract.
   `uv run python targets/linkding/fetch.py --ticket <ticket> --prepare-e2e`, then run it blind.
   If time and the cap allow, run it in the sequential mode as well, for the comparison.
4. Record per run, labelled measured: tests written; pass at head; fail at base on an assertion;
   missing-name and crash counts; mutants killed on the changed lines and overall; spend and time
   per stage. Put the evidence in docs/runs/ and the comparison in docs/exploration.md.
5. Update sections 13 and 14 of the architecture page with the numbers
   (`python3 docs/pages/architecture/build.py`, then republish the built file to
   https://claude.ai/artifact/6eVbvKyNdsBA7RjXkeq3wa by passing that URL; read it first).

**Cap:** about 10 USD of model spend for track 1 (estimate), plus what the escalation's tests cost, and this one session. The track ends with the
commands and their output, or says plainly what did not run and why. No other tool is scored.

**Leave alone:** the first run `.artifacts/runs/linkding-sort-by-modified/` and its worktrees; it
is finished and its tests are committed on `qa/linkding-sort-by-modified` in its head worktree.

Build with Oleg's plugins as CLAUDE.md says; the supervisor skills need him to arm them
(`docs/plugin-notes.md`), so spawn its agents directly with written specs when he has not. A test
for every factory change. Branch per change, `just check` green, squash PR with the output in the
body, a `docs/log.md` entry and `docs/status.md` last. Report to Oleg in plain English: what ran,
what it showed, and whether track 2 is ready to start. Never ask him to approve passing work; what
is truly his goes at the end as a short numbered list.
