# s4a · One gate contract, per-step configuration, told, listed, recorded

Worktree: `~/dev/qa-factory-wt/gates` (branch `feat/person-gates`). Work only there; run tools
with `uv run --no-sync ...`. No model call, nothing run against an application.

Read first: `docs/roadmap.md` (the table "Where a person steps in" and item 4), `docs/brief.md`
(the steps table), `docs/decisions.md` 2026-10-10 "stronger models before people" (a question can
never approve failing work; passing work never waits for a person unless a rule asks), then
`factory/envelope.py`, `factory/driver.py` (`run_step`, `_write_question`), `factory/steps/verify.py`
(`_escalation_gate`, `_approve`, `_answer`: the two gates that exist), `factory/restate_service.py`
(how a gate parks the workflow and `write_answer`), `factory/report.py`.

**Hands off:** `verify.run_mutation`, `factory/checks/mutants.py`, `factory/checks/devtests.py`
(another branch changes them; a rebase must stay clean). In `verify.py` change only what the gate
dicts and the answer reading need.

## Decisions already made (do not reopen)

- **Modes per step:** `auto` (the step stops only when its own rule says so), `model` (a stronger
  model decides before a person; built for Verify only, elsewhere the same as `auto` for now, and
  the code says so where it reads the mode), `person` (the step always stops at its end for a
  person). Defaults: `verify: model`, every other step `auto`. Today's single `gate: "person"`
  field in a ticket or recipe means `gates.verify: person` and keeps working.
- **Precedence:** the ticket's `gates.<step>` over the recipe's `gates.<step>` over the default.
- **Answer file:** `answer.json` beside `question.md`, as today. `by` is required; an answer
  without it is not consumed: the driver prints what is missing and exits 2. `decision` is one of
  the gate's accepted answers; `note` optional. Verify's old form `{"approved": true|false}` stays
  accepted (`approve`/`decline`).
- **Who is asked:** `who` stays a free string; the recipe may set `"approver": "<name>"`, default
  `"Oleg"` as today.

## Build

1. **The contract.** `envelope.Gate` gains `kind: str` (one word naming the gate, e.g.
   `approval`, `escalation`; later slices add `clarify`, `plan`, `review`, `ship`) and
   `answers: list[dict]`, each `{"decision": "<word>", "means": "<one sentence>",
   "carries": "<optional: the extra field the answer may carry, e.g. 'ticket', 'plan',
   'guidance'>"}`. `from_dict` reads old records (no `kind`: `"approval"`; no `answers`: `[]`).
   `to_dict` writes both. `_write_question` renders kind, who, question, the accepted answers with
   their meaning, and a ready-to-edit example answer with `"by"`.
2. **`factory/gates.py`** (new): `mode_for(step, ticket, app) -> str` (with the legacy `gate`
   field), `read_answer(path) -> dict` (raises `AnswerError` naming the missing or unknown field;
   maps `approved` to a decision), `notify(run_dir, step, gate, ticket, app, *, runner=subprocess.run,
   post=<urllib opener>)`, `waiting(runs_root) -> list[dict]`. Every function takes its
   collaborators as arguments so the tests inject fakes.
3. **Verify adopts it, behaviour unchanged.** `_approve`'s gate: `kind: "approval"`, answers
   `approve`, `decline`. `_escalation_gate`'s: `kind: "escalation"`, answers `retry` (carries
   `guidance`), `recheck` (carries `round`), `change_is_wrong`, `environment`, `fail` (any other
   decision keeps failing the step as today, so old answers still work). `_answer` reads the
   answer through `gates.read_answer`. `_approve` reads the mode through `gates.mode_for`:
   `person` stops as today; `auto` and `model` approve as today.
4. **The driver.** `run_step`: before running a step with an answer, `gates.read_answer`; on
   `AnswerError` print `answer: <what is wrong>` and the question path, return the old output
   (exit 2 follows). After a step returns `needs_person`, call `gates.notify` (never let it fail
   the run: catch, print one line). The Restate path shares `run_step`, so it gets both; check
   `restate_service.write_answer` still fits and that `answer_hint` mentions `by`.
5. **Told.** `notify`: on macOS with `osascript` on PATH, `display notification "<question, cut
   to 200 chars>" with title "qa-factory: <ticket id> waits at <step>"`; when the recipe or the
   ticket has `notify_url`, POST `{"ticket": id, "step": name, "kind": ..., "who": ..., "question":
   ..., "run_dir": ..., "question_path": ...}` as JSON with a 5 s timeout. Both best effort.
6. **Listed.** `python -m factory waiting [--runs-root <dir>] [--json]`: every run folder under
   the root whose latest record of some step is `needs_person` and has no `answer.json` yet
   (`steps/NN-<step>.json` with that status; `.roundN` and `.answerN` files are history), one line
   each: ticket id, step, kind, who, since (the record's `finished`), the question's first 100
   chars, the question path. Runs with an `answer.json` waiting to be consumed are listed with
   "answer pending". Nothing waiting prints "nothing is waiting".
7. **Recorded.** The driver already archives a consumed answer as `steps/NN-<step>.answerM.json`.
   `report.py`: a section "Who answered" listing every archived answer: step, round, `by`,
   decision, note, and the time (the answer file has no time: add `"answered_at"` when the driver
   archives it, as a wrapper `{"answered_at": ..., "answer": {...}}` or a field added to the copy;
   keep the original answer's keys intact). `python -m factory status` prints the answerer on the
   step's line when there is one.
8. **`docs/adopt.md`**: section 4 (recipe fields: `gates`, `approver`, `notify_url`), section 5
   (the ticket's `gates`; `gate` still accepted), section 6 (the answer file's required `by`, the
   `waiting` command, the notification). Keep the guide's voice.

## Tests and evidence

- `tests/test_gates.py` (new): `mode_for` precedence and the legacy field; `read_answer` (missing
  `by`, unknown decision, `approved` mapping); `notify` with a fake runner and a fake poster (one
  call each, the payload, nothing raised when either fails); `waiting` over a tmp runs root with a
  waiting run, a run with a pending answer, a finished run, a run with only history files.
- `tests/test_driver.py`: an answer without `by` is refused and left in place; a gate triggers the
  notifier (inject through a module attribute or a parameter); the archived answer carries
  `answered_at`.
- `tests/test_verify_step.py`: the two gates carry `kind` and `answers`; the old `approved`
  answer still passes; `{"decision": "approve", "by": ...}` passes too.
- `tests/test_report.py`: the "Who answered" section.
- Every existing test still passes. Paste the last lines of `ruff check`, `ruff format --check`
  and `pytest`.

## Report

Files changed; commands and output; deviations with reasons; what was left alone. Do not commit.
