"""Runs a ticket through the six steps in order, keeping one record per step so a run can resume."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from factory import gates
from factory.envelope import StepInput, StepOutput, StepRecord, now_iso

STEP_NAMES = ["frame", "plan", "implement", "verify", "review", "ship"]
# The ticket fields a person's clarification (Frame's `clarify` answer) may replace.
CLARIFIABLE = ("description", "contract", "acceptance_criteria")
CLARIFIED_FILE = "ticket.clarified.json"

StepFn = Callable[[dict], "dict | StepOutput"]

# Called after a step stops for a person; a module attribute so tests replace it.
NOTIFY = gates.notify


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
    example: dict = {"approved": True, "by": "Oleg", "note": ""}
    if gate is None:
        text = f"# Step {index} {name} needs a person\n\n{output.reason}\n"
    else:
        text = (
            f"# Step {index} {name} needs a person\n\n"
            f"Kind: {gate.kind}\n\n"
            f"Who: {gate.who}\n\n"
            f"Question: {gate.question}\n\n"
        )
        if gate.answers:
            text += "Accepted answers:\n\n"
            for a in gate.answers:
                carries = f' (with "{a["carries"]}")' if a.get("carries") else ""
                text += f"- `{a['decision']}`{carries}: {a.get('means', '')}\n"
            text += "\n"
            first = gate.answers[0]
            example = {"decision": first["decision"]}
            if first.get("carries"):
                example[first["carries"]] = ""
            example.update({"by": gate.who or "Oleg", "note": ""})
        text += f"Context:\n\n```json\n{json.dumps(gate.context, indent=2)}\n```\n\n"
    text += (
        f"Answer by writing {run_dir}/answer.json (`by` is required), for example:\n\n"
        f"```json\n{json.dumps(example)}\n```\n"
    )
    path.write_text(text)
    return path


def _archive_answer(answer_path: Path, target: Path) -> None:
    """Keep a consumed answer as history, with the time it was consumed; the original keys stay."""
    try:
        data = json.loads(answer_path.read_text())
    except (OSError, json.JSONDecodeError):
        answer_path.rename(target)
        return
    if isinstance(data, dict):
        data.setdefault("answered_at", now_iso())
    _write_json(target, data)
    answer_path.unlink()


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


def with_clarified(ticket: dict, run_dir) -> dict:
    """The ticket with `<run_dir>/ticket.clarified.json` merged in, when that file exists.

    Its keys replace the ticket's; only description, contract and acceptance_criteria may be there,
    so the ticket file's other fields (`caps`, `gates`, ...) always win. Raises ValueError otherwise.
    """
    path = Path(run_dir) / CLARIFIED_FILE
    if not path.exists():
        return ticket
    clarified = json.loads(path.read_text())
    if not isinstance(clarified, dict):
        raise ValueError(f"{path} must hold a JSON object")
    foreign = sorted(set(clarified) - set(CLARIFIABLE))
    if foreign:
        raise ValueError(f"{path} may only hold {', '.join(CLARIFIABLE)}; found {', '.join(foreign)}")
    return {**ticket, **clarified}


def _merge_clarified(ticket: dict, run_dir: Path) -> dict:
    """with_clarified, and the merged ticket written to `<run_dir>/ticket.json` as the record."""
    merged = with_clarified(ticket, run_dir)
    if (run_dir / CLARIFIED_FILE).exists():
        _write_json(run_dir / "ticket.json", merged)
    return merged


def prepare(ticket_path, runs_root=".artifacts/runs") -> tuple[dict, dict, Path]:
    """Read a ticket and make its run folder. Returns (ticket, repo, run_dir).

    A person's clarification of the ticket (`ticket.clarified.json` in the run folder) is merged in.
    """
    ticket = json.loads(Path(ticket_path).read_text())
    repo = _load_repo(ticket)
    root = Path(runs_root)
    if not root.is_absolute():
        root = repo_root() / root
    run_dir = (root / ticket["id"]).resolve()
    (run_dir / "steps").mkdir(parents=True, exist_ok=True)
    if not (run_dir / "ticket.json").exists():
        _write_json(run_dir / "ticket.json", ticket)
    ticket = _merge_clarified(ticket, run_dir)
    return ticket, repo, run_dir


def run_step(
    index: int,
    name: str,
    fn: StepFn,
    ticket: dict,
    repo: dict,
    run_dir: Path,
    artifacts: dict,
    out: TextIO = sys.stdout,
) -> StepOutput:
    """Run one step, resumable from its record in the run folder; both engines call this.

    A passed record is returned without running the step. A record waiting for a person is returned
    as it is until `answer.json` exists; then the step runs with the answer, which is consumed once.
    A failed record becomes an earlier round and the step runs again. Every run writes the record.
    """
    steps_dir = run_dir / "steps"
    record_path = steps_dir / f"{index:02d}-{name}.json"
    answer_path = run_dir / "answer.json"
    # A clarification Frame wrote earlier in this same run reaches every later step (both engines).
    ticket = _merge_clarified(ticket, run_dir)
    old: StepRecord | None = None
    if record_path.exists():
        old = StepRecord.from_dict(json.loads(record_path.read_text()))

    if old and old.status == "pass":
        print(f"skip  {index} {name}", file=out)
        return old.output

    if old and old.status == "needs_person" and not answer_path.exists():
        gate = old.output.gate
        print(f"GATE  {index} {name}: {gate.question if gate else old.output.reason}", file=out)
        print(f"question: {run_dir / 'question.md'}", file=out)
        return old.output

    if old and old.status == "needs_person":  # an answer is there: check it before consuming it
        try:
            gates.read_answer(answer_path, old.output.gate.answers if old.output.gate else None)
        except gates.AnswerError as err:
            print(f"answer: {err}", file=out)
            print(f"question: {run_dir / 'question.md'}", file=out)
            return old.output

    # A failed record becomes an earlier round now. A question that is being answered becomes one
    # after the step ran (the step reads the asking record while it runs), so a step that stops
    # twice keeps both questions and both answers: answer<round> never overwrites an earlier one.
    earlier = len(list(steps_dir.glob(f"{index:02d}-{name}.round*.json")))
    archive_asked: Path | None = None
    if old and old.status == "fail":
        earlier += 1
        record_path.rename(steps_dir / f"{index:02d}-{name}.round{earlier}.json")
    elif old and old.status == "needs_person":
        earlier += 1
        archive_asked = steps_dir / f"{index:02d}-{name}.round{earlier}.json"
    round_no = earlier + 1

    step_artifacts = dict(artifacts)
    if old and old.status == "needs_person":
        step_artifacts["answer"] = str(answer_path)

    step_input = StepInput(
        ticket=ticket, repo=repo, artifacts=step_artifacts, round=round_no, run_dir=str(run_dir)
    )
    started = now_iso()
    t0 = time.monotonic()
    output = _call(fn, step_input)
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
    data = record.to_dict()
    if output.status == "pass":  # what each artifact file held when the step passed, for `redo`
        data["artifact_sha256"] = {
            k: _sha256(v) for k, v in output.artifacts.items() if isinstance(v, str) and Path(v).is_file()
        }
    if archive_asked is not None and record_path.exists():
        record_path.rename(archive_asked)
    _write_json(record_path, data)
    if "answer" in step_artifacts and answer_path.exists():
        _archive_answer(answer_path, steps_dir / f"{index:02d}-{name}.answer{round_no}.json")

    if output.status == "fail":
        print(f"FAIL  {index} {name}: {output.reason}", file=out)
    elif output.status == "needs_person":
        question = output.gate.question if output.gate else output.reason
        print(f"GATE  {index} {name}: {question}", file=out)
        _write_question(run_dir, name, index, output)
        print(f"question: {run_dir / 'question.md'}", file=out)
        try:
            for problem in NOTIFY(run_dir, name, output.gate, ticket, repo.get("app") or {}):
                print(f"notify: {problem}", file=out)
        except Exception as err:  # telling is best effort; it never fails the run
            print(f"notify: {type(err).__name__}: {err}", file=out)
    else:
        print(f"pass  {index} {name}  ({duration} s)", file=out)
    return output


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
    ticket, repo, run_dir = prepare(ticket_path, runs_root)
    steps = steps if steps is not None else load_steps()

    artifacts: dict[str, str] = {}
    for index, name in enumerate(STEP_NAMES, start=1):
        output = run_step(index, name, steps[name], ticket, repo, run_dir, artifacts, out)
        if output.status == "fail":
            print(f"run: {run_dir}", file=out)
            return 1
        if output.status == "needs_person":
            return 2
        artifacts.update(output.artifacts)
        if name == until:
            print(f"stopped after {name} as asked: {run_dir}", file=out)
            return 0

    print(f"all {len(STEP_NAMES)} steps passed: {run_dir}", file=out)
    return 0


def _answered(path: Path) -> str:
    """` answered by <who> (<decision>)` when this round of the step ran on a person's answer."""
    try:
        answer = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(answer, dict):
        return ""
    return f" answered by {answer.get('by') or '-'} ({gates.decision_of(answer) or '-'})"


def status(run_dir, out: TextIO = sys.stdout) -> int:
    """Print one line per step record in a run folder."""
    steps_dir = Path(run_dir) / "steps"
    for path in sorted(steps_dir.glob("*.json")):
        if ".answer" in path.name or ".redo" in path.name:
            continue
        rec = StepRecord.from_dict(json.loads(path.read_text()))
        label = " (earlier round)" if ".round" in path.name else ""
        answered = _answered(steps_dir / f"{rec.index:02d}-{rec.step}.answer{rec.input.round}.json")
        line = f"{rec.index} {rec.step} {rec.status}{label}{answered} {rec.duration_s} s {rec.output.reason}"
        print(line.rstrip(), file=out)
    return 0


def _sha256(path: str):
    """The file's sha256; "directory" for a folder; "unknown" when it does not exist."""
    p = Path(path)
    if p.is_file():
        return hashlib.sha256(p.read_bytes()).hexdigest()
    return "directory" if p.is_dir() else "unknown"


def _next_free(steps_dir: Path, stem: str, kind: str) -> int:
    k = 1
    while (steps_dir / f"{stem}.{kind}{k}.json").exists():
        k += 1
    return k


def redo(run_dir, step: str, by: str, note: str = "", rerun: bool = False, out: TextIO = sys.stdout) -> int:
    """After a person edited a passed step's artifact by hand: the next `run` resumes after that step.

    Every later step's record becomes an earlier round; with `rerun` the step's own too, so it runs
    again. `steps/NN-<step>.redoK.json` keeps who, when, the note and the artifact files' sha256: before
    (from the step's record) and after (the files as they are now).
    Returns 1, saying what to do instead, for a step that has not passed or a run waiting at a gate.
    """
    if step not in STEP_NAMES:
        print(f"redo: unknown step {step!r}; one of {STEP_NAMES}", file=out)
        return 1
    run_dir = Path(run_dir)
    steps_dir = run_dir / "steps"
    index = STEP_NAMES.index(step) + 1
    stem = f"{index:02d}-{step}"
    for path in gates._latest_records(steps_dir):
        try:
            waiting = json.loads(path.read_text()).get("status") == "needs_person"
        except (OSError, json.JSONDecodeError):
            continue
        if waiting:
            print(
                f"redo: the run waits at a gate ({path.name}); answer it first: write "
                f"{run_dir / 'answer.json'} as {run_dir / 'question.md'} says, then run the ticket again",
                file=out,
            )
            return 1
    record_path = steps_dir / f"{stem}.json"
    if not record_path.exists():
        print(f"redo: {step} has no record in {steps_dir}; run the ticket instead", file=out)
        return 1
    raw = json.loads(record_path.read_text())
    record = StepRecord.from_dict(raw)
    if record.status != "pass":
        print(
            f"redo: {step} has not passed (status {record.status}); run the ticket again instead, "
            "which runs a failed step again",
            file=out,
        )
        return 1

    files = {k: v for k, v in record.output.artifacts.items() if isinstance(v, str)}
    # "before" is what the step's record saw when it passed; a record without hashes (an older run,
    # or a directory or missing artifact) says "unknown".
    recorded = raw.get("artifact_sha256") or {}
    before = {k: recorded.get(k, "unknown") for k in files}
    archived = []
    later = [(i, n) for i, n in enumerate(STEP_NAMES, start=1) if i > index]
    for i, name in ([(index, step)] if rerun else []) + later:
        latest = steps_dir / f"{i:02d}-{name}.json"
        if latest.exists():
            target = steps_dir / f"{i:02d}-{name}.round{_next_free(steps_dir, latest.stem, 'round')}.json"
            latest.rename(target)
            archived.append(target.name)
    k = _next_free(steps_dir, stem, "redo")
    redo_record = {
        "step": step,
        "by": by,
        "at": now_iso(),
        "note": note,
        "rerun": rerun,
        "artifacts": files,
        "sha256_before": before,
        "sha256_after": {k2: _sha256(v) for k2, v in files.items()},
        "archived": archived,
    }
    _write_json(steps_dir / f"{stem}.redo{k}.json", redo_record)
    for name in archived:
        print(f"archived {name}", file=out)
    if not archived:
        print("archived nothing: no later step had run", file=out)
    print(f"redo record: {steps_dir / f'{stem}.redo{k}.json'}", file=out)
    first = step if rerun else (STEP_NAMES[index] if index < len(STEP_NAMES) else None)
    print(f"the next run starts at {first}" if first else "every step is done; nothing runs again", file=out)
    return 0
