# s4b · A gate at every step, correct as well as approve, redo

Worktree: `~/dev/qa-factory-wt/gates` (branch `feat/person-gates`), after s4a (read
`factory/gates.py` and the new `Gate` first). No model call, nothing run against an application.
Same hands-off list as s4a. The steps' gates are built on the step envelope (status `needs_person`
plus a `Gate`), so the plain driver exits with the question and Restate parks the run, both
without new engine code.

## Decisions already made (do not reopen)

- **Frame stops** (under `auto`) when any criterion has `testable: false`, or when the new schema
  field `missing_contract` is non-empty. `ambiguities` alone never stop a run: the five shipped
  tickets had 7 to 11 each (`tests/fixtures/frames/*.json`, their recorded Frame outputs) and
  must still pass. `missing_contract` lists what a test writer must know and neither the ticket
  (`contract`, `description`, criteria) nor the code before the change states: route paths, field
  names, values, labels, status codes. The prompt (`factory/prompts/frame.md`) says exactly that,
  and says to leave it empty when the ticket states the surface.
- **Plan stops** (under `auto`) when the new schema fields say `risk: "high"` or
  `unknown_patterns` is non-empty (patterns the strategy does not cover and the plan had to
  invent). The prompt explains both.
- **Review stops** (under `auto`) instead of failing when the verdict is still `request_changes`
  after the fix round, or when no writer round is left for a fix round. Under `person`, an
  approving review also stops for sign-off.
- **Ship stops** under `person` before committing. Under `auto` and `model` it commits as today.
- **Verify** keeps its two gates (s4a). Under `person` it stops for approval as today.
- **Correct, not only approve:** an answer may carry a replacement artifact; the step resumes
  with it.

## Build

1. **Frame** (`factory/steps/frame.py`, `factory/prompts/frame.md`). Schema gains
   `missing_contract: [str]`. After `one_prompt` returns, decide: mode `person`, or a criterion not
   testable, or `missing_contract` non-empty → `needs_person` with `Gate(kind="clarify", who,
   question=<what is missing, as a list>, context={"missing_contract", "untestable": [...],
   "ambiguities"}, answers=[proceed ("as read"), clarify (carries `ticket`: the fields to
   replace: any of description, contract, acceptance_criteria), decline])`. On resume with
   `proceed`: pass with the recorded Frame artifact (no new call). With `clarify`: the carried
   fields are written to `<run_dir>/ticket.clarified.json`, merged into the ticket for the rest
   of the run (see 6), and Frame runs once more on the clarified ticket; its gate rule applies
   again. With `decline`: fail. The ambiguities list stays informational.
2. **Plan** (`plan.py`, `prompts/plan.md`). Schema gains `risk: low|medium|high` and
   `unknown_patterns: [str]`. Gate `kind="plan"`, answers `approve`, `edit` (carries `plan`: a
   path to an edited plan JSON in the structured shape, or the object inline), `decline`. On
   `edit`, the plan artifact file is replaced (keep the old one as `plan.before-edit.json`) and the
   step passes with `reason` "plan edited by <by>".
3. **Review** (`review.py`). Where it fails today on `request_changes` after the fix round, or on
   no round left, raise a gate `kind="review"` with the findings in the context, answers
   `sign_off` (carries `note`) → pass with the review artifact and the note in the reason,
   `another_round` → one more fix round when a writer round is left (`verify.repair_from_review`
   then review again), else fail with the reason, `decline` → fail. Under `person`, an approve
   verdict stops with the same kind and the answers `sign_off`, `decline`. Mind the existing
   branch where Review resumes Verify's fix-round gate (`"answer" in artifacts`): the two answers
   must not be confused; use the record's `gate.kind` (read the previous `needs_person` record of
   Review from `steps/05-review.json`... the driver renames nothing on a gate, so it is there).
4. **Ship** (`ship.py`). Under `person`, before the commit: `needs_person`, `kind="ship"`, context
   with the files, the branch name, the suite that will run; answers `approve`, `decline`. On
   `approve` commit and run the suite as today; `decline` fails.
5. **`python -m factory redo <run folder> <step> --by <who> [--note ...] [--rerun]`**: for a
   passed step whose artifact a person edited by hand. Archives every later step's records as
   earlier rounds (`NN-<name>.roundK.json`, next free K) so the next `run` resumes from the step
   after it; writes `steps/NN-<step>.redo<K>.json` with who, when, note, and the sha256 of the
   step's artifact files before and after (take "before" from the record's artifacts if the
   files still exist; otherwise record "unknown"). With `--rerun` the step's own record is
   archived too, so the step runs again. Prints what it archived. Refuses a step that is not
   passed, or a run that is waiting at a gate (say what to do instead).
6. **The clarified ticket.** `driver.prepare`: after reading the ticket file, if
   `<run_dir>/ticket.clarified.json` exists, its keys replace the ticket's (description, contract,
   acceptance_criteria only; anything else in the file is an error) and the merged ticket is what
   every step receives. The original file's `caps` therefore still win on re-runs (another branch
   depends on that). Write the merged ticket to `<run_dir>/ticket.json` as the record.
7. **`docs/adopt.md`**: section 5 the new ticket fields; section 6 a short table of the gates
   (step, when it stops under `auto`, the answers and what each carries), `redo`, the clarified
   ticket; section 7 unchanged.

## Tests and evidence

- Replay: `tests/test_frame_gate.py` loads every `tests/fixtures/frames/*.json` as a canned Frame
  result and asserts the step passes under `auto`; one fixture edited to `testable: false`, one
  with `missing_contract` filled, each stops with `kind: "clarify"`; `person` stops on a clean
  frame; the `proceed`, `clarify` (Frame called again, the clarified file written, the merged
  ticket reaches the next step through the driver) and `decline` answers.
- Plan: stops on `risk: high` and on `unknown_patterns`; `edit` with a path and inline; `approve`.
- Review: the `request_changes` after the fix round stops instead of failing; `sign_off`,
  `another_round` with and without a round left, `decline`; Verify's fix-round gate still works
  (`tests/test_prompt_steps.py` has the fakes).
- Ship: `person` stops before any commit (no `qa/` branch in the tmp repo), `approve` commits,
  `decline` fails (`tests/test_ship.py`).
- `redo`: archives later records, writes the redo record, `--rerun`, refuses the wrong states.
- `tests/test_driver.py`: the clarified ticket merges, rejects a foreign key, keeps `caps`.
- Every existing test passes. Paste the last lines of `ruff check`, `ruff format --check`, `pytest`.

## Report

Files changed; commands and output; deviations with reasons; what was left alone. Do not commit.
