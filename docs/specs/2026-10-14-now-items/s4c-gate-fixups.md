# s4c · Gate fix-ups from the reviews of s4a and s4b

Worktree: `~/dev/qa-factory-wt/gates` (branch `feat/person-gates`), on top of s4a and s4b
(committed as 5aefa37). Same hands-off list as s4a. Decisions taken by the session on the open
questions, binding:

1. **Strict answers stay.** The driver keeps refusing a decision outside the gate's accepted
   answers (exit 2, the file left in place, the message naming the accepted answers). A person
   re-answers; nothing fails silently. Keep it; no change there.
2. **`redo` records real "before" hashes (reading B).** `driver.run_step` stores
   `artifact_sha256: {artifact key: sha256 of the file}` in the record it writes when a step
   passes (files only; a missing or directory artifact is skipped). `redo` takes "before" from the
   step's record and "after" from the files as they are now; when the record has no hashes (older
   runs), "before" is `"unknown"` as today. Update the `redo` tests and add one for a record with
   hashes.
3. **The Restate answer hint** (`restate_service.answer_hint`): the curl example sends
   `{"decision": "<the gate's first accepted answer>", "by": "<who>", "note": ""}`, built from
   the gate the run waits on, so it is never refused by the driver. Test it.
4. **`waiting` names a refused answer.** When `answer.json` exists but `gates.read_answer` raises,
   the line reads `answer refused: <the error>` instead of `answer pending`. Test it.
5. **Notifications off for the live Restate test.** `gates.notify` returns at once when the
   environment variable `QA_FACTORY_NO_NOTIFY` is set to `1`; `tests/test_restate_live.py` sets it
   for the service it starts; `docs/adopt.md` section 6 names the variable in one line (for a
   headless machine or a CI job). Test the early return.
6. **An `edit` answer may point at the plan file itself.** `plan._edited` accepts a file holding
   the `{"structured": ..., "text": ..., "metrics": ...}` wrapper by unwrapping `structured`, so
   a person who edits `plan/plan.json` in place and answers `{"decision": "edit", "plan":
   "plan/plan.json", "by": ...}` is not turned away; the error message for anything else says
   both accepted forms. Test it.
7. **The escalation question text** (`verify._escalation_gate`) uses the recipe's approver
   (`gates`' default) in its example answers instead of the hardcoded name.

## Tests and evidence

Every point above has a test. Paste the last lines of `uv run --no-sync ruff check factory tests
targets`, `ruff format --check`, `pytest` and `just check` (the live Restate test must run, not
skip, and no notification may appear: say whether one did).

## Report

Files changed; commands and output; deviations with reasons; what was left alone. Do not commit.
