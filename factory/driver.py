"""Runs a ticket through the six steps in order, keeping one record per step so a run can resume."""

from __future__ import annotations

import importlib
import json
import sys
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from factory.envelope import StepInput, StepOutput, StepRecord, now_iso

STEP_NAMES = ["frame", "plan", "implement", "verify", "review", "ship"]

StepFn = Callable[[dict], "dict | StepOutput"]


def repo_root() -> Path:
    """The directory holding pyproject.toml, found upward from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("could not find pyproject.toml above " + str(Path(__file__)))


def load_steps() -> dict[str, StepFn]:
    """Import factory.steps.<name> for each step and return {name: module.run}."""
    steps: dict[str, StepFn] = {}
    for name in STEP_NAMES:
        module_name = f"factory.steps.{name}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as err:
            if err.name != module_name:
                raise
            raise RuntimeError(f"step '{name}' is not implemented: no module {module_name}") from err
        steps[name] = module.run
    return steps


def _expand(value):
    """Expand a leading ~ in every string inside a recipe."""
    if isinstance(value, str):
        return str(Path(value).expanduser()) if value.startswith("~") else value
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


def _load_repo(ticket: dict) -> dict:
    app_path = repo_root() / ticket["app"]  # an absolute ticket["app"] wins over the root
    app = _expand(json.loads(app_path.read_text()))
    # One worktree pair per ticket, so a second ticket never moves or cleans a parked run's trees.
    worktrees = Path(app["worktrees"]) / ticket["id"]
    return {
        "app": app,
        "base": ticket["base"],
        "head": ticket["head"],
        "base_tree": str(worktrees / "base"),
        "head_tree": str(worktrees / "head"),
    }


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, default=str) + "\n")


def _write_question(run_dir: Path, name: str, index: int, output: StepOutput) -> Path:
    gate = output.gate
    path = run_dir / "question.md"
    if gate is None:
        text = f"# Step {index} {name} needs a person\n\n{output.reason}\n"
    else:
        text = (
            f"# Step {index} {name} needs a person\n\n"
            f"Who: {gate.who}\n\n"
            f"Question: {gate.question}\n\n"
            f"Context:\n\n```json\n{json.dumps(gate.context, indent=2)}\n```\n\n"
        )
    text += (
        f"Answer by writing {run_dir}/answer.json, for example "
        '{"approved": true, "by": "Oleg", "note": ""}\n'
    )
    path.write_text(text)
    return path


def _call(fn: StepFn, step_input: StepInput) -> StepOutput:
    """Call a step; any exception becomes a fail output."""
    try:
        result = fn(step_input.to_dict())
        return result if isinstance(result, StepOutput) else StepOutput.from_dict(result)
    except Exception as err:
        tb = traceback.format_exc()
        return StepOutput(
            status="fail",
            reason=f"{type(err).__name__}: {err}",
            metrics={"traceback": tb[-500:]},
        )


def run(
    ticket_path,
    runs_root=".artifacts/runs",
    steps: dict[str, StepFn] | None = None,
    out: TextIO = sys.stdout,
    until: str | None = None,
) -> int:
    """Run or resume a ticket. Returns 0 when all steps pass, 1 on a failure, 2 at a question.

    `until` names a step after which the run stops with 0, so a run can be advanced step by step.
    """
    if until is not None and until not in STEP_NAMES:
        raise ValueError(f"unknown step {until!r}; one of {STEP_NAMES}")
    ticket = json.loads(Path(ticket_path).read_text())
    repo = _load_repo(ticket)
    steps = steps if steps is not None else load_steps()

    root = Path(runs_root)
    if not root.is_absolute():
        root = repo_root() / root
    run_dir = (root / ticket["id"]).resolve()
    steps_dir = run_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    if not (run_dir / "ticket.json").exists():
        _write_json(run_dir / "ticket.json", ticket)

    artifacts: dict[str, str] = {}
    for index, name in enumerate(STEP_NAMES, start=1):
        record_path = steps_dir / f"{index:02d}-{name}.json"
        answer_path = run_dir / "answer.json"
        old: StepRecord | None = None
        if record_path.exists():
            old = StepRecord.from_dict(json.loads(record_path.read_text()))

        if old and old.status == "pass":
            print(f"skip  {index} {name}", file=out)
            artifacts.update(old.output.artifacts)
            continue

        if old and old.status == "needs_person" and not answer_path.exists():
            gate = old.output.gate
            print(f"GATE  {index} {name}: {gate.question if gate else old.output.reason}", file=out)
            print(f"question: {run_dir / 'question.md'}", file=out)
            return 2

        earlier = len(list(steps_dir.glob(f"{index:02d}-{name}.round*.json")))
        if old and old.status == "fail":
            earlier += 1
            record_path.rename(steps_dir / f"{index:02d}-{name}.round{earlier}.json")
        round_no = earlier + 1

        step_artifacts = dict(artifacts)
        if old and old.status == "needs_person":
            step_artifacts["answer"] = str(answer_path)

        step_input = StepInput(
            ticket=ticket, repo=repo, artifacts=step_artifacts, round=round_no, run_dir=str(run_dir)
        )
        started = now_iso()
        t0 = time.monotonic()
        output = _call(steps[name], step_input)
        duration = round(time.monotonic() - t0, 3)
        record = StepRecord(
            step=name,
            index=index,
            status=output.status,
            input=step_input,
            output=output,
            started=started,
            finished=now_iso(),
            duration_s=duration,
        )
        _write_json(record_path, record.to_dict())
        if "answer" in step_artifacts and answer_path.exists():
            answer_path.rename(steps_dir / f"{index:02d}-{name}.answer{round_no}.json")

        if output.status == "fail":
            print(f"FAIL  {index} {name}: {output.reason}", file=out)
            print(f"run: {run_dir}", file=out)
            return 1
        if output.status == "needs_person":
            question = output.gate.question if output.gate else output.reason
            print(f"GATE  {index} {name}: {question}", file=out)
            _write_question(run_dir, name, index, output)
            print(f"question: {run_dir / 'question.md'}", file=out)
            return 2
        print(f"pass  {index} {name}  ({duration} s)", file=out)
        artifacts.update(output.artifacts)
        if name == until:
            print(f"stopped after {name} as asked: {run_dir}", file=out)
            return 0

    print(f"all {len(STEP_NAMES)} steps passed: {run_dir}", file=out)
    return 0


def status(run_dir, out: TextIO = sys.stdout) -> int:
    """Print one line per step record in a run folder."""
    steps_dir = Path(run_dir) / "steps"
    for path in sorted(steps_dir.glob("*.json")):
        if ".answer" in path.name:
            continue
        rec = StepRecord.from_dict(json.loads(path.read_text()))
        label = " (earlier round)" if ".round" in path.name else ""
        print(
            f"{rec.index} {rec.step} {rec.status}{label} {rec.duration_s} s {rec.output.reason}".rstrip(),
            file=out,
        )
    return 0
