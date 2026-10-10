# Slice A: the step contract and the driver

Files: factory/envelope.py, factory/driver.py, factory/__main__.py, tests/test_driver.py.

## envelope.py
Dataclasses `Gate(who, question, context: dict)`, `StepInput(ticket, repo, artifacts, round, run_dir)`,
`StepOutput(status, artifacts, reason="", gate=None, metrics=dict)` and
`StepRecord(step, index, status, input, output, started, finished, duration_s)`, each with
`to_dict()` and `from_dict()`; `status` is one of "pass", "fail", "needs_person" (validate in
__post_init__). ISO-8601 timestamps. Keep it small.

## driver.py
`STEP_NAMES = ["frame", "plan", "implement", "verify", "review", "ship"]`.
`load_steps()` imports `factory.steps.<name>` lazily and returns {name: module.run}; a missing
module raises a clear error naming the step.
`run(ticket_path, runs_root=".artifacts/runs", steps=None, out=sys.stdout) -> int`:
- Reads the ticket JSON; resolves `ticket["app"]` relative to the repository root (the directory
  holding pyproject.toml, found from this file); loads the app recipe; expands `~` in its path
  values; computes base_tree = <worktrees>/base, head_tree = <worktrees>/head.
- Creates `<runs_root>/<ticket id>/` and `steps/`, writes `ticket.json` there if absent.
- Walks STEP_NAMES in order with index 1..6; record path `steps/0N-<name>.json`.
  - record exists, status pass: skip, print `skip  N name`, merge its output artifacts into the
    accumulated artifacts.
  - record exists, status needs_person: if `<run_dir>/answer.json` exists, re-run the step with
    `artifacts["answer"] = that path`; otherwise print the question and return 2.
  - record exists, status fail, or no record: run the step. `round` = 1 + number of earlier
    records for this step that failed (keep them as `steps/0N-<name>.round<k>.json` when a new
    record replaces an old one).
  - Running: StepInput(ticket, repo, dict(accumulated artifacts), round, run_dir); call; any
    exception becomes a fail output with reason = the exception's class and message (last 500
    chars of the traceback in metrics["traceback"]). Write the record. Print
    `pass  N name  (D s)` / `FAIL  N name: reason` / `GATE  N name: question`.
  - fail: return 1. needs_person: write `question.md` (title, who, question, context as a JSON
    block, then one line: "Answer by writing <run_dir>/answer.json, for example
    {"approved": true, "by": "Oleg", "note": ""}") and return 2. pass: merge artifacts, go on.
- Returns 0 when all six passed. Print a one-line summary at the end with the run dir.
`status(run_dir, out)` prints one line per record: index, name, status, duration, reason.

## __main__.py
`python -m factory run <ticket.json> [--runs-root DIR]` and `python -m factory status <run_dir>`;
exit code is the driver's return value. argparse, no third-party.

## tests/test_driver.py
Use fake step callables injected through `steps=`; a tmp_path runs_root; a tiny ticket and app
recipe JSON written into tmp_path (the ticket's "app" path may be absolute: support that too).
Cover: all pass → 0 and six records; third step needs_person → 2, question.md exists with the
question text, later steps not called; re-run with answer.json → the first two steps are not
called again, the third receives artifacts["answer"], run completes → 0; a failing step → 1, a
second run re-executes it with round 2 and keeps the old record as round1; a step that raises →
fail record with the exception message; `status()` output lists the steps; `python -m factory`
through subprocess for the usage path. Use the testing rules of the py-testing skills where
they apply (plain pytest functions, tmp_path, no sleeps).
